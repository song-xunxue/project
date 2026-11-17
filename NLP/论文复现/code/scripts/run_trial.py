"""资源试跑：最小配置验证数据/权重/依赖/硬件全链路可用，记录输出与耗时（规范"资源试跑"）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：gpt2(124M) x SST-2 x 4-shot x seed0 x 50 条测试样本，输出准确率、p_cf、耗时；
     结果写 results/raw/trial_*.json，不进正式汇总。
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calib.calibration import eval_accuracy, get_p_content_free, get_label_probs
from calib.data_utils import construct_prompt, load_dataset
from calib.experiment import RESULTS_DIR, random_sampling
from calib.lm import GPT2Runner

import numpy as np


def main():
    model_name, dataset, shots, n_test, seed = "gpt2", "sst2", 4, 50, 0
    print(f"资源试跑：{model_name} x {dataset} x {shots}-shot x {n_test} 条 x seed {seed}")
    t0 = time.time()

    train_s, train_l, test_pool_s, test_pool_l, params = load_dataset(dataset)
    np.random.seed(0)
    test_s, test_l, test_ids = random_sampling(test_pool_s, test_pool_l, n_test)
    np.random.seed(seed)
    train_s, train_l, train_ids = random_sampling(train_s, train_l, shots)

    runner = GPT2Runner(model_name, fp16=False)
    runner.set_batch_size(16)

    t1 = time.time()
    prompts = [construct_prompt(params, train_s, train_l, s) for s in test_s]
    topk_list = runner.first_token_topk(prompts, num_log_probs=100)
    probs = get_label_probs(runner, params, topk_list, train_s, train_l, test_s)
    t2 = time.time()

    p_cf = get_p_content_free(runner, params, train_s, train_l, ("N/A", "", "[MASK]"))
    acc_orig = eval_accuracy(probs, test_l)
    acc_cal = eval_accuracy(probs, test_l, mode="diagonal_W", p_cf=p_cf)

    print(f"模型加载 {t1 - t0:.0f}s | 推理 {t2 - t1:.0f}s | 全程 {time.time() - t0:.0f}s")
    print(f"基线准确率 {acc_orig:.4f} | 校准后 {acc_cal:.4f} | p_cf {np.round(p_cf, 4).tolist()}")
    print(f"显存占用 {__import__('torch').cuda.max_memory_allocated() / 1024**3:.2f} GB")

    out = {"trial": True, "model": model_name, "dataset": dataset, "shots": shots,
           "n_test": n_test, "seed": seed, "acc_original": acc_orig, "acc_calibrated": acc_cal,
           "p_cf": [float(x) for x in p_cf], "load_seconds": round(t1 - t0, 1),
           "infer_seconds": round(t2 - t1, 1), "total_seconds": round(time.time() - t0, 1)}
    (RESULTS_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "raw" / "trial_sst2_gpt2.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写 results/raw/trial_sst2_gpt2.json")


if __name__ == "__main__":
    main()
