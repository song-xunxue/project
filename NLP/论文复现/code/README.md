# 复现工程说明（Calibrate Before Use, Zhao et al. ICML 2021）

对应提交规范 README 要求：环境版本、数据取得方式、命令、预计耗时、预期输出及逐条结果入口。
**当前状态：全量复现已完成（2026-11-16）：全网格 240 run（4 模型×3 数据集×4 shots×5 seeds）一次通过零重试，241 文件独立复算校验通过，Table 3 消融与汇总图已产出；待最终提交物（report/slides）。**

## 1. 环境版本

- conda 环境 `repro`（Python 3.11，独立环境，不影响系统其他 Python 环境）
- 依赖：torch（CUDA 12.6 构建）+ transformers + datasets + pandas + matplotlib
- 硬件：RTX 4060 Laptop 8GB（单卡即可，无训练只有推理）
- 安装命令（已执行）：
  ```bash
  C:/Users/26904/anaconda3/envs/repro/python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu126
  C:/Users/26904/anaconda3/envs/repro/python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple transformers datasets pandas matplotlib
  ```

## 2. 数据取得方式（均已就位）

| 数据集 | 文件 | 来源与说明 |
|---|---|---|
| SST-2 | `data/sst2/stsa.binary.train|dev`（作者仓库原文件） | 作者仓库 master 分支，经 cdn.jsdelivr.net 镜像下载 |
| SST-2 test | `data/sst2/stsa.binary.test`（1821 条） | 作者仓库缺失该文件；取自 AcademiaSinicaNLPLab/sentiment_dataset 镜像（同为 Socher SST 二分类标准划分，格式一致） |
| TREC | `data/trec/train.txt`(5452) `test.txt`(500) | 作者仓库原文件 |
| AGNews | `data/agnews/train.csv`(120000) `test.csv`(7600) `classes.txt` | 作者仓库原文件，经 ghfast.top 镜像下载 |

各文件来源、许可与 SHA256 详见 `data/README.md`。

## 3. 模型权重（下载到 `models/`，**不进最终提交包**，按规范提供路径+校验）

```bash
cd code
PYTHONUTF8=1 C:/Users/26904/anaconda3/envs/repro/python.exe scripts/download_models.py
# 经 HF_ENDPOINT=https://hf-mirror.com 镜像下载 gpt2 / gpt2-medium / gpt2-large / gpt2-xl
# 脚本内已默认 HF_HUB_DISABLE_XET=1——镜像不代理 Xet 存储协议，不禁用会 404
```

## 3.1 管线自检（2026-11-03 已通过）

用最小规格 gpt2 验证过全链路连通：数据加载→prompt 构造→首 token top-k→回声补全→p_cf→校准评测。
注意两个 transformers 5.x 适配点（已改好）：`tokenizer(...)` 取代已移除的 `batch_encode_plus`；
推理需 `HF_HUB_OFFLINE=1`（可选，避免联网检查）时模型从本地 models/ 目录加载。

## 3.2 已完成运行记录（2026-11-03，中期进展记录的证据基础）

| 批次 | 命令要点 | 结果 | 日志 |
|---|---|---|---|
| P1 资源试跑 | `scripts/run_trial.py`（gpt2×SST-2×4-shot×50 条） | 基线 0.4200 / 校准 0.5000 / 显存峰值 2.18 GB / 全程 3s | `results/logs/P1_trial.log` |
| P2 冒烟 SST-2 | `calib/experiment.py --model gpt2 --dataset sst2 --shots 0,1,4,8 --seeds 1 --subsample 300 --bs 16` | 4 配置落盘（详表见 `../中期进展记录.md` ③） | `results/logs/P2_smoke_gpt2_sst2.log` |
| P2b 冒烟 AGNews/TREC | 同上，`--dataset agnews,trec` | 8 配置落盘；AGNews 0-shot 有 OOM 重试告警（bs=16×长文本顶到 8GB 边缘，未崩溃） | `results/logs/P2b_smoke_gpt2_agnews_trec.log` |

完整性校验：`PYTHONUTF8=1 $R scripts/check_results.py`——从逐样本 CSV 独立复算准确率/翻转数并与 raw JSON、summary.csv 交叉核对，当前 13/13 通过。
冒烟与全网格 seed0 配置完全一致（同 fp32 同 bs），全网格运行时自动去重复用。
注意：直接以 `python calib/experiment.py` 运行需要在 experiment.py 顶部的 sys.path 处理（2026-11-03 已加入），
或改用 `python -m calib.experiment`；`results/logs/` 为运行日志归档目录（tee 落盘）。

## 3.3 已下载权重的版本与校验（model.safetensors，hf-mirror.com，2026-11-03）

| 模型 | 参数量 | safetensors 大小 | SHA256（前 16 位） |
|---|---|---|---|
| gpt2 | 124M | 522.7 MB | `248dfc3911869ec4` |
| gpt2-medium | 355M | 1449.6 MB | `fc5a354a19255ad4` |
| gpt2-large | 774M | 3096.7 MB | `5f47f3e12f91cd33` |
| gpt2-xl | 1.5B | 6133.9 MB | `0f8b28eb05a8075f` |

