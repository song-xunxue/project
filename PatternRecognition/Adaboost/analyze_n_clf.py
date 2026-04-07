"""
AdaBoost 弱分类器数量对比分析脚本

在不同弱分类器数量下，分别运行四种方法：
    1. 自实现 AdaBoost 二分类 (DecisionStump)
    2. sklearn AdaBoost 二分类基线
    3. 自实现 AdaBoost 多分类 (SAMME)
    4. sklearn AdaBoost 多分类基线 (SAMME)

输出：
    1. 控制台 + 日志文件：n_clf_analysis.log
    2. 准确率曲线图：n_clf_accuracy_curve.png

运行方式：
    python analyze_n_clf.py

作者: 李文煜
日期: 2026-04-07
"""

import sys
import os
import datetime
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

from model import AdaBoostBinary, AdaBoostMulti
from test_model_binary import data_process_binary
from test_model_multi import data_process_multi


# ======================== 双向日志 ========================

class Logger(object):
    """双向输出 Logger：同时将内容写入控制台和日志文件"""

    def __init__(self, filename="n_clf_analysis.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        pass


# ======================== 评估函数 ========================

def evaluate_custom_binary(n_clf, X_train, X_test, y_train, y_test):
    """自实现二分类"""
    model = AdaBoostBinary(n_clf=n_clf)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    return np.sum(predictions == y_test) / len(y_test)


def evaluate_sklearn_binary(n_clf, X_train, X_test, y_train, y_test):
    """sklearn 二分类基线"""
    model = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=1),
        n_estimators=n_clf,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model.score(X_test, y_test)


def evaluate_custom_multi(n_clf, X_train, X_test, y_train, y_test):
    """自实现 SAMME 多分类"""
    model = AdaBoostMulti(n_clf=n_clf)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    return np.sum(predictions == y_test) / len(y_test)


def evaluate_sklearn_multi(n_clf, X_train, X_test, y_train, y_test):
    """sklearn SAMME 多分类基线"""
    model = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=1),
        n_estimators=n_clf,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model.score(X_test, y_test)


# ======================== 主流程 ========================

if __name__ == '__main__':
    # 启动日志记录
    sys.stdout = Logger("n_clf_analysis.log")

    print("=" * 80)
    print("AdaBoost 弱分类器数量对比分析")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    csv_path = "./data/wine_quality_full.csv"
    if not os.path.exists(csv_path):
        print(f"错误：找不到数据集 {csv_path}，请先运行 plot.py")
        exit(1)

    # 加载数据
    X_train_bin, X_test_bin, y_train_bin, y_test_bin = data_process_binary(csv_path)
    X_train_mul, X_test_mul, y_train_mul, y_test_mul = data_process_multi(csv_path)

    print(f"数据集: Wine Quality ({len(X_train_bin) + len(X_test_bin)} samples, {X_train_bin.shape[1]} features)")
    print(f"训练集: {len(X_train_bin)} samples, 测试集: {len(X_test_bin)} samples")
    print(f"二分类标签: quality>=6 -> 1, <6 -> -1")
    print(f"多分类标签: quality {sorted(np.unique(y_train_mul))}")
    print()

    # 待测试的弱分类器数量
    n_clf_values = [1, 3, 5, 10, 15, 20, 30, 50, 80, 100, 150]

    # 结果存储
    results = {
        '自实现二分类': [],
        'sklearn二分类': [],
        '自实现SAMME': [],
        'sklearn SAMME': []
    }

    # 表格头部
    print(f"{'n_clf':>6} | {'自实现二分类':>12} | {'sklearn二分类':>12} | {'自实现SAMME':>12} | {'sklearn SAMME':>12}")
    print("-" * 72)

    # 逐个 n_clf 值测试
    for n_clf in n_clf_values:
        print(f">> 正在测试 n_clf = {n_clf} ...", end=" ")

        acc_cb = evaluate_custom_binary(n_clf, X_train_bin, X_test_bin, y_train_bin, y_test_bin)
        acc_sb = evaluate_sklearn_binary(n_clf, X_train_bin, X_test_bin, y_train_bin, y_test_bin)
        acc_cm = evaluate_custom_multi(n_clf, X_train_mul, X_test_mul, y_train_mul, y_test_mul)
        acc_sm = evaluate_sklearn_multi(n_clf, X_train_mul, X_test_mul, y_train_mul, y_test_mul)

        results['自实现二分类'].append(acc_cb)
        results['sklearn二分类'].append(acc_sb)
        results['自实现SAMME'].append(acc_cm)
        results['sklearn SAMME'].append(acc_sm)

        print(f"{acc_cb * 100:.2f}% | {acc_sb * 100:.2f}% | {acc_cm * 100:.2f}% | {acc_sm * 100:.2f}%")
        print(f"{n_clf:>6} | {acc_cb * 100:>11.2f}% | {acc_sb * 100:>11.2f}% | {acc_cm * 100:>11.2f}% | {acc_sm * 100:>11.2f}%")

    # ======================== 绘制准确率曲线 ========================

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # 左：二分类
    axes[0].plot(n_clf_values, [a * 100 for a in results['自实现二分类']],
                  'o-', label='自实现 AdaBoost', linewidth=2, markersize=7)
    axes[0].plot(n_clf_values, [a * 100 for a in results['sklearn二分类']],
                  's--', label='sklearn 基线', linewidth=2, markersize=7)
    axes[0].set_xlabel('弱分类器数量', fontsize=13)
    axes[0].set_ylabel('准确率 (%)', fontsize=13)
    axes[0].set_title('二分类：弱分类器数量对准确率的影响', fontsize=14)
    axes[0].set_xticks(n_clf_values)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=11)

    # 右：多分类
    axes[1].plot(n_clf_values, [a * 100 for a in results['自实现SAMME']],
                  'o-', label='自实现 SAMME', linewidth=2, markersize=7)
    axes[1].plot(n_clf_values, [a * 100 for a in results['sklearn SAMME']],
                  's--', label='sklearn SAMME 基线', linewidth=2, markersize=7)
    axes[1].set_xlabel('弱分类器数量', fontsize=13)
    axes[1].set_ylabel('准确率 (%)', fontsize=13)
    axes[1].set_title('多分类：弱分类器数量对准确率的影响', fontsize=14)
    axes[1].set_xticks(n_clf_values)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=11)

    plt.tight_layout()
    plt.savefig('./n_clf_accuracy_curve.png', dpi=300, bbox_inches='tight')
    print(f"\n准确率曲线已保存: ./n_clf_accuracy_curve.png")

    print("\n=== 弱分类器数量对比分析完成 ===")
