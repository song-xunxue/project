# 论文复现：Calibrate Before Use（组号 G17 / 论文号 P33）

复现 **Calibrate Before Use: Improving Few-Shot Performance of Language Models**（Tony Z. Zhao, Eric Wallace, Shi Feng, Dan Klein, Sameer Singh. ICML 2021, PMLR 139）的少样本上下文校准方法。原文 PDF 见 `zhao21c.pdf`，作者开源代码参考副本见 `作者代码/few-shot-learning/`（Apache 2.0）。

**最终结果一览（全部为本机真实运行，240 run）**：

- 全网格：4 个 GPT-2 规格（124M/355M/774M/1.5B）× 3 数据集（SST-2/AGNews/TREC）× 4 shots（0/1/4/8）× 5 seeds，300 条冻结测试子集，fp32——240/240 run 一次通过，总耗时 1 小时 40 分
- 核心结论①：**校准收益规模依赖**——0-shot 校准在 Medium/Large/XL 上 SST-2（+13~17pp）与 AGNews（+11~23pp）全面正收益，124M 的 GPT-2 反向
- 核心结论②：**TREC 全规模坍缩（超出原文单点报告的新发现）**——TREC 上四模型全部 (模型, shot) 组合校准后显著低于基线
- 核心结论③：**Table 3 消融复现成立**——内容无关输入的选择实质性影响结果（如 XL AGNews 0-shot：空串 0.5733 vs 三输入平均 0.5200）

## 目录结构

| 路径 | 内容 |
|---|---|
| `report.pdf` / `report.tex` | 复现报告（正文 4–6 页，含原文定位、设置差异、结果、消融、案例、结论） |
| `slides.pptx` / `slides.pdf` | 汇报幻灯片（7 页，16:9） |
| `contributions.md` | 成员分工与代码 / AI 使用说明 |
| `code/` | 复现代码（`calib/` 四模块 + `scripts/` + `configs/` + `data/`）；运行入口与差异声明见 `code/README.md` |
| `results/` | 原始日志、汇总表、逐样本输出、案例分析（≥10 例）、消融与探针产物 |
| `工程管理/` | issue 台账、运行台账、决策记录（D01–D05）、评审记录（R01/R01b） |
| `材料/` | 中期材料包（`中期.zip`）、汇总图件（`figures/`）、最终材料包（`最终材料.zip`） |
| `中期进展记录.md` | 中期阶段记录（六字段，经两轮评审定稿） |

## 环境

- conda 环境 `repro`：Python 3.11 + torch 2.14.1+cu126 + transformers 5.22.1 + datasets 5.1.0 + pandas/matplotlib
- 硬件：RTX 4060 Laptop 8GB（单卡，纯推理无训练）
- 安装与模型权重下载（权重约 11GB，**不进提交包**，按规范提供路径与校验）：见 `code/README.md` 第 1、3.3 节

## 快速开始

```bash
cd code
R=C:/Users/26904/anaconda3/envs/repro/python.exe   # 换成自己的 repro 环境 python

# 1) 单配置试跑（gpt2 × SST-2 × 4-shot × 50 条，约 3 秒）
PYTHONUTF8=1 $R scripts/run_trial.py

# 2) 全网格（240 run，按（模型×数据集）核定 bs，约 1.5–2 小时）
bash scripts/run_grid_batch.sh gpt2 16 16 16
bash scripts/run_grid_batch.sh gpt2-medium 16 8 16
bash scripts/run_grid_batch.sh gpt2-large 12 4 12
bash scripts/run_grid_batch.sh gpt2-xl 2 2 2

# 3) 校验 / 汇总 / 消融 / 图
PYTHONUTF8=1 $R scripts/check_results.py                       # 全量独立复算校验
PYTHONUTF8=1 $R calib/experiment.py --aggregate_only           # 48 组均值±std
PYTHONUTF8=1 $R scripts/cf_ablation_offline.py --pairs sst2:1,agnews:0   # Table 3 消融
PYTHONUTF8=1 $R scripts/make_fullfigs.py && cd ../材料/figures && xelatex fig3_fullgrid_acc
```

预计耗时：试跑秒级；单（模型×数据集）20 run 约 1–30 分钟；全网格约 1.5–2 小时（bs 已按显存探针核定，见 `工程管理/decisions.md` D02）。

## 逐条结果入口

| 想看什么 | 去哪里 |
|---|---|
| 每次运行的关键数字（240 行） | `results/summary.csv` |
| 跨 seed 聚合（48 组均值±std） | `results/aggregate.txt` |
| 单次运行的完整配置与训练样例 | `results/raw/<数据集>_<模型>_<shot>shot_sub300_seed<k>.json` |
| 逐样本概率与两种预测 | `results/samples/` 同名 CSV |
| Table 3 消融（四种内容无关输入） | `results/cf_ablation/`（50 记录 + 汇总 CSV） |
| ≥10 个案例分析 | `results/案例分析_全量.md`（24 例） |
| 汇总图 | `材料/figures/fig3_fullgrid_acc.*`、`fig4_table3_ablation.*`（tex/pdf/png） |
| 运行日志 | `results/logs/`（每个（模型×数据集）批次一个日志 + 全量校验日志） |
| 数据来源 / 许可 / SHA256 / 固定子集声明 | `code/data/README.md` |

## 与作者代码的差异声明

本工程重实现作者 `few-shot-learning` 的分类管线并逐行对齐其 prompt 格式与校准逻辑；9 项差异（仅三分类数据集、本地 GPT-2、transformers 5.x API、总是回声补全等）逐条见 `code/README.md` 第 6 节。模型权重版本与 SHA256 见 `code/README.md` 第 3.3 节。

## 复现性说明

- 所有随机过程固定种子（测试子集 seed 0 冻结、训练样例 seed 0–4），同配置可精确复现
- 同配置重跑自动跳过且校验配置一致性（bs/精度/prompt 参数不一致会报错拒绝，防止静默复用）
- 批处理大小按（模型×数据集）显存探针核定；`gpt2-xl` fp32 超出 8GB 物理显存的部分由 Windows WDDM 溢出兜底（bs=2 实测最快，无 OOM 崩溃）
- AI 辅助声明见 `contributions.md`