## 4. 运行命令与预计耗时

```bash
cd 论文复现/code
R=C:/Users/26904/anaconda3/envs/repro/python.exe

# 资源试跑（先跑这个，记录输出与耗时再决定全量）：最小模型 x SST-2 x 4-shot x 1 seed x 50 条
PYTHONUTF8=1 $R scripts/run_trial.py

# 单数据集全网格（模型 x shot x 5 seeds，官方 300 条固定测试子集）
PYTHONUTF8=1 $R calib/experiment.py --model gpt2-xl --dataset sst2 --shots 0,1,4,8 --seeds 5 --subsample 300

# 三个数据集全部 + 内容无关输入消融（Table 3）
PYTHONUTF8=1 $R calib/experiment.py --model gpt2,gpt2-medium,gpt2-large,gpt2-xl --dataset sst2,agnews,trec --shots 0,1,4,8 --seeds 5 --subsample 300 --cf_ablation

# 汇总（论文 Table 风格 均值±std）
PYTHONUTF8=1 $R calib/experiment.py --aggregate_only
```

预计耗时（fp32，bs 按 2026-11-15 探针核定的（模型×数据集）显式传参，见下表）：gpt2 约 15 分钟，gpt2-medium 约 40 分钟，gpt2-large 约 1.5 小时，gpt2-xl 约 2 小时；四模型合计一晚可完成。断点安全：已存在的 run 结果自动跳过（`results/raw/` 去重，配置不一致会报错拒绝）。

| bs | sst2 | agnews | trec | 依据（peak reserved，探针见 `../results/probes/`） |
|---|---|---|---|---|
| gpt2 | 16 | 16 | 16 | 4.32 / 5.44 / 2.42 GB，安全 |
| gpt2-medium | 16 | 8 | 16 | 5.92 / 5.46 / 3.76 GB，安全（agnews bs12=7.34GB 淘汰） |
| gpt2-large | 12 | 4 | 12 | 6.47 / 5.89 / 5.35 GB，安全（agnews bs8=9.10GB 淘汰） |
| gpt2-xl | 2 | 2 | 2 | 7.04 / 8.16 / 6.65 GB；高档位超物理显存但 WDDM 溢出兜底无 OOM，bs2 实测最快 |

## 5. 预期输出与逐条结果入口

| 输出 | 路径 | 说明 |
|---|---|---|
| 原始日志（每次运行） | `../results/raw/<数据集>_<模型>_<shot>shot_sub300_seed<k>.json` | 配置、训练样例 ID 与文本、测试 ID、p_cf、两套准确率、耗时 |
| 逐样本结果 | `../results/samples/同名.csv` | sample_id、gold、基线预测、校准预测、各类概率 |
| 汇总表 | `../results/summary.csv` | 每次运行一行（汇总脚本输入） |
| 聚合统计 | `--aggregate_only` 的 stdout（另存 `../results/aggregate.txt`） | 按模型 x 数据集 x shot 的 均值±std |

## 6. 与作者代码的差异声明（规范要求）

- 作者仓库：tonyzhaozh/few-shot-learning，master 分支（2026-11-03 经镜像读取），本地参考副本在 `../作者代码/few-shot-learning/`
- 本工程重实现其 `data_utils.load_dataset`（prompt 前后缀/标签词逐字一致）、`utils.random_sampling`（同种子方案）、`run_classification.get_label_probs`（top-k + 回声补全）、`get_p_content_free`（三输入平均）、`eval_accuracy`（diagonal_W/identity_W）——逻辑逐行对齐
- 差异：(1) 仅实现分类任务三数据集（论文还有 LAMA/抽取任务，超出约定范围）；(2) 仅 GPT-2 本地路线（论文主结果为 GPT-3 API）；(3) 推理用现代 transformers API + torch.no_grad（作者 detach 等价）；(4) 标签缺失概率总是回声补全（作者 `--approx` 为置零近似）；(5) 已知作者 README 声明：其重构后训练集与论文表格所用不一致，趋势应一致
- 其余已知微小差异（2026-11-04 R01 评审逐项验证不影响数值）：(6) 未实现作者 `params_check`（标签词单 token 断言）——已用 GPT-2 BPE 验证 13 个标签词全部单 token；(7) top-k 对数概率用 `log(probs+1e-30)` 防下溢（作者为 `log(probs)`，仅影响 top-k 内下溢到 0 的概率，偏差 ~1e-31 量级）；(8) attention_mask 取自 tokenizer padding（作者按 `ids != 50256` 推断，真实文本含 EOS 时会误判；本地更稳健，语义等价）；(9) 缺失标签表于 2026-11-04 对齐作者 all_found 模式（此前按标签词粒度对双词类重复记录，回声数值等价、仅多算冗余前向）
