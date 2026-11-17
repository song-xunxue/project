"""bs 短试跑：按（模型 x 数据集）核定全网格批大小，测显存峰值（I09 / 决策 D05）。

日期: 2026-11-15

2026-11-15
变更说明：
  1. 初版：每个候选 bs 用独立子进程跑 8-shot x 50 条探针（含 top-k / 回声 / p_cf 三阶段，
     与 run_one 完整推理链一致），记录显存 peak allocated / reserved 与耗时；
     探针集强制并入全测试池最长样本，覆盖最坏 batch；候选 bs 降序尝试，达标即停。
  2. 判定标准：peak reserved <= SAFE_CAP_GB(6.6) 为安全通过；<= HARD_CAP_GB(7.0) 为
     边缘通过（仅当无安全档时选用）；发生 CUDA OOM 即淘汰。8GB 卡实测可用约 7.9GB，
     留约 1GB 余量给分配器碎片与 CUDA 上下文。
  3. gpt2 不在候选搜索内（bs=16 已被冒烟 seed0 文件的配置校验锁死，且 P2b 实证 agnews
     bs16 可存活），仅做一次记录性探针量化其显存余量。
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROBE_DIR = Path(__file__).resolve().parent.parent.parent / "results" / "probes"
SAFE_CAP_GB = 6.6   # 安全阈值：peak reserved 低于此值直接采用该 bs
HARD_CAP_GB = 7.0   # 边缘阈值：仅当无 bs 达安全阈值时，取不超过此值的最大候选
N_TEST = 50         # 探针测试条数（与 P1 资源试跑一致的量级）
PROBE_SHOTS = 8     # 用最长 prompt 的 8-shot 探测（覆盖网格中最大上下文）

# 候选 bs（降序 = 从高往低试，达标即停）：gpt2 仅记录性探针；
# medium/large/xl 按 README 预估档位 + 向上一档试探速度、AGNews 长文本另降一档
PLAN = {
    "gpt2":        {"sst2": [16],    "agnews": [16],   "trec": [16]},
    "gpt2-medium": {"sst2": [16, 12], "agnews": [12, 8], "trec": [16, 12]},
    "gpt2-large":  {"sst2": [12, 8],  "agnews": [8, 4],  "trec": [12, 8]},
    "gpt2-xl":     {"sst2": [8, 4],   "agnews": [4, 2],  "trec": [8, 4]},
}


def probe_single(model_name, dataset, bs):
    """单次探针（子进程内执行）：完整推理三阶段，返回显存峰值与耗时。"""
    import numpy as np
    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from calib.calibration import eval_accuracy, get_label_probs, get_p_content_free
    from calib.data_utils import construct_prompt, load_dataset
    from calib.experiment import random_sampling
    from calib.lm import GPT2Runner

    t0 = time.time()
    train_pool_s, train_pool_l, test_pool_s, test_pool_l, params = load_dataset(dataset)

    # 测试子集：seed 0 抽 50 条（与正式 run 的冻结子集同一抽样方式），再强制并入
    # 全池最长样本，确保探针覆盖最坏 batch 的填充长度
    np.random.seed(0)
    test_s, test_l, test_ids = random_sampling(test_pool_s, test_pool_l, N_TEST)
    longest = max(range(len(test_pool_s)), key=lambda i: len(test_pool_s[i]))
    if longest not in test_ids:
        test_s.append(test_pool_s[longest])
        test_l.append(test_pool_l[longest])
        test_ids.append(longest)

    # 训练样例：8-shot seed 0（决定 prompt 长度的另一部分）
    np.random.seed(0)
    train_s, train_l, train_ids = random_sampling(train_pool_s, train_pool_l, PROBE_SHOTS)

    runner = GPT2Runner(model_name, fp16=False)
    runner.set_batch_size(bs)
    params["model"] = model_name
    load_done = time.time()

    prompts = [construct_prompt(params, train_s, train_l, s) for s in test_s]
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    reserved_after_load = torch.cuda.max_memory_reserved() / 1024 ** 3

    t1 = time.time()
    topk_list = runner.first_token_topk(prompts, num_log_probs=100)
    probs = get_label_probs(runner, params, topk_list, train_s, train_l, test_s)
    p_cf = get_p_content_free(runner, params, train_s, train_l, ("N/A", "", "[MASK]"))
    t2 = time.time()

    acc_orig = eval_accuracy(probs, test_l)  # 探针准确率仅作健全性指标，不进正式结果
    peak_alloc = torch.cuda.max_memory_allocated() / 1024 ** 3
    peak_reserved = torch.cuda.max_memory_reserved() / 1024 ** 3

    return {"model": model_name, "dataset": dataset, "bs": bs, "oom": False,
            "n_test": len(test_s), "shots": PROBE_SHOTS,
            "acc_probe": round(float(acc_orig), 4),
            "p_cf_head": [round(float(x), 4) for x in p_cf[:2]],
            "reserved_after_load_gb": round(reserved_after_load, 2),
            "peak_allocated_gb": round(peak_alloc, 2),
            "peak_reserved_gb": round(peak_reserved, 2),
            "load_seconds": round(load_done - t0, 1),
            "infer_seconds": round(t2 - t1, 1)}


def main():
    ap = argparse.ArgumentParser(description="bs 短试跑（I09/D05）")
    ap.add_argument("--plan", action="store_true", help="父模式：按 PLAN 逐组合降序试探")
    ap.add_argument("--model", default=None, help="单探针模式：模型名")
    ap.add_argument("--dataset", default=None, help="单探针模式：数据集")
    ap.add_argument("--bs", type=int, default=None, help="单探针模式：批大小")
    args = ap.parse_args()

    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1"}
    py = sys.executable

    if not args.plan:
        # 单探针模式：OOM 不抛出，落盘 oom=true 供父模式判读
        out_path = PROBE_DIR / f"{args.dataset}_{args.model}_bs{args.bs}.json"
        try:
            result = probe_single(args.model, args.dataset, args.bs)
        except Exception as e:  # noqa: BLE001
            # CUDA OOM（torch.cuda.OutOfMemoryError 或 RuntimeError）消息均含 out of memory；
            # 其余异常照常抛出，不吞
            if "out of memory" not in str(e).lower():
                raise
            result = {"model": args.model, "dataset": args.dataset, "bs": args.bs,
                      "oom": True, "error": str(e)[:300]}
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return

    # 父模式：逐（模型 x 数据集）降序试探，达标即停
    summary = {}
    for model_name, per_ds in PLAN.items():
        for dataset, candidates in per_ds.items():
            chosen = None
            for bs in candidates:
                probe_json = PROBE_DIR / f"{dataset}_{model_name}_bs{bs}.json"
                if probe_json.exists():
                    r = json.loads(probe_json.read_text(encoding="utf-8"))
                    print(f"[复用已有探针] {model_name} x {dataset} bs={bs}")
                else:
                    print(f"[探针] {model_name} x {dataset} bs={bs} ...", flush=True)
                    cp = subprocess.run([py, __file__, "--model", model_name,
                                         "--dataset", dataset, "--bs", str(bs)],
                                        env=env, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace")
                    if cp.returncode != 0:
                        print(cp.stdout[-800:])
                        print(cp.stderr[-800:])
                        raise SystemExit(f"探针子进程异常退出 rc={cp.returncode}")
                    r = json.loads(cp.stdout.strip().splitlines()[-1])
                verdict = "OOM淘汰"
                if not r["oom"]:
                    pr = r["peak_reserved_gb"]
                    verdict = ("安全通过" if pr <= SAFE_CAP_GB
                               else ("边缘通过" if pr <= HARD_CAP_GB else "超阈值淘汰"))
                print(f"    -> reserved {r.get('peak_reserved_gb', '-')} GB | "
                      f"{r.get('infer_seconds', '-')}s | {verdict}", flush=True)
                if verdict in ("安全通过", "边缘通过"):
                    chosen = {**r, "verdict": verdict}
                    if verdict == "安全通过":
                        break  # 达安全阈值即停，不再试更低 bs
            summary[f"{model_name}|{dataset}"] = chosen

    print("\n===== bs 核定汇总（peak reserved，GB）=====")
    print(f"{'模型':<14}{'数据集':<8}{'bs':<5}{'判定':<6}{'reserved':<10}{'推理s':<8}")
    for key, r in summary.items():
        m, d = key.split("|")
        if r is None:
            print(f"{m:<14}{d:<8}{'-':<5}{'全部淘汰':<6}")
        else:
            print(f"{m:<14}{d:<8}{r['bs']:<5}{r['verdict']:<6}{r['peak_reserved_gb']:<10}"
                  f"{r['infer_seconds']:<8}")
    (PROBE_DIR / "probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写 results/probes/probe_summary.json")


if __name__ == "__main__":
    main()
