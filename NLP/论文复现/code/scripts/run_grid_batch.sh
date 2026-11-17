#!/usr/bin/env bash
# 全网格单模型批次（I07）：一个模型 x 三个数据集，每个数据集独立调用并按 D05 显式传 bs。
# 用法: bash scripts/run_grid_batch.sh <model> <bs_sst2> <bs_agnews> <bs_trec>
# 失败自动重试 2 次（同 bs，因为 raw JSON 配置校验锁死 bs，不可降档重试）；
# 数据集之间互相独立，单个失败不阻断后续。退出码 = 是否有数据集最终失败。
set -o pipefail
MODEL="$1"; BS_SST2="$2"; BS_AGNEWS="$3"; BS_TREC="$4"
R="C:/Users/26904/anaconda3/envs/repro/python.exe"
cd "$(dirname "$0")/.." || exit 1
# logs 目录无任何创建方（experiment.py 只建 raw/samples），缺失时 tee 失败 → pipefail 假报 FAILED
mkdir -p ../results/logs || exit 1

FAILED=0
declare -A BS=( [sst2]="$BS_SST2" [agnews]="$BS_AGNEWS" [trec]="$BS_TREC" )
for ds in sst2 agnews trec; do
  log="../results/logs/I07_${MODEL}_${ds}.log"
  rc=1
  for attempt in 1 2 3; do
    echo "===== ${MODEL} x ${ds} (bs=${BS[$ds]}) 第 ${attempt} 次尝试 开始 $(date '+%F %T') ====="
    PYTHONUTF8=1 HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 "$R" -u calib/experiment.py \
      --model "$MODEL" --dataset "$ds" --shots 0,1,4,8 --seeds 5 --subsample 300 \
      --bs "${BS[$ds]}" 2>&1 | tee -a "$log"
    rc=$?
    echo "===== ${MODEL} x ${ds} 第 ${attempt} 次尝试 EXIT=${rc} $(date '+%F %T') ====="
    [ "$rc" -eq 0 ] && break
    sleep 10  # OOM 后稍候重试，给驱动回收显存的时间
  done
  [ "$rc" -ne 0 ] && { echo "!!! ${MODEL} x ${ds} 三次尝试均失败"; FAILED=1; }
done
echo "===== 批次 ${MODEL} 结束 FAILED=${FAILED} $(date '+%F %T') ====="
exit "$FAILED"
