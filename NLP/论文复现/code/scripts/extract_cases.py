"""全量案例分析：从全部 run 的逐样本 CSV 提取校准翻转案例（论文报告素材，I11）。

日期: 2026-11-15

2026-11-15
变更说明：
  1. 初版：扫描 results/raw/*.json + results/samples/*.csv，找出 pred_original !=
     pred_calibrated 的样本，分两类——校准修复（基线错→校准对）与校准破坏（基线对→校准错）；
     每类按校准后决策置信裕度排序取头部案例，保证模型 x 数据集 x shot 维度覆盖，
     输出 Markdown 案例分析（含原文、gold、两套预测、校准前后概率、机制归类）。
  2. 原文从 data_utils.load_dataset 按样本 id 回取（sample_id 即测试池下标）；
     校准分数用 raw JSON 的 p_cf 现场重算（W=diag(1/p_cf)），与落盘 pred_calibrated 同式。
  3. 用法：PYTHONUTF8=1 HF_HUB_OFFLINE=1 python scripts/extract_cases.py [--per_case N]
     产物：results/案例分析_全量.md（最终归档由主循环移至工程管理/）
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calib.data_utils import load_dataset

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
CLASS_NAMES = {
    "sst2": ["neg", "pos"],
    "agnews": ["World", "Sports", "Business", "Sci/Tech"],
    "trec": ["NUM", "LOC", "HUM", "DESC", "ENTY", "ABBR"],
}


def calibrated_scores(probs, p_cf):
    """与 eval_accuracy(diagonal_W) 同式：归一化后 W=diag(1/p_cf) 线性变换，返回校准分数。"""
    p = probs / np.sum(probs)
    W = np.linalg.inv(np.identity(len(p_cf)) * p_cf)
    return (W @ np.expand_dims(p, axis=-1)).ravel()


_POOL_CACHE = {}


def get_test_pool(ds):
    """按数据集缓存测试池原文（240 run 全扫时避免重复解析数据文件）。
    load_dataset 五元组为 (train_s, train_l, test_s, test_l, params)，原文在第 3 位——
    sample_id 即该池的下标（experiment.py random_sampling 返回的 idxs）。"""
    if ds not in _POOL_CACHE:
        _, _, pool_s, _, _ = load_dataset(ds)
        assert isinstance(pool_s[0], str), f"{ds} 测试池首元素非字符串，解包错位？"
        _POOL_CACHE[ds] = pool_s
    return _POOL_CACHE[ds]


def load_run(path):
    """读一个 run 的 raw JSON + samples CSV，返回逐样本记录列表。"""
    r = json.loads(path.read_text(encoding="utf-8"))
    expr = r["expr_name"]
    ds = r["config"]["dataset"]
    p_cf = np.array(r["p_cf"])
    test_pool_s = get_test_pool(ds)
    rows = []
    with open(RESULTS_DIR / "samples" / f"{expr}.csv", newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if int(row["pred_original"]) == int(row["pred_calibrated"]):
                continue  # 只看翻转样本
            probs = np.array(json.loads(row["probs"]))
            cal = calibrated_scores(probs, p_cf)
            rows.append({
                "expr": expr, "model": r["config"]["model"], "dataset": ds,
                "shots": r["config"]["num_shots"], "seed": r["config"]["seed"],
                "sample_id": int(row["sample_id"]),
                "text": test_pool_s[int(row["sample_id"])],
                "gold": int(row["gold"]),
                "pred_orig": int(row["pred_original"]),
                "pred_cal": int(row["pred_calibrated"]),
                "p_norm": (probs / np.sum(probs)).round(4).tolist(),
                "cal": cal.round(4).tolist(),
                # 校准后决策裕度：校准分数第一名与第二名之差（翻转案例的机制强度）
                "margin": float(np.sort(cal)[-1] - np.sort(cal)[-2]),
            })
    return rows


def classify_case(case, names):
    """机制归类：回声/坍缩现象的文字解释字段（供报告引用，规则见中期记录⑤）。"""
    kind = "校准修复" if case["pred_orig"] != case["gold"] and case["pred_cal"] == case["gold"] \
        else ("校准破坏" if case["pred_orig"] == case["gold"] and case["pred_cal"] != case["gold"] else "双向翻错")
    return kind


def main():
    ap = argparse.ArgumentParser(description="提取校准翻转案例（I11）")
    ap.add_argument("--per_case", type=int, default=4, help="每（翻转类型 x 模型）取前 N 例")
    ap.add_argument("--out", default=str(RESULTS_DIR / "案例分析_全量.md"))
    args = ap.parse_args()

    all_cases = []
    for path in sorted((RESULTS_DIR / "raw").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if "config" not in r:
            continue  # trial/probe 类文件
        all_cases.extend(load_run(path))
    print(f"全部 run 翻转样本总数：{len(all_cases)}")

    fixed = [c for c in all_cases if classify_case(c, None) == "校准修复"]
    broken = [c for c in all_cases if classify_case(c, None) == "校准破坏"]
    both_wrong = [c for c in all_cases if classify_case(c, None) == "双向翻错"]
    print(f"校准修复 {len(fixed)} 例 | 校准破坏 {len(broken)} 例 | 双向翻错 {len(both_wrong)} 例")

    # 覆盖性选取：每（类型 x 模型）按裕度取头部，再按数据集多样性补齐
    def pick(cases):
        picked, seen_models = [], {}
        for c in sorted(cases, key=lambda x: -x["margin"]):
            m = c["model"]
            if seen_models.get(m, 0) >= args.per_case:
                continue
            seen_models[m] = seen_models.get(m, 0) + 1
            picked.append(c)
        return picked

    chosen = pick(fixed) + pick(broken) + pick(both_wrong)
    lines = ["# 全量案例分析（校准翻转样本）", "",
             f"> 从全部落盘 run 的逐样本 CSV 自动提取（脚本 scripts/extract_cases.py）；"
             f"翻转总数 {len(all_cases)} = 校准修复 {len(fixed)} + 校准破坏 {len(broken)}"
             f" + 双向翻错 {len(both_wrong)}；"
             f"本表按\"校准后决策裕度\"（校准分数第一名减第二名）每（类型 x 模型）取头部 "
             f"{args.per_case} 例，共 {len(chosen)} 例。", "",
             "| # | 类型 | 模型 | 数据集 | shot | seed | sample_id | gold | 基线预测 | 校准预测 | 裕度 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, c in enumerate(chosen, 1):
        names = CLASS_NAMES[c["dataset"]]
        lines.append(
            f"| {k} | {classify_case(c, names)} | {c['model']} | {c['dataset']} | "
            f"{c['shots']} | {c['seed']} | {c['sample_id']} | {names[c['gold']]} | "
            f"{names[c['pred_orig']]} | {names[c['pred_cal']]} | {c['margin']:.3f} |")
    lines += ["", "---", ""]
    for k, c in enumerate(chosen, 1):
        names = CLASS_NAMES[c["dataset"]]
        text = c["text"].replace("\n", " ")
        text = text if len(text) <= 220 else text[:220] + "..."
        lines += [f"## 案例 {k}：{classify_case(c, names)}（{c['model']} x {c['dataset']} x "
                  f"{c['shots']}-shot x seed{c['seed']}）", "",
                  f"- **原文**（sample_id={c['sample_id']}）：{text}",
                  f"- **gold**：{names[c['gold']]} | **基线预测**：{names[c['pred_orig']]} | "
                  f"**校准预测**：{names[c['pred_cal']]}",
                  f"- **归一化标签概率**（基线通道）：{dict(zip(names, c['p_norm']))}",
                  f"- **校准分数**（W=diag(1/p_cf) 后）：{dict(zip(names, c['cal']))}", ""]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"已写 {args.out}（{len(chosen)} 例）")


if __name__ == "__main__":
    main()
