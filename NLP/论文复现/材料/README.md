# 中期报告材料包（Calibrate Before Use 复现）

> 打包日期：2026-11-04 ｜ 用途：撰写课程中期进展记录的全部数据与图像
> 论文：Calibrate Before Use（Zhao et al., ICML 2021）｜ 运行环境：conda `repro`，RTX 4060 Laptop 8GB，fp32

## 包内清单

| 内容 | 路径 | 说明 |
|---|---|---|
| 中期进展记录（六字段正文） | `中期进展记录.md` | ③④⑤字段全部数字可溯源到本包 data/ |
| 图1 基线 vs 校准准确率 | `figures/fig1_acc_compare.pdf/.png` | 三数据集 × shots 0/1/4/8，gpt2 seed0，300 条固定测试子集；随机水平虚线（SST-2 50% / AGNews 25% / TREC 16.67%） |
| 图2 校准先验 p_cf 热力矩阵 | `figures/fig2_pcf_heatmap.pdf/.png` | 行=shot、列=类别、色深∝先验概率；AGNews 1-shot Technology 0.81 先验坍缩为关键证据 |
| 图源（可复现） | `figures/*.tex` | 由 `code/scripts/make_midterm_figs.py` 从 raw JSON 自动生成，xelatex 编译 |
| 汇总表 | `data/summary.csv` | 每次运行一行（expr_name/模型/数据集/shot/seed/两套准确率/翻转数/耗时） |
| 原始日志 ×13 | `data/raw/` | 完整配置、训练样例 ID 与文本、测试 ID、p_cf、两套准确率（含 trial 试跑） |
| 逐样本输出 ×12 | `data/samples/` | sample_id、gold、基线/校准预测、各类概率（8 位小数） |
| 运行日志 ×3 | `data/logs/` | P1 试跑 / P2 冒烟 SST-2 / P2b 冒烟 AGNews+TREC 的完整 stdout/stderr |

## 关键数字速查（与记录③一致）

| 数据集 | shots | 基线 | 校准 | 随机水平 |
|---|---|---|---|---|
| SST-2 | 0 / 1 / 4 / 8 | 72.67 / 48.33 / 49.33 / 49.67 | 60.67 / 50.67 / 50.00 / 49.33 | 50% |
| AGNews | 0 / 1 / 4 / 8 | 59.00 / 23.67 / 24.33 / 24.33 | 54.00 / **52.33** / 25.00 / 24.67 | 25% |
| TREC | 0 / 1 / 4 / 8 | 26.00 / 34.00 / 19.00 / 33.33 | 11.67 / 12.67 / 23.33 / **3.33** | 16.67% |

- 机制正例：AGNews 1-shot 先验坍缩到 Technology（p_cf 0.81），校准 +28.7 pp（与论文 Table 4 中 GPT-2 XL 同配置 +22.5 pp 行为一致）
- 边界例：TREC 8-shot 校准坍缩至 3.33%（微小 p_cf 分量被 1/p_cf 放大）；SST-2 0-shot 校准 −12.0 pp（弱先验噪声放大）
- 全部 13 个结果文件经 `code/scripts/check_results.py` 独立复算一致，并经 R01 评审 GPU 全量端到端复现（300/300 逐条一致）

## 数据完整性校验方式

```bash
cd 论文复现/code
PYTHONUTF8=1 C:/Users/26904/anaconda3/envs/repro/python.exe scripts/check_results.py
# 输出"全部通过（13 个结果文件）"即为与包内 data/raw 一致的校验基线
```
