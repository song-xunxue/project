# Contributions（组号 G17 / 论文号 P33）

论文：Calibrate Before Use: Improving Few-Shot Performance of Language Models（Zhao et al., ICML 2021, PMLR 139）

> 说明：以下成员分工栏按要求留白，由组内确认后填写；所有运行与核验路径均可从本仓库文件溯源。

## 成员与分工

| 成员 | 分工与实际贡献 | 个人运行 / 核验路径 |
|---|---|---|
| （待填） | | |
| （待填） | | |
| （待填） | | |
| （待填） | | |

## 代码与 AI 使用说明

- **代码**：`code/calib/`（数据加载 / 推理封装 / 校准与评测 / 实验主流程）为本组自行实现，
  与作者开源代码 `tonyzhaozh/few-shot-learning`（master 分支，本地参考副本见 `作者代码/`）逐行对齐
  其 prompt 格式、抽样方案、标签概率提取（top-k + 回声补全）、p_cf 计算与 eval_accuracy 逻辑；
  差异共 9 项，逐条声明见 `code/README.md` 第 6 节（仅分类三数据集、本地 GPT-2 路线、
  现代 transformers API、总是回声补全等）。
- **AI 辅助（如实声明）**：使用 Claude Code 辅助完成工程实现与执行——环境搭建、复现代码初稿、
  批处理与探针脚本、对抗评审（多代理互查修复 6 处缺陷）、全网格 240 run 的执行与汇总、图件生成；
  实验方案（缩规模范围、数据集、种子与子集设定）由本组确定，全部实验在本机 GPU 实际运行，
  每个数字可溯源到 `results/` 下的具体文件；论文理解、结果判读与结论由本组成员完成。
- **运行证据**：`results/logs/`（批次日志）、`results/summary.csv`（240 行）、
  `results/raw/*.json`（含配置与训练样例 ID）、`工程管理/`（issue 台账 / 运行台账 / 决策记录 / 评审记录）。
