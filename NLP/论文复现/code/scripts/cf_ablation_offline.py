"""离线内容无关输入消融（Table 3）：从已落盘 run 重算四种 p_cf 选择的校准准确率（I08/I10）。

日期: 2026-11-15

2026-11-15
变更说明：
  1. 初版：绕开 experiment.py --cf_ablation 的失效 bug（消融 run 的 expr_name 不含
     content_free_inputs 字段，与主 run 同名命中"已存在跳过"去重，消融结果与主 run 完全相同，
     见 issues I08）。本脚本不动主链路：逐样本标签概率直接读 results/samples/*.csv（已含
     全部推理产物），只为每种单输入内容无关选择补 1 次回声前向算 p_cf（每 run 3 次、
     每次 1 个短 prompt 批），再离线重算校准准确率。
  2. 校准准确率复用 calib.calibration.eval_accuracy（diagonal_W / identity_W 两模式）；
     p_cf 复用 get_p_content_free（与主链路同一实现，保证口径一致）。
  3. 内置两道正确性防线：①往返校验——用 CSV probs + raw JSON 的三输入 p_cf 重算
     diagonal_W 准确率，须与 raw JSON 记录的 acc_calibrated 一致（容差 1e-6，probs 列
     曾按 8 位小数舍入）；②抽样复算——第一个 run 用独立内联 numpy 路径（不调
     eval_accuracy）重算一种单输入选择的准确率并比对。
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calib.calibration import eval_accuracy, get_p_content_free
from calib.data_utils import load_dataset
from calib.experiment import RESULTS_DIR, _RUNNER_CACHE, get_runner

ABL_DIR = RESULTS_DIR / "cf_ablation"
VARIANTS = ("N/A", "", "[MASK]")  # 与主链路 content_free_inputs 默认三元组一致
# 离线脚本只做短 prompt 回声前向（p_cf），bs 取 D02 表各模型 trec 列（最短 prompt 安全档）；
# GPT2Runner.bs 须显式 set_batch_size 才存在（构造函数不初始化，experiment.py 主链路同样显式设置）
OFFLINE_BS = {"gpt2": 16, "gpt2-medium": 16, "gpt2-large": 12, "gpt2-xl": 2}


def read_samples_csv(expr_name):
    """读逐样本 CSV，返回 (probs 矩阵 (n,C), gold 列表)。probs 列为 JSON 数组字符串。"""
    path = RESULTS_DIR / "samples" / f"{expr_name}.csv"
    probs, golds = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            probs.append(json.loads(row["probs"]))
            golds.append(int(row["gold"]))
    return np.array(probs), golds


def verify_inline(probs, golds, p_cf):
    """独立复算路径：内联 W 构造 + 归一化 + argmax（不经过 eval_accuracy），防同一实现自证。"""
    C = probs.shape[1]
    W = np.linalg.inv(np.identity(C) * p_cf)
    hit = 0
    for row, gold in zip(probs, golds):
        p = row / np.sum(row)
        cal = W @ np.expand_dims(p, axis=-1)
        hit += int(int(np.argmax(cal)) == gold)
    return hit / len(golds)


def run_one_offline(model_name, dataset, num_shots, seed, runner, params):
    """对一个已落盘 run 离线重算四种内容无关输入选择的校准准确率。"""
    expr_name = f"{dataset}_{model_name}_{num_shots}shot_sub300_seed{seed}"
    raw_path = RESULTS_DIR / "raw" / f"{expr_name}.json"
    if not raw_path.exists():
        print(f"[缺主 run，跳过] {expr_name}（全网格未跑该配置？）")
        return None
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    out_path = ABL_DIR / f"{expr_name}.json"
    if out_path.exists():
        print(f"[跳过（消融已存在）] {expr_name}")
        return json.loads(out_path.read_text(encoding="utf-8"))

    probs, golds = read_samples_csv(expr_name)
    test_l = raw["test_labels"]
    assert len(probs) == len(test_l) == len(golds), f"{expr_name} 行数不一致"
    assert golds == list(test_l), f"{expr_name} gold 与 raw test_labels 不一致"

    # 防线3 模板漂移校验（镜像 experiment.py 跳过前核对）：p_cf 经 construct_prompt 消费
    # label_dict/prompt 前缀，若 data_utils.py 在主 run 落盘后被改动，单输入 p_cf 会与
    # 标签概率处于不同模板下，Table 3 静默失真且两道既有防线都测不到
    cfg = raw["config"]
    cur = {"label_dict": {str(k): v for k, v in params["label_dict"].items()},
           "prompt_prefix": params["prompt_prefix"],
           "q_prefix": params["q_prefix"], "a_prefix": params["a_prefix"]}
    drift = [f"{k}: run存档={cfg[k]} 当前={v}" for k, v in cur.items() if cfg[k] != v]
    assert not drift, f"{expr_name} data_utils 模板与主 run 存档不一致，p_cf 将失真：\n  " \
                      + "\n  ".join(drift)

    p_cf_full = np.array(raw["p_cf"])

    # 防线1 往返校验：CSV probs + 三输入 p_cf 重算须命中主 run 的校准准确率
    acc_full_rt = eval_accuracy(probs, test_l, mode="diagonal_W", p_cf=p_cf_full)
    rt_diff = abs(acc_full_rt - raw["accuracies"]["diagonal_W"])
    assert rt_diff <= 1e-6, f"{expr_name} 往返校验失败：重算 {acc_full_rt} vs 记录 " \
                            f"{raw['accuracies']['diagonal_W']}（差 {rt_diff}）"

    # 每种单输入补 1 次 p_cf 回声前向（train_s/train_l 取 raw JSON 存档，与主 run 同一批训练样例）
    train_s, train_l = raw["train_sentences"], raw["train_labels"]
    record = {"expr_name": expr_name, "model": model_name, "dataset": dataset,
              "shots": num_shots, "seed": seed,
              "p_cf_full": [float(x) for x in p_cf_full],
              "acc_diag_full": float(acc_full_rt),
              "acc_ident_full": eval_accuracy(probs, test_l, mode="identity_W", p_cf=p_cf_full),
              "roundtrip_diff": float(rt_diff)}
    for v in VARIANTS:
        p_cf_v = get_p_content_free(runner, params, train_s, train_l, (v,))
        record[f"p_cf_{v or 'empty'}"] = [float(x) for x in p_cf_v]
        record[f"acc_diag_{v or 'empty'}"] = eval_accuracy(probs, test_l, mode="diagonal_W", p_cf=p_cf_v)
        record[f"acc_ident_{v or 'empty'}"] = eval_accuracy(probs, test_l, mode="identity_W", p_cf=p_cf_v)
    # 四种选择（三输入平均 / N/A / [MASK] / 空串）的 diagonal_W 准确率是否互异
    record["four_diag_distinct"] = len({record["acc_diag_full"], record["acc_diag_N/A"],
                                        record["acc_diag_[MASK]"], record["acc_diag_empty"]}) == 4

    # 防线2 抽样复算：每个（模型×数据集×shot）的 seed0 用独立内联路径复核一种单输入选择
    if seed == 0:
        key = "acc_diag_N/A"
        v_check = verify_inline(probs, golds, np.array(record["p_cf_N/A"]))
        diff = abs(v_check - record[key])
        assert diff <= 1e-9, f"{expr_name} 独立复算不一致：{v_check} vs {record[key]}"
        record["inline_verify_diff"] = float(diff)

    ABL_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[完成] {expr_name} diag: full {record['acc_diag_full']:.4f} | N/A "
          f"{record['acc_diag_N/A']:.4f} | [MASK] {record['acc_diag_[MASK]']:.4f} | "
          f"空串 {record['acc_diag_empty']:.4f}")
    return record


def main():
    ap = argparse.ArgumentParser(description="离线内容无关输入消融（Table 3，I08/I10）")
    ap.add_argument("--model", default="gpt2,gpt2-medium,gpt2-large,gpt2-xl",
                    help="模型名（逗号分隔）")
    ap.add_argument("--pairs", default="sst2:1,agnews:0",
                    help="数据集:shot 对（逗号分隔）；默认论文 Table 3 设置：1-shot SST-2、0-shot AGNews")
    ap.add_argument("--seeds", type=int, default=5, help="种子数（0..n-1）")
    args = ap.parse_args()

    pairs = [(p.split(":")[0], int(p.split(":")[1])) for p in args.pairs.split(",")]
    all_records = []
    for model_name in args.model.split(","):
        runner = get_runner(model_name.strip(), fp16=False)  # 同模型只加载一次权重
        runner.set_batch_size(OFFLINE_BS.get(model_name.strip(), 4))
        for dataset, shots in pairs:
            _, _, _, _, params = load_dataset(dataset)
            params["model"] = model_name.strip()
            for seed in range(args.seeds):
                t0 = time.time()
                rec = run_one_offline(model_name.strip(), dataset, shots, seed, runner, params)
                if rec is not None:
                    all_records.append(rec)
                    print(f"    （{time.time() - t0:.1f}s）")
        # 模型循环末尾释放显存：_RUNNER_CACHE 永不清理，四模型同进程时权重累积
        # （0.52+1.45+3.10GB 后再加载 xl 的 6.13GB 必 OOM）——须先 del 局部引用再清缓存
        del runner
        _RUNNER_CACHE.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # 聚合表：按（模型 x 数据集 x shot）对 seed 取均值，四种选择的 diagonal_W 准确率
    print("\n===== Table 3 消融聚合（diagonal_W，seed 均值）=====")
    print(f"{'模型':<14}{'数据集':<8}{'shot':<5}{'full(三平均)':<14}{'N/A':<10}"
          f"{'[MASK]':<10}{'空串':<10}{'四值互异':<6}")
    groups = {}
    for r in all_records:
        groups.setdefault((r["model"], r["dataset"], r["shots"]), []).append(r)
    for (m, d, s), rs in sorted(groups.items()):
        def mean(key):
            return np.mean([r[key] for r in rs])
        distinct = all(r["four_diag_distinct"] for r in rs)
        print(f"{m:<14}{d:<8}{s:<5}{mean('acc_diag_full'):<14.4f}{mean('acc_diag_N/A'):<10.4f}"
              f"{mean('acc_diag_[MASK]'):<10.4f}{mean('acc_diag_empty'):<10.4f}"
              f"{'是' if distinct else '否':<6}")

    # 汇总 CSV 追加（重跑安全：整行重写同 expr_name 的旧行）
    summary_path = ABL_DIR / "cf_ablation_summary.csv"
    cols = ["expr_name", "model", "dataset", "shots", "seed",
            "p_cf_full", "p_cf_N/A", "p_cf_[MASK]", "p_cf_empty",
            "acc_diag_full", "acc_diag_N/A", "acc_diag_[MASK]", "acc_diag_empty",
            "acc_ident_full", "acc_ident_N/A", "acc_ident_[MASK]", "acc_ident_empty",
            "roundtrip_diff", "inline_verify_diff", "four_diag_distinct"]
    old_rows = {}
    if summary_path.exists():
        with open(summary_path, newline="", encoding="utf-8") as f:
            old_rows = {row["expr_name"]: row for row in csv.DictReader(f)}
    for r in all_records:
        old_rows[r["expr_name"]] = {c: (",".join(f"{x:.6f}" for x in r[c])
                                        if isinstance(r.get(c), list) else r.get(c, "")) for c in cols}
    ABL_DIR.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(sorted(old_rows.values(), key=lambda r: r["expr_name"]))
    print(f"已写 {summary_path.relative_to(RESULTS_DIR.parent)}（{len(old_rows)} 行）")


if __name__ == "__main__":
    main()
