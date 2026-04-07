"""
AdaBoost 二分类测试脚本

将 Wine Quality 数据集转为二分类任务：
    - quality >= 6 → +1（好酒）
    - quality < 6  → -1（差酒）

使用自实现的 AdaBoostBinary 模型进行训练和测试，
输出逐样本预测结果和最终准确率。

运行方式：
    python test_model_binary.py
    （需先运行 plot.py 下载数据集）

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 补充模块文档字符串和详细中文注释
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from model import AdaBoostBinary


def data_process_binary(csv_path):
    """
    加载并预处理二分类数据

    读取 Wine Quality CSV 文件，将品质评分二值化：
        quality >= 6 → +1（好酒）
        quality < 6  → -1（差酒）
    按 8:2 比例划分训练集和测试集。

    参数:
        csv_path (str): 数据集 CSV 文件路径

    返回:
        X_train (np.ndarray): 训练集特征，形状 (n_train, 11)
        X_test (np.ndarray): 测试集特征，形状 (n_test, 11)
        y_train (np.ndarray): 训练集标签，取值 {-1, +1}
        y_test (np.ndarray): 测试集标签，取值 {-1, +1}
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到数据集 {csv_path}，请先运行 plot.py 获取数据")

    df = pd.read_csv(csv_path)
    X = df.drop(columns=['quality']).values
    y = df['quality'].values

    # 二分类标签：quality>=6 记为 1（好酒），<6 记为 -1（差酒）
    y_binary = np.where(y >= 6, 1, -1)

    # 按 8:2 划分训练集和测试集，固定随机种子保证可复现
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_binary, test_size=0.2, random_state=42
    )
    return X_train, X_test, y_train, y_test


def test_model_binary_process(X_train, X_test, y_train, y_test):
    """
    训练并测试 AdaBoost 二分类模型

    使用 30 个弱分类器（DecisionStump）训练模型，
    输出前 20 个测试样本的预测结果对比和整体准确率。

    参数:
        X_train (np.ndarray): 训练集特征
        X_test (np.ndarray): 测试集特征
        y_train (np.ndarray): 训练集标签
        y_test (np.ndarray): 测试集真实标签
    """
    print("=" * 40)
    print("模型开始测试 [基础AdaBoost 二分类] ...")
    print("=" * 40)

    # 初始化模型：设置 30 个弱分类器
    model = AdaBoostBinary(n_clf=30)
    print(">> 正在训练二分类模型，正在查找切分点，请稍候...")
    model.fit(X_train, y_train)
    print(">> 训练完成！开始预测测试集...")

    # 进行预测
    predictions = model.predict(X_test)

    # 计算准确率
    test_num = len(y_test)
    test_corrects = np.sum(predictions == y_test)
    test_acc = test_corrects / test_num

    # 打印前 20 个预测结果比对（✅ 正确 / ❌ 错误）
    for i in range(min(20, test_num)):
        status = "✅" if predictions[i] == y_test[i] else "❌"
        print(f"{status} 样本 {i + 1:02d} | 预测: {int(predictions[i]):2d} ---- 真实: {int(y_test[i]):2d}")

    print("...")
    print("=" * 40)
    print(f" [AdaBoost 二分类]模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 40)


if __name__ == "__main__":
    csv_path = "./data/wine_quality_full.csv"
    X_train, X_test, y_train, y_test = data_process_binary(csv_path)
    test_model_binary_process(X_train, X_test, y_train, y_test)
