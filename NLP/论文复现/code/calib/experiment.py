"""实验主流程：抽样、运行、保存（对齐作者 run_classification.py 与其 README 官方复现命令）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：样例抽样（np.random.seed + choice）、测试集固定子集（freeze seed 0），
     逐样本结果落盘 results/raw/*.json 与 results/samples/*.csv，汇总行追加 results/summary.csv；
     支持 --content_free_ablation（论文 Table 3 消融）。

2026-11-04
变更说明：
  1. 头部加 sys.path 处理：支持 python calib/experiment.py 直接运行（原直跑时 calib 包导入不可达）。
  2. 跳过已有结果前核对配置一致性（fp16/bs/num_log_probs/subsample/content_free_inputs），
     不一致即报错退出，防止不同配置被 expr_name 去重键静默复用（R01 P-9 整改）。

2026-11-15
变更说明：
  1. aggregate() 跳过无 config 键的文件（trial/probe 类资源试跑产物），
     否则 --aggregate_only 遍历 results/raw/ 时对 trial_sst2_gpt2.json 直接 KeyError。
"""
import argparse
import csv
import json
import sys
import time
from copy import deepcopy
from pathlib import Path

import numpy as np

# 支持 python calib/experiment.py 直接运行：把 code/ 加入模块搜索路径，
# 否则 from calib.xxx 只在 python -m calib.experiment 方式下可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calib.calibration import eval_accuracy, get_p_content_free, get_label_probs
from calib.data_utils import load_dataset
from calib.lm import GPT2Runner

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"

_RUNNER_CACHE = {}  # (模型名, fp16) -> GPT2Runner，避免同一模型反复加载权重


def get_runner(model_name, fp16=False):
    """带缓存的模型获取：同一模型在一次网格运行中只加载一次权重。"""
    key = (model_name, fp16)
    if key not in _RUNNER_CACHE:
        _RUNNER_CACHE[key] = GPT2Runner(model_name, fp16=fp16)
    return _RUNNER_CACHE[key]


def random_sampling(sentences, labels, num):
    """随机抽 num 个不重复下标（作者 random_sampling：np.random.choice replace=False）。"""
    assert len(sentences) == len(labels)
    idxs = np.random.choice(len(labels), size=num, replace=False)
    return [sentences[i] for i in idxs], [labels[i] for i in idxs], idxs.tolist()


