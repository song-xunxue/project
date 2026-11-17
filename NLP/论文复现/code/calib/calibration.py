"""上下文校准（contextual calibration）与评测（对齐作者 run_classification.py）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：get_p_content_free / eval_accuracy 与作者实现逐行对齐；
     支持内容无关输入消融（单输入 vs 三输入平均，对应论文 Table 3）。

2026-11-04
变更说明：
  1. get_label_probs 缺失表改为作者 all_found 模式（按"类"粒度，一个类最多记一次；
     原按"标签词"粒度对双词类重复记录，回声数值等价但多算冗余前向，R01 维度2 整改）；
     缺失计数打印改为作者格式（带分母 X/N）。
"""
import numpy as np

from calib.data_utils import construct_prompt


def get_label_probs(runner, params, topk_list, train_sentences, train_labels, test_sentences):
    """从首 token top-k 分布提取各标签概率；top-k 未覆盖的标签用回声模式补全
    （作者 get_label_probs 的逻辑：主通道 + 困惑度回填，--approx 即跳过回填置零，本工程总是回填）。
    返回形状 (测试数, 类数) 的未归一化概率。"""
    num_classes = len(params["label_dict"])
    all_label_probs = []
    missing = []  # (样例下标, 类下标) 列表——按"类"粒度记录，与作者 all_missing_positions 一致
    for i, top_logprobs in enumerate(topk_list):
        label_probs = [0.0] * num_classes
        for j, label_names in params["label_dict"].items():
            # 作者 all_found 模式：类内任一标签词缺失即整类入缺失表（一个类最多记一次）
            all_found = True
            for label in label_names:  # 一个类可对应多个标签词（如 AGNews 类3 = Technology/Science）
                label = " " + label  # prompt 末尾无空格，标签词以空格开头计概率
                if label in top_logprobs:
                    label_probs[j] += np.exp(top_logprobs[label])
                else:
                    all_found = False
            if not all_found:
                missing.append((i, j))
        all_label_probs.append(label_probs)
    all_label_probs = np.array(all_label_probs)

    if missing:
        # 打印带分母（作者格式 "Missing probs: X/N"），N = 测试数 × 类数
        print(f"缺失标签概率 {len(missing)}/{len(topk_list) * num_classes} 处，回声模式补全中")
        prompts, group_sizes = [], []
        for i, j in missing:
            for label in params["label_dict"][j]:
                prompts.append(construct_prompt(params, train_sentences, train_labels,
                                                test_sentences[i]) + " " + label)
            group_sizes.append(len(params["label_dict"][j]))
        lps = runner.echo_last_token_logprob(prompts)
        idx = 0
        for (i, j), size in zip(missing, group_sizes):
            # 类概率 = 各标签词概率之和（与作者一致）
            all_label_probs[i, j] = sum(np.exp(lp) for lp in lps[idx:idx + size])
            idx += size
    assert (all_label_probs > 0).all(), "仍有标签概率未补全"
    return all_label_probs


def get_p_content_free(runner, params, train_sentences, train_labels, content_free_inputs=("N/A",)):
    """查询模型对内容无关输入的各类概率 p_cf（作者 get_p_content_free）。
    多个内容无关输入时取平均再归一化（论文实现细节：N/A、空串、[MASK] 三者平均）。"""
    all_p_y = []
    for cf_input in content_free_inputs:
        prompt = construct_prompt(params, train_sentences, train_labels, cf_input)
        # 标签概率用回声模式精确计算（prompt + " " + label 的末 token logprob）
        label_prompts = [prompt + " " + label for names in params["label_dict"].values()
                         for label in names]
        lps = runner.echo_last_token_logprob(label_prompts)
        p_y, idx = [0.0] * len(params["label_dict"]), 0
        for i, names in params["label_dict"].items():
            p_y[i] = sum(np.exp(lp) for lp in lps[idx:idx + len(names)])
            idx += len(names)
        all_p_y.append(p_y)
    p_y = np.mean(np.array(all_p_y), axis=0)
    return p_y / np.sum(p_y)  # 归一化到和为 1


def eval_accuracy(all_label_probs, test_labels, mode=None, p_cf=None):
    """评测准确率（作者 eval_accuracy）。mode=None 为基线（W=I, b=0）；
    mode='diagonal_W' 为上下文校准（W=diag(1/p_cf), b=0）；
    mode='identity_W' 为备选解（W=I, b=-p_cf，论文脚注7：生成任务上更优）。"""
    num_classes = all_label_probs.shape[1]
    if p_cf is None:
        W = np.identity(num_classes)
        b = np.zeros([num_classes, 1])
    elif mode == "diagonal_W":
        W = np.linalg.inv(np.identity(num_classes) * p_cf)
        b = np.zeros([num_classes, 1])
    elif mode == "identity_W":
        W = np.identity(num_classes)
        b = -1 * np.expand_dims(p_cf, axis=-1)
    else:
        raise ValueError("未知校准模式: " + str(mode))

    correct = []
    for label_probs, true_label in zip(all_label_probs, test_labels):
        label_probs = label_probs / np.sum(label_probs)  # 归一化到 1（作者注释：prob NOT normalized）
        calibrated = np.matmul(W, np.expand_dims(label_probs, axis=-1)) + b
        correct.append(int(np.argmax(calibrated) == true_label))
    return float(np.mean(correct))
