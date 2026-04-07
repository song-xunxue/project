"""
数据集下载与预处理脚本

从 UCI 机器学习仓库下载 Wine Quality（红酒品质）数据集，
保存为本地 CSV 文件供后续实验使用。

数据集说明：
    - 来源：UCI Machine Learning Repository (ID: 186)
    - 规模：红/白葡萄酒共约 6,500 样本，12 列（11 特征 + 1 目标）
    - 特征：11 个理化指标（固定酸度、挥发性酸度、柠檬酸等）
    - 目标：quality（品质评分，整数 3~9）
    - 适用任务：分类（二分类/多分类）+ 回归

运行方式：
    python plot.py
    首次运行会从网络下载数据集，后续已存在 CSV 文件则无需重复运行

作者: 李文煜
日期: 2026-04-05

2026-04-07
变更说明：
  1. 补充模块文档字符串和详细中文注释
"""

from ucimlrepo import fetch_ucirepo
import pandas as pd
import os

# 1. 从 UCI 仓库拉取完整数据集（ID=186 对应 Wine Quality）
wine_quality = fetch_ucirepo(id=186)

# 2. 拼接特征和目标变量为完整 DataFrame
X = wine_quality.data.features  # 11个理化特征（fixed_acidity ~ alcohol）
y = wine_quality.data.targets   # 质量评分（quality，整数 3~9）
df_full = pd.concat([X, y], axis=1)

# 3. 定义本地保存路径
save_dir = "./data"
save_path = os.path.join(save_dir, "wine_quality_full.csv")

# 4. 自动创建目录（若不存在）
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 5. 保存为 CSV 文件（UTF-8 编码，不写入行索引）
df_full.to_csv(save_path, index=False, encoding="utf-8")

# 验证保存结果：打印路径、形状、前5行和标签分布
print(f"数据集已成功保存到：{save_path}")
print(f"数据集形状（行×列）：{df_full.shape}")
print("\n数据集前5行：")
print(df_full.head())
print("\n质量评分分布：")
print(df_full["quality"].value_counts().sort_index())
