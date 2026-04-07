"""
AdaBoost 实验可视化脚本

生成四张可视化图表：
    1. data_distribution.png     — 数据分布概览（质量分布、二分类标签、特征箱线图、相关性热力图）
    2. confusion_matrix_multi.png — SAMME 多分类混淆矩阵
    3. binary_metrics.png        — 二分类 ROC 曲线 + Precision-Recall 曲线
    4. feature_importance.png    — 基于累加 alpha 权重的特征重要性

运行方式：
    python visualize_adaboost.py

作者: 李文煜
日期: 2026-04-07
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# 配置中文字体，防止图表中的中文显示为方块/乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_curve, auc,
    precision_recall_curve, average_precision_score
)

from model import AdaBoostBinary, AdaBoostMulti
from test_model_binary import data_process_binary
from test_model_multi import data_process_multi

CSV_PATH = "./data/wine_quality_full.csv"
FEATURE_NAMES = [
    'fixed_acidity', 'volatile_acidity', 'citric_acid',
    'residual_sugar', 'chlorides', 'free_sulfur_dioxide',
    'total_sulfur_dioxide', 'density', 'pH', 'sulphates', 'alcohol'
]


def load_data():
    """加载数据，返回二分类和多分类的训练/测试集及原始 DataFrame"""
    df = pd.read_csv(CSV_PATH)
    X_train_bin, X_test_bin, y_train_bin, y_test_bin = data_process_binary(CSV_PATH)
    X_train_mul, X_test_mul, y_train_mul, y_test_mul = data_process_multi(CSV_PATH)
    return (df,
            X_train_bin, X_test_bin, y_train_bin, y_test_bin,
            X_train_mul, X_test_mul, y_train_mul, y_test_mul)


# ======================== 图1：数据分布 ========================

def plot_data_distribution(df):
    """数据分布概览（2×2 子图）"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # 左上：质量评分分布
    quality_counts = df['quality'].value_counts().sort_index()
    bars = axes[0, 0].bar(quality_counts.index, quality_counts.values,
                           color='#4C72B0', edgecolor='white')
    for bar, count in zip(bars, quality_counts.values):
        pct = count / len(df) * 100
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                         f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9)
    axes[0, 0].set_title('红酒质量评分分布', fontsize=13)
    axes[0, 0].set_xlabel('质量评分')
    axes[0, 0].set_ylabel('样本数')

    # 右上：二分类标签分布
    y_binary = np.where(df['quality'].values >= 6, '好酒(>=6)', '差酒(<6)')
    bin_counts = pd.Series(y_binary).value_counts()
    colors = ['#DD8452', '#55A868']
    bars2 = axes[0, 1].bar(bin_counts.index, bin_counts.values,
                            color=colors, edgecolor='white')
    for bar, count in zip(bars2, bin_counts.values):
        pct = count / len(df) * 100
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                         f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10)
    axes[0, 1].set_title('二分类标签分布', fontsize=13)
    axes[0, 1].set_ylabel('样本数')

    # 左下：特征箱线图
    features_df = df.drop(columns=['quality'])
    # 标准化以便在同一尺度显示
    features_norm = (features_df - features_df.mean()) / features_df.std()
    bp = axes[1, 0].boxplot(features_norm.values, labels=range(1, 12),
                             patch_artist=True, showfliers=False)
    for patch in bp['boxes']:
        patch.set_facecolor('#C44E52')
        patch.set_alpha(0.6)
    axes[1, 0].set_title('11个特征分布箱线图（标准化后）', fontsize=13)
    axes[1, 0].set_xlabel('特征编号')
    axes[1, 0].set_ylabel('标准化值')
    axes[1, 0].set_xticklabels(range(1, 12), fontsize=8)

    # 右下：相关性热力图
    corr = df.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, ax=axes[1, 1], annot_kws={'size': 7},
                xticklabels=corr.columns, yticklabels=corr.columns)
    axes[1, 1].set_title('特征相关性热力图', fontsize=13)
    axes[1, 1].tick_params(axis='x', rotation=45, labelsize=7)
    axes[1, 1].tick_params(axis='y', rotation=0, labelsize=7)

    plt.tight_layout()
    plt.savefig('./data_distribution.png', dpi=300, bbox_inches='tight')
    print(">> 数据分布图已保存: ./data_distribution.png")
    plt.close()


# ======================== 图2：混淆矩阵 ========================

def plot_confusion_matrix(X_train, X_test, y_train, y_test):
    """SAMME 多分类混淆矩阵"""
    model = AdaBoostMulti(n_clf=50)
    print(">> 正在训练多分类模型（混淆矩阵）...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    cm = confusion_matrix(y_test, y_pred)
    classes = sorted(np.unique(np.concatenate([y_test, y_pred])))

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=classes, yticklabels=classes,
                annot_kws={'size': 12})

    # 在每个单元格添加百分比标注
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            pct = cm[i, j] / cm[i].sum() * 100 if cm[i].sum() > 0 else 0
            ax.text(j + 0.5, i + 0.75, f'({pct:.1f}%)',
                     ha='center', va='center', fontsize=8, color='gray')

    ax.set_xlabel('预测类别', fontsize=13)
    ax.set_ylabel('真实类别', fontsize=13)
    ax.set_title('AdaBoost SAMME 多分类混淆矩阵 (Wine Quality)', fontsize=14)

    plt.tight_layout()
    plt.savefig('./confusion_matrix_multi.png', dpi=300, bbox_inches='tight')
    print(">> 混淆矩阵已保存: ./confusion_matrix_multi.png")
    plt.close()


