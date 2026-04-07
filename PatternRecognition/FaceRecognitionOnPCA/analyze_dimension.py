"""
PCA 降维维度对比分析脚本

在不同 K 值（主成分数量）下，分别运行三种分类方法，
对比维度对识别准确率的影响，并输出：
    1. 控制台表格：各 K 值 × 各分类方法的准确率
    2. 日志文件：dimension_analysis.log
    3. 曲线图：dimension_accuracy_curve.png

分析的 K 值列表：[2, 3, 5, 10, 20, 30, 40, 50, 80, 100, 150]
分类方法：欧氏距离 1-NN、余弦相似度 1-NN、PCA + SVM

运行方式：
    python analyze_dimension.py
    （需先运行 plot.py 下载数据集，无需先训练模型，本脚本会自动训练各 K 值的 PCA）

作者: 李文煜
日期: 2026-04-07
"""

import os
import sys
import datetime
import cv2
import torch
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# 配置中文字体，防止图表中的中文显示为方块/乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from sklearn.svm import SVC
from model.model import PCAFaceModel


# ============== 数据加载 ==============

def train_data_process(test_img_idx):
    """
    构建训练集（与 model_train.py 相同逻辑）

    参数:
        test_img_idx (list[int]): 排除的测试集图像编号

    返回:
        train_x (torch.Tensor): 训练集图像，形状 (N, D)
        train_y (torch.Tensor): 训练集标签，形状 (N,)
        img_h (int): 图像高度
        img_w (int): 图像宽度
    """
    train_x, train_y = [], []
    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        for j in range(1, 11):
            if j in test_img_idx:
                continue
            img_path = os.path.join(dir_path, f'{j}.pgm')
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            train_x.append(img.reshape(-1))
            train_y.append(i)
    train_x = torch.tensor(np.array(train_x), dtype=torch.float32)
    train_y = torch.tensor(np.array(train_y), dtype=torch.long)
    img_h, img_w = img.shape
    return train_x, train_y, img_h, img_w


def test_data_process(test_img_idx):
    """
    构建测试集（与 test_model.py 相同逻辑）

    参数:
        test_img_idx (list[int]): 测试集图像编号

    返回:
        test_x (torch.Tensor): 测试集图像，形状 (M, D)
        test_y (torch.Tensor): 测试集标签，形状 (M,)
    """
    test_x, test_y = [], []
    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        for j in range(1, 11):
            if j not in test_img_idx:
                continue
            img_path = os.path.join(dir_path, f'{j}.pgm')
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            test_x.append(img.reshape(-1))
            test_y.append(i)
    test_x = torch.tensor(np.array(test_x), dtype=torch.float32)
    test_y = torch.tensor(np.array(test_y), dtype=torch.long)
    return test_x, test_y


# ============== 三种分类方法 ==============

def classify_euclidean(test_features, train_features, train_labels, test_labels):
    """
    欧氏距离 1-NN 分类

    参数:
        test_features (torch.Tensor): 测试集 PCA 特征，形状 (M, K)
        train_features (torch.Tensor): 训练集 PCA 特征，形状 (N, K)
        train_labels (torch.Tensor): 训练集标签，形状 (N,)
        test_labels (torch.Tensor): 测试集真实标签，形状 (M,)

    返回:
        float: 准确率（0~1）
    """
    correct = 0
    total = test_features.size(0)
    for i in range(total):
        # 计算当前测试样本与所有训练样本的欧氏距离
        distances = torch.norm(train_features - test_features[i], dim=1)
        # 取距离最小的训练样本标签作为预测
        pred = train_labels[torch.argmin(distances)]
        if pred == test_labels[i]:
            correct += 1
    return correct / total


def classify_cosine(test_features, train_features, train_labels, test_labels):
    """
    余弦相似度 1-NN 分类

    参数:
        test_features (torch.Tensor): 测试集 PCA 特征，形状 (M, K)
        train_features (torch.Tensor): 训练集 PCA 特征，形状 (N, K)
        train_labels (torch.Tensor): 训练集标签，形状 (N,)
        test_labels (torch.Tensor): 测试集真实标签，形状 (M,)

    返回:
        float: 准确率（0~1）
    """
    correct = 0
    total = test_features.size(0)
    for i in range(total):
        # 计算余弦相似度（越大越相似）
        sims = torch.nn.functional.cosine_similarity(
            train_features, test_features[i].unsqueeze(0), dim=1
        )
        # 取相似度最大的训练样本标签作为预测
        pred = train_labels[torch.argmax(sims)]
        if pred == test_labels[i]:
            correct += 1
    return correct / total