def run_one(model_name, dataset, num_shots, seed, subsample_test_set=300,
            num_log_probs=100, bs=None, fp16=False, content_free_inputs=("N/A", "", "[MASK]"),
            extra_modes=()):
    """运行单个配置（模型 x 数据集 x shot x 种子），返回结果字典并落盘。"""
    expr_name = f"{dataset}_{model_name}_{num_shots}shot_sub{subsample_test_set}_seed{seed}"
    out_path = RESULTS_DIR / "raw" / f"{expr_name}.json"
    if out_path.exists():
        old = json.loads(out_path.read_text(encoding="utf-8"))
        # expr_name 去重键不含精度/批大小/内容无关输入/prompt 参数等字段——跳过前必须核对
        # 已存配置与本次调用一致，防止不同配置的历史结果被静默复用（R01 P-9 整改，与
        # cf_ablation 失效 bug 同根因；prompt 参数为 R01b B2 补充）
        eff_bs = bs or 4
        _, _, _, _, cur_params = load_dataset(dataset)
        checks = {"fp16": (old["config"]["fp16"], fp16),
                  "num_log_probs": (old["config"]["num_log_probs"], num_log_probs),
                  "bs": (old["config"]["bs"], eff_bs),
                  "subsample_test_set": (old["config"]["subsample_test_set"], subsample_test_set),
                  "content_free_inputs": (old["config"]["content_free_inputs"],
                                          list(content_free_inputs)),
                  "label_dict": (old["config"]["label_dict"],
                                 {str(k): v for k, v in cur_params["label_dict"].items()}),
                  "prompt_prefix": (old["config"]["prompt_prefix"], cur_params["prompt_prefix"]),
                  "q_prefix": (old["config"]["q_prefix"], cur_params["q_prefix"]),
                  "a_prefix": (old["config"]["a_prefix"], cur_params["a_prefix"])}
        bad = [f"{k}: 已存={o} 本次={n}" for k, (o, n) in checks.items() if o != n]
        if bad:
            raise SystemExit(f"[expr_name 冲突] {expr_name} 已存在但配置不同，拒绝静默复用：\n  "
                             + "\n  ".join(bad))
        print(f"跳过（已存在，配置一致）: {expr_name}")
        return old

    train_pool_s, train_pool_l, test_pool_s, test_pool_l, params = load_dataset(dataset)

    # 1. 测试集固定子集：与作者一致，freeze_test_set=True 时永远用 seed 0 抽样
    np.random.seed(0 if subsample_test_set else seed)
    if subsample_test_set and subsample_test_set < len(test_pool_l):
        test_s, test_l, test_ids = random_sampling(test_pool_s, test_pool_l, subsample_test_set)
    else:
        test_ids = list(range(len(test_pool_l)))
        test_s, test_l = test_pool_s, test_pool_l

    # 2. 训练样例抽样：用本配置的 seed
    np.random.seed(seed)
    if num_shots > 0:
        train_s, train_l, train_ids = random_sampling(train_pool_s, train_pool_l, num_shots)
    else:
        train_s, train_l, train_ids = [], [], []

    # 3. 推理：全部测试句的首 token top-k
    runner = get_runner(model_name, fp16=fp16)
    runner.set_batch_size(bs or 4)
    params["model"] = model_name
    print(f"[{expr_name}] 测试 {len(test_s)} 条 | 训练样例 {num_shots} 条 | 批大小 {runner.bs}")
    t0 = time.time()
    topk_list = runner.first_token_topk(
        [construct_prompt_checked(params, train_s, train_l, s) for s in test_s],
        num_log_probs=num_log_probs)
    all_label_probs = get_label_probs(runner, params, topk_list, train_s, train_l, test_s)

    # 4. p_cf 与两套准确率（基线 / 校准）
    p_cf = get_p_content_free(runner, params, train_s, train_l, content_free_inputs)
    acc_original = eval_accuracy(all_label_probs, test_l)
    acc_calibrated = eval_accuracy(all_label_probs, test_l, mode="diagonal_W", p_cf=p_cf)
    accs = {"original": acc_original, "diagonal_W": acc_calibrated}
    for mode in extra_modes:  # 消融用：identity_W 备选解
        accs[mode] = eval_accuracy(all_label_probs, test_l, mode=mode, p_cf=p_cf)
    elapsed = time.time() - t0
    print(f"[{expr_name}] 基线 {acc_original:.4f} | 校准 {acc_calibrated:.4f} | p_cf {np.round(p_cf, 4).tolist()} | {elapsed:.0f}s")

    # 5. 逐样本记录（规范要求：样本编号、gold、各类概率、两种预测）
    W = np.linalg.inv(np.identity(len(params["label_dict"])) * p_cf)
    rows = []
    for i, (probs, gold) in enumerate(zip(all_label_probs, test_l)):
        p_norm = probs / np.sum(probs)
        pred_orig = int(np.argmax(p_norm))
        pred_cal = int(np.argmax(np.matmul(W, np.expand_dims(p_norm, axis=-1))))
        rows.append({"sample_id": test_ids[i], "gold": gold,
                     "pred_original": pred_orig, "pred_calibrated": pred_cal,
                     "probs": [round(float(x), 8) for x in probs]})
    (RESULTS_DIR / "samples").mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "samples" / f"{expr_name}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "gold", "pred_original",
                                               "pred_calibrated", "probs"])
        writer.writeheader()
        writer.writerows(rows)

    # 6. 原始结果落盘（含完整配置，供复核与汇总）
    result = {
        "expr_name": expr_name,
        "config": {"model": model_name, "dataset": dataset, "num_shots": num_shots,
                   "seed": seed, "subsample_test_set": subsample_test_set,
                   "num_log_probs": num_log_probs, "bs": runner.bs, "fp16": fp16,
                   "content_free_inputs": list(content_free_inputs),
                   "label_dict": {str(k): v for k, v in params["label_dict"].items()},
                   "prompt_prefix": params["prompt_prefix"],
                   "q_prefix": params["q_prefix"], "a_prefix": params["a_prefix"]},
        "train_ids": train_ids,
        "train_sentences": train_s,
        "train_labels": train_l,
        "test_ids": test_ids,
        "test_labels": test_l,
        "p_cf": [float(x) for x in p_cf],
        "accuracies": accs,
        "elapsed_seconds": round(elapsed, 1),
        "num_flip": sum(1 for r in rows if r["pred_original"] != r["pred_calibrated"]),
    }
    (RESULTS_DIR / "raw").mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    append_summary(result)
    return result


def construct_prompt_checked(params, train_s, train_l, test_sentence):
    """construct_prompt 的包装：训练样例的标签词取该类第一个名字（与作者一致）。"""
    from calib.data_utils import construct_prompt
    return construct_prompt(params, train_s, train_l, test_sentence)


