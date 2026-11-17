# 实验运行台账

> 每次启动一个批次记一行；开始时间取启动时刻，结束时间与结果列在批次退出后回填；
> 异常列如实记录报错/重启，无异常写"无"。命令中的 `$R` = conda 环境 `repro` 的 python.exe。

| 批次 | 命令 | 开始时间 | 结束时间 | run数/结果 | 显存/耗时 | 异常 |
|---|---|---|---|---|---|---|
| P1 资源试跑（gpt2×SST-2×4-shot×50条，fp32 bs16） | `cd code && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R scripts/run_trial.py 2>&1 \| tee ../results/logs/P1_trial.log` | 2026-11-03 22:59:41 | 2026-11-03 22:59:45 | 1 run；基线 0.4200 / 校准 0.5000 / p_cf [0.565, 0.435]，`results/raw/trial_sst2_gpt2.json` 已落盘 | 峰值 2.18 GB；加载 2s + 推理 1s，全程 3s | 无 |
| P2 首次启动（gpt2×sst2×shots 0,1,4,8×seed0×sub300，fp32 bs16） | `cd code && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R calib/experiment.py --model gpt2 --dataset sst2 --shots 0,1,4,8 --seeds 1 --subsample 300 --bs 16`（链式 tee，未设 pipefail） | 2026-11-03 22:59:58 | 2026-11-03 22:59:59 | 0/4 run（未产出任何配置结果） | — | **启动即失败**：`ModuleNotFoundError: No module named 'calib'`。原因：以路径方式直跑时 `sys.path[0]` 是 `calib/` 而非 `code/`；且 tee 吞掉退出码使 `&&` 链误报 ALL DONE。**已修复**：主循环在 `experiment.py` 头部加 `sys.path.insert(code/)`（源头修复，README 命令原样可跑），后续链式命令一律 `set -o pipefail` |
| P2 重试（同上配置） | `cd code && set -o pipefail && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R calib/experiment.py --model gpt2 --dataset sst2 --shots 0,1,4,8 --seeds 1 --subsample 300 --bs 16 2>&1 \| tee ../results/logs/P2_smoke_gpt2_sst2.log` | 2026-11-03 23:00:42 | 2026-11-03 23:01:07 | 4/4 run 落盘（0-shot 基线 0.7267/校准 0.6067；1-shot 0.4833/0.5067；4-shot 0.4933/0.5000；8-shot 0.4967/0.4933）；samples CSV ×4 + summary.csv ×4 行 | 单 run 推理 1.5–16.2s；无 OOM | 无 |
| P2 断点验证（同 P2 命令重跑） | 同 P2 重试命令 | 2026-11-03 23:07 | 2026-11-03 23:07 | 4/4 提示"跳过（已存在）"，EXIT=0——断点去重机制验证通过（D04 前提成立） | 加载后秒级退出 | 无 |
| P2b 冒烟（gpt2×agnews,trec×shots 0,1,4,8×seed0×sub300，fp32 bs16） | `cd code && set -o pipefail && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R calib/experiment.py --model gpt2 --dataset agnews,trec --shots 0,1,4,8 --seeds 1 --subsample 300 --bs 16 2>&1 \| tee ../results/logs/P2b_smoke_gpt2_agnews_trec.log` | 2026-11-03 23:03:17 | 2026-11-03 23:04:47 | 8/8 run 落盘（AGNews 1-shot 校准 0.5233 为最大正收益 +28.7pp；TREC 8-shot 校准 0.0333 为最大负收益）；summary.csv 累计 12 行 | AGNews 单 run 10–31s，TREC 2–4s | **AGNews 0-shot OOM 告警**：CUDACachingAllocator 分配 1.9GB 失败（free 0）后自恢复，批次未中断（EXIT=0）——bs=16×长文本 fp32 顶到 8GB 边缘，记入 D05，全网格前须按模型×数据集核定 bs |
| I09 bs 短试跑（4模型×3数据集候选 bs 探针，8-shot×50+1条） | `cd code && set -o pipefail && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R scripts/bs_probe.py --plan 2>&1 \| tee ../results/logs/I09_bs_probe.log` | 2026-11-15 23:42 | 2026-11-16 00:1x | 12 组合核定 + xl bs2 备胎 2 项：gpt2 16/16/16（4.32/5.44/2.42GB）、medium 16/8/16（5.92/5.46/3.76GB）、large 12/4/12（6.47/5.89/5.35GB）、xl 2/2/2（7.04/8.16/6.65GB）；探针 JSON 落 `results/probes/`（14 个） | xl 高档位超物理显存但 WDDM 溢出兜底无一 OOM，bs2 全面快于 bs4（agnews 37.3s vs 72.1s） | 无（淘汰组合均为判定线拒绝，非崩溃） |
| I07 全网格 gpt2 批次（sst2,agnews,trec × shots 0,1,4,8 × seeds 0-4，fp32 bs16） | `bash scripts/run_grid_batch.sh gpt2 16 16 16` | 2026-11-16 01:35:51 | 2026-11-16 01:42:26 | 60/60 run（12 冒烟 seed0 跳过复用，48 新落盘）；三数据集 EXIT=0 一次通过 | 全程 6m35s（sst2 1m47s / agnews 3m44s / trec 1m04s） | AGNews 2 处 allocator 自恢复 OOM 告警（未中断批次） |
| I07 全网格 gpt2-medium 批次（bs 16/8/16） | `bash scripts/run_grid_batch.sh gpt2-medium 16 8 16` | 2026-11-16 01:42:26 | 2026-11-16 01:55:57 | 60/60 run 全新落盘；三数据集 EXIT=0 一次通过 | 全程 13m31s（sst2 3m21s / agnews 7m53s / trec 2m17s） | AGNews 1 处 allocator 自恢复 OOM 告警 |
| I07 全网格 gpt2-large 批次（bs 12/4/12） | `bash scripts/run_grid_batch.sh gpt2-large 12 4 12` | 2026-11-16 01:55:57 | 2026-11-16 02:23:09 | 60/60 run 全新落盘；三数据集 EXIT=0 一次通过 | 全程 27m12s（sst2 6m26s / agnews 16m20s / trec 4m26s） | 无 |
| I07 全网格 gpt2-xl 批次（bs 2/2/2） | `bash scripts/run_grid_batch.sh gpt2-xl 2 2 2` | 2026-11-16 02:23:09 | 2026-11-16 03:15:40 | 60/60 run 全新落盘；三数据集 EXIT=0 一次通过 | 全程 52m31s（sst2 13m07s / agnews 29m42s / trec 9m42s）；fp32+WDDM 溢出无崩溃（D02 预判成立） | 无 |
| I07 全量校验与汇总 | `$R scripts/check_results.py`；`$R calib/experiment.py --aggregate_only` 另存 aggregate.txt | 2026-11-16 03:16 | 2026-11-16 03:16:52 | 241 文件（240 run + 1 trial）独立复算全过；aggregate.txt 48 组（4模型×3数据集×4shots，5 seeds 均值±std） | 约 1 分钟 | 无 |
| I10 Table 3 消融全量（sst2:1 + agnews:0 × 4模型 × seeds 0-4） | `cd code && PYTHONUTF8=1 HF_HUB_OFFLINE=1 $R scripts/cf_ablation_offline.py --model gpt2,gpt2-medium,gpt2-large,gpt2-xl --pairs sst2:1,agnews:0 --seeds 5 2>&1 \| tee ../results/logs/I10_cf_ablation.log` | 2026-11-16 03:16 | 2026-11-16 03:17:01 | 40 run 消融完成（38 新 + 2 复用干跑记录）；往返校验 + seed0 独立复算全过；`results/cf_ablation/` 50 记录 | 约 1 分钟（4 模型加载 + 38×3 短回声前向） | 无 |

## 回填约定

- 批次正常退出：回填"结束时间""run数/结果""显存/耗时"三列，异常列保持"无"。
- 批次异常退出：异常列写明报错最后一行 + 已定位原因 + 重启计划，随后**另起一行**记录重启批次（不覆盖原行，保留失败证据供中期记录第⑤字段引用）。
- 全网格（第二期 I07）按模型分批，每模型一行。
