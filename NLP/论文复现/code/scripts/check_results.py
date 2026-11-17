"""结果完整性校验：独立复算准确率，交叉核对 raw JSON / samples CSV / summary.csv 三类产物。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：逐个 raw/*.json 独立复算（从 samples CSV 的逐样本概率重算基线/校准准确率与
     预测翻转数，与 JSON 声明值比对），并核对 summary.csv 行、配置一致性、p_cf 归一性；
     试跑文件（trial=True）只做字段与量级检查。任何不一致退出码非 0。
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = CODE_DIR.parent / "results"

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print(f"  [FAIL] {msg}")


def check_full_run(raw_path):
    """正式运行（非 trial）的完整校验：独立复算 + 三产物交叉核对。"""
    r = json.loads(raw_path.read_text(encoding="utf-8"))
    name = r["expr_name"]
    c = r["config"]
    print(f"[{name}]")

    # 1. 文件名与配置一致性
    expect = f"{c['dataset']}_{c['model']}_{c['num_shots']}shot_sub{c['subsample_test_set']}_seed{c['seed']}"
    if name != expect:
        fail(f"expr_name 与 config 不符: {name} != {expect}")
    if len(r["train_ids"]) != c["num_shots"]:
        fail(f"训练样例数 {len(r['train_ids'])} != shots {c['num_shots']}")
    if len(set(r["train_ids"])) != len(r["train_ids"]):
        fail("训练样例 ID 有重复")
    if len(r["test_ids"]) != c["subsample_test_set"]:
        fail(f"测试样本数 {len(r['test_ids'])} != 子集 {c['subsample_test_set']}")

    # 2. p_cf 检查：全正、归一化
    p_cf = np.array(r["p_cf"])
    if (p_cf <= 0).any():
        fail(f"p_cf 有非正分量: {p_cf}")
    if abs(p_cf.sum() - 1.0) > 1e-6:
        fail(f"p_cf 未归一化: sum={p_cf.sum()}")

    # 3. 从逐样本 CSV 独立复算
    samples_path = RESULTS_DIR / "samples" / f"{name}.csv"
    if not samples_path.exists():
        fail(f"缺逐样本文件: {samples_path.name}")
        return
    with open(samples_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(r["test_ids"]):
        fail(f"逐样本行数 {len(rows)} != 测试数 {len(r['test_ids'])}")
    n = len(r["config"]["label_dict"])  # 类数（label_dict 以字符串键存储）

    acc_orig_mismatch = acc_cal_mismatch = flip_mismatch = 0
    for row in rows:
        probs = np.array(json.loads(row["probs"]))
        if len(probs) != n:
            fail(f"样本 {row['sample_id']} 概率维数 {len(probs)} != 类数 {n}")
            break
        gold = int(row["gold"])
        p_norm = probs / probs.sum()
        if int(np.argmax(p_norm)) != int(row["pred_original"]):
            acc_orig_mismatch += 1
        W = np.diag(1.0 / p_cf)
        if int(np.argmax(W @ p_norm)) != int(row["pred_calibrated"]):
            acc_cal_mismatch += 1
    acc_orig = float(np.mean([int(x["pred_original"]) == int(x["gold"]) for x in rows]))
    acc_cal = float(np.mean([int(x["pred_calibrated"]) == int(x["gold"]) for x in rows]))
    num_flip = sum(1 for x in rows if x["pred_original"] != x["pred_calibrated"])
    if acc_orig_mismatch or acc_cal_mismatch:
        fail(f"预测复算不一致: original {acc_orig_mismatch} 处, calibrated {acc_cal_mismatch} 处")
    if abs(acc_orig - r["accuracies"]["original"]) > 1e-9:
        fail(f"基线准确率复算 {acc_orig:.6f} != 声明 {r['accuracies']['original']:.6f}")
    if abs(acc_cal - r["accuracies"]["diagonal_W"]) > 1e-9:
        fail(f"校准准确率复算 {acc_cal:.6f} != 声明 {r['accuracies']['diagonal_W']:.6f}")
    if num_flip != r["num_flip"]:
        fail(f"翻转数复算 {num_flip} != 声明 {r['num_flip']}")

    # 4. summary.csv 行核对
    with open(RESULTS_DIR / "summary.csv", "r", encoding="utf-8") as f:
        srows = [x for x in csv.DictReader(f) if x["expr_name"] == name]
    if len(srows) != 1:
        fail(f"summary.csv 中 {name} 出现 {len(srows)} 次")
    else:
        s = srows[0]
        if s["acc_original"] != f"{r['accuracies']['original']:.4f}" or \
           s["acc_calibrated"] != f"{r['accuracies']['diagonal_W']:.4f}":
            fail("summary.csv 准确率与 raw JSON 不一致")
    if not FAILS or not any(name in m for m in FAILS):
        print(f"  [PASS] 基线 {acc_orig:.4f} | 校准 {acc_cal:.4f} | 翻转 {num_flip} | 独立复算一致")


def check_trial(raw_path):
    """资源试跑文件的字段与量级检查（无逐样本产物）。"""
    r = json.loads(raw_path.read_text(encoding="utf-8"))
    print(f"[{raw_path.stem}] (trial)")
    for key in ("model", "dataset", "shots", "n_test", "acc_original", "acc_calibrated", "p_cf"):
        if key not in r:
            fail(f"trial 缺字段: {key}")
    if 0.0 <= r.get("acc_original", -1) <= 1.0 and 0.0 <= r.get("acc_calibrated", -1) <= 1.0:
        print(f"  [PASS] 基线 {r['acc_original']:.4f} | 校准 {r['acc_calibrated']:.4f} | 字段齐全")
    else:
        fail("trial 准确率越界")


def main():
    raw_dir = RESULTS_DIR / "raw"
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        print("results/raw/ 为空， nothing to check")
        return
    for path in files:
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("trial"):
            check_trial(path)
        else:
            check_full_run(path)
    print("=" * 60)
    if FAILS:
        print(f"校验失败 {len(FAILS)} 处")
        sys.exit(1)
    print(f"全部通过（{len(files)} 个结果文件）")


if __name__ == "__main__":
    main()