# ======================== 图3：二分类详细指标 ========================

def plot_binary_metrics(X_train, X_test, y_train, y_test):
    """ROC 曲线 + Precision-Recall 曲线"""
    model = AdaBoostBinary(n_clf=30)
    print(">> 正在训练二分类模型（ROC/PR）...")
    model.fit(X_train, y_train)

    # 计算连续分数（不加 sign），用于 ROC/PR 曲线
    clf_preds = [clf.alpha * clf.predict(X_test) for clf in model.clfs]
    y_scores = np.sum(clf_preds, axis=0)

    # 将标签从 {-1, 1} 映射到 {0, 1}，适配 sklearn 指标
    y_test_binary = (y_test == 1).astype(int)
    y_scores_pos = y_scores  # 分数越大越倾向正类（1）

    # ROC 曲线
    fpr, tpr, _ = roc_curve(y_test_binary, y_scores_pos)
    roc_auc = auc(fpr, tpr)

    # Precision-Recall 曲线
    precision, recall, _ = precision_recall_curve(y_test_binary, y_scores_pos)
    ap = average_precision_score(y_test_binary, y_scores_pos)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 左：ROC
    axes[0].plot(fpr, tpr, 'b-', linewidth=2, label=f'AUC = {roc_auc:.4f}')
    axes[0].plot([0, 1], [0, 1], 'r--', linewidth=1, label='随机基线')
    axes[0].set_xlabel('假正率 (FPR)', fontsize=12)
    axes[0].set_ylabel('真正率 (TPR)', fontsize=12)
    axes[0].set_title('ROC 曲线 — AdaBoost 二分类', fontsize=14)
    axes[0].legend(fontsize=12)
    axes[0].grid(True, alpha=0.3)

    # 右：PR
    axes[1].plot(recall, precision, 'g-', linewidth=2, label=f'AP = {ap:.4f}')
    axes[1].set_xlabel('召回率 (Recall)', fontsize=12)
    axes[1].set_ylabel('精确率 (Precision)', fontsize=12)
    axes[1].set_title('Precision-Recall 曲线 — AdaBoost 二分类', fontsize=14)
    axes[1].legend(fontsize=12)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('./binary_metrics.png', dpi=300, bbox_inches='tight')
    print(">> 二分类指标图已保存: ./binary_metrics.png")
    plt.close()


# ======================== 图4：特征重要性 ========================

def plot_feature_importance(X_train, y_train):
    """基于累加 alpha 权重的特征重要性"""
    model = AdaBoostBinary(n_clf=30)
    print(">> 正在训练二分类模型（特征重要性）...")
    model.fit(X_train, y_train)

    # 累加每个弱分类器的 alpha 权重到对应特征
    importance = np.zeros(len(FEATURE_NAMES))
    for clf in model.clfs:
        importance[clf.feature_idx] += clf.alpha

    # 按重要性排序
    sorted_idx = np.argsort(importance)
    sorted_names = [FEATURE_NAMES[i] for i in sorted_idx]
    sorted_values = importance[sorted_idx]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.RdYlGn(sorted_values / sorted_values.max())
    ax.barh(sorted_names, sorted_values, color=colors, edgecolor='white')
    ax.set_xlabel('累加 Alpha 权重', fontsize=12)
    ax.set_title('AdaBoost 二分类 — 特征重要性（累加 Alpha 权重）', fontsize=14)

    # 标注数值
    for i, (val, name) in enumerate(zip(sorted_values, sorted_names)):
        ax.text(val + 0.05, i, f'{val:.2f}', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('./feature_importance.png', dpi=300, bbox_inches='tight')
    print(">> 特征重要性图已保存: ./feature_importance.png")
    plt.close()


# ======================== 主流程 ========================

if __name__ == '__main__':
    print("=" * 60)
    print("AdaBoost 实验可视化")
    print("=" * 60)

    if not os.path.exists(CSV_PATH):
        print(f"错误：找不到数据集 {CSV_PATH}，请先运行 plot.py")
        exit(1)

    df, X_train_bin, X_test_bin, y_train_bin, y_test_bin, \
        X_train_mul, X_test_mul, y_train_mul, y_test_mul = load_data()

    plot_data_distribution(df)
    plot_confusion_matrix(X_train_mul, X_test_mul, y_train_mul, y_test_mul)
    plot_binary_metrics(X_train_bin, X_test_bin, y_train_bin, y_test_bin)
    plot_feature_importance(X_train_bin, y_train_bin)

    print("\n=== 所有可视化图表生成完毕 ===")