def append_summary(result):
    """把一次运行的关键数字追加到 results/summary.csv（汇总表）。"""
    c, a = result["config"], result["accuracies"]
    summary_path = RESULTS_DIR / "summary.csv"
    is_new = not summary_path.exists()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["expr_name", "model", "dataset", "shots", "seed",
                             "acc_original", "acc_calibrated", "num_flip", "elapsed_seconds"])
        writer.writerow([result["expr_name"], c["model"], c["dataset"], c["num_shots"], c["seed"],
                         f"{a['original']:.4f}", f"{a['diagonal_W']:.4f}",
                         result["num_flip"], result["elapsed_seconds"]])


def aggregate(model=None, dataset=None):
    """按 (模型, 数据集, shot) 聚合各 seed：输出均值与标准差（论文 Table 风格）。"""
    import statistics
    groups = {}
    for path in sorted((RESULTS_DIR / "raw").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if "config" not in r:
            # trial/probe 类资源试跑文件无 config 键，不进正式聚合（2026-11-15 第二期开启前修补）
            continue
        c = r["config"]
        if model and c["model"] != model:
            continue
        if dataset and c["dataset"] != dataset:
            continue
        key = (c["model"], c["dataset"], c["num_shots"])
        groups.setdefault(key, []).append(r["accuracies"])
    print(f"{'模型':<12}{'数据集':<8}{'shot':<6}{'seeds':<7}基线 均值±std | 校准 均值±std")
    for (m, d, s), accs in sorted(groups.items()):
        orig = [a["original"] for a in accs]
        cal = [a["diagonal_W"] for a in accs]
        print(f"{m:<12}{d:<8}{s:<6}{len(accs):<7}{statistics.mean(orig):.4f}±{statistics.stdev(orig) if len(orig) > 1 else 0:.4f} "
              f"| {statistics.mean(cal):.4f}±{statistics.stdev(cal) if len(cal) > 1 else 0:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate Before Use 复现实验")
    parser.add_argument("--model", default="gpt2-xl", help="模型名（models/ 下目录名，逗号分隔）")
    parser.add_argument("--dataset", default="sst2", help="数据集 sst2/agnews/trec（逗号分隔）")
    parser.add_argument("--shots", default="0,1,4,8", help="shot 列表")
    parser.add_argument("--seeds", type=int, default=5, help="训练样例集合的种子数（0..n-1）")
    parser.add_argument("--subsample", type=int, default=300, help="测试集固定子集大小；0 为全集")
    parser.add_argument("--bs", type=int, default=None, help="批大小（默认按模型给 4）")
    parser.add_argument("--fp16", action="store_true", help="半精度推理（默认 fp32）")
    parser.add_argument("--num_log_probs", type=int, default=100, help="首 token top-k")
    parser.add_argument("--cf_ablation", action="store_true",
                        help="内容无关输入消融：另跑 N/A 与 [MASK] 单输入及 identity_W（Table 3）")
    parser.add_argument("--aggregate_only", action="store_true", help="只汇总已有结果，不运行")
    parser.add_argument("--aggregate_model", default=None)
    parser.add_argument("--aggregate_dataset", default=None)
    args = parser.parse_args()

    if args.aggregate_only:
        aggregate(args.aggregate_model, args.aggregate_dataset)
        return

    for model_name in args.model.split(","):
        for dataset in args.dataset.split(","):
            for shots in [int(s) for s in args.shots.split(",")]:
                for seed in range(args.seeds):
                    run_one(model_name.strip(), dataset.strip(), shots, seed,
                            subsample_test_set=args.subsample,
                            num_log_probs=args.num_log_probs, bs=args.bs, fp16=args.fp16)
                    if args.cf_ablation and shots > 0:
                        # Table 3 式消融：单内容无关输入（不再重跑推理，见 calibration 注释；
                        # 这里按新输入重算 p_cf 与准确率，标签概率复用缓存文件——简化为独立运行）
                        run_one(model_name.strip(), dataset.strip(), shots, seed,
                                subsample_test_set=args.subsample,
                                num_log_probs=args.num_log_probs, bs=args.bs, fp16=args.fp16,
                                content_free_inputs=("N/A",), extra_modes=("identity_W",))
                        run_one(model_name.strip(), dataset.strip(), shots, seed,
                                subsample_test_set=args.subsample,
                                num_log_probs=args.num_log_probs, bs=args.bs, fp16=args.fp16,
                                content_free_inputs=("[MASK]",), extra_modes=("identity_W",))


if __name__ == "__main__":
    main()