def classify_svm(test_features, train_features, train_labels, test_labels):
    """
    PCA + SVM 分类（线性核）

    参数:
        test_features (torch.Tensor): 测试集 PCA 特征
        train_features (torch.Tensor): 训练集 PCA 特征
        train_labels (torch.Tensor): 训练集标签
        test_labels (torch.Tensor): 测试集真实标签

    返回:
        float: 准确率（0~1）
    """
    # sklearn 要求 NumPy 输入
    X_train = train_features.cpu().numpy()
    Y_train = train_labels.cpu().numpy()
    X_test = test_features.cpu().numpy()
    Y_test = test_labels.cpu().numpy()

    # 训练 SVM 线性分类器
    svm = SVC(kernel='linear', C=1.0)
    svm.fit(X_train, Y_train)
    predictions = svm.predict(X_test)

    correct = sum(1 for p, r in zip(predictions, Y_test) if p == r)
    return correct / len(Y_test)


# ============== 双向日志 ==============

class Logger(object):
    """
    双向输出 Logger：同时将内容写入控制台和日志文件

    参数:
        filename (str): 日志文件路径
    """

    def __init__(self, filename="dimension_analysis.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        pass


# ============== 主流程 ==============

if __name__ == '__main__':
    # 启动日志记录
    sys.stdout = Logger("dimension_analysis.log")

    print("=" * 60)
    print("PCA 降维维度对比分析")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 加载数据
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    TEST_IMAGE_INDEX = [9, 10]

    train_x, train_y, _, _ = train_data_process(TEST_IMAGE_INDEX)
    test_x, test_y = test_data_process(TEST_IMAGE_INDEX)

    train_x = train_x.to(device)
    train_y = train_y.to(device)
    test_x = test_x.to(device)
    test_y = test_y.to(device)

    print(f"计算设备: {device}")
    print(f"训练集: {train_x.shape[0]} 张, 测试集: {test_x.shape[0]} 张")
    print(f"原始特征维度: {train_x.shape[1]}\n")

    # 待测试的 K 值（从低维到高维，覆盖完整范围）
    k_values = [2, 3, 5, 10, 20, 30, 40, 50, 80, 100, 150]

    # 结果存储
    results = {
        '欧氏距离 1-NN': [],
        '余弦相似度 1-NN': [],
        'PCA + SVM': []
    }

    # 表格头部
    print(f"{'K值':>6} | {'欧氏距离':>10} | {'余弦相似度':>10} | {'PCA+SVM':>10}")
    print("-" * 52)

    # 逐个 K 值训练 PCA 并测试三种分类方法
    for k in k_values:
        model = PCAFaceModel(k_components=k)
        model.fit(train_x)

        train_features = model.transform(train_x)
        test_features = model.transform(test_x)

        acc_euc = classify_euclidean(test_features, train_features, train_y, test_y)
        acc_cos = classify_cosine(test_features, train_features, train_y, test_y)
        acc_svm = classify_svm(test_features, train_features, train_y, test_y)

        results['欧氏距离 1-NN'].append(acc_euc)
        results['余弦相似度 1-NN'].append(acc_cos)
        results['PCA + SVM'].append(acc_svm)

        print(f"{k:>6} | {acc_euc * 100:>9.2f}% | {acc_cos * 100:>9.2f}% | {acc_svm * 100:>9.2f}%")

    # ============== 绘制准确率曲线 ==============
    plt.figure(figsize=(12, 7))

    markers = {'欧氏距离 1-NN': 'o-', '余弦相似度 1-NN': 's--', 'PCA + SVM': '^-.'}
    for method, accuracies in results.items():
        acc_percent = [a * 100 for a in accuracies]
        plt.plot(k_values, acc_percent, markers[method], label=method, linewidth=2, markersize=8)

    plt.xlabel('PCA 保留的主成分数量 K', fontsize=14)
    plt.ylabel('识别准确率 (%)', fontsize=14)
    plt.title('PCA 降维维度（K值）对三种分类方法准确率的影响', fontsize=16)
    plt.xticks(k_values)
    plt.ylim(0, 105)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12, loc='lower right')
    plt.tight_layout()
    plt.savefig('./dimension_accuracy_curve.png', dpi=300, bbox_inches='tight')
    print("\n准确率曲线已保存: ./dimension_accuracy_curve.png")
    plt.show()

    print("\n=== 维度对比分析完成 ===")
