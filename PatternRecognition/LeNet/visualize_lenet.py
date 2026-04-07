"""
LeNet 实验可视化脚本

生成四张可视化图表：
    1. confusion_matrix.png         — 10×10 混淆矩阵 + 每类 precision/recall/F1
    2. misclassified_samples.png    — 典型错误样本可视化
    3. feature_maps.png             — 卷积层特征图可视化
    4. class_accuracy.png           — 各类别准确率柱状图

运行方式：
    python visualize_lenet.py
    （需先运行 model_train.py 训练模型生成 best_model.pth）

作者: 李文煜
日期: 2026-04-07
"""

import torch
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from torchvision.datasets import FashionMNIST
from torchvision import transforms
import torch.utils.data as Data

from model import LeNet

CLASS_NAMES = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model_and_data():
    """加载训练好的模型和测试数据集"""
    # 加载模型
    model = LeNet().to(DEVICE)
    model.load_state_dict(torch.load('./best_model.pth', map_location=DEVICE))
    model.eval()

    # 加载测试集
    test_data = FashionMNIST(
        root='./data', train=False,
        transform=transforms.Compose([transforms.Resize(size=28), transforms.ToTensor()]),
        download=True
    )
    test_loader = Data.DataLoader(dataset=test_data, batch_size=64, shuffle=False, num_workers=0)

    # 收集所有预测和真实标签
    all_preds = []
    all_labels = []
    all_images = []

    with torch.no_grad():
        for b_x, b_y in test_loader:
            b_x = b_x.to(DEVICE)
            output = model(b_x)
            pre_lab = torch.argmax(output, dim=1)
            all_preds.extend(pre_lab.cpu().numpy())
            all_labels.extend(b_y.numpy())
            all_images.extend(b_x.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_images = np.array(all_images)

    return model, all_preds, all_labels, all_images


# ======================== 图1：混淆矩阵 ========================

def plot_confusion_matrix(all_preds, all_labels):
    """绘制 10×10 混淆矩阵，附带分类报告"""
    cm = confusion_matrix(all_labels, all_preds)

    fig, ax = plt.subplots(figsize=(10, 9))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
                annot_kws={'size': 9})

    # 在每个单元格添加百分比
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            pct = cm[i, j] / cm[i].sum() * 100 if cm[i].sum() > 0 else 0
            if pct > 0:
                ax.text(j + 0.5, i + 0.78, f'({pct:.1f}%)',
                         ha='center', va='center', fontsize=7, color='gray')

    ax.set_xlabel('预测类别', fontsize=13)
    ax.set_ylabel('真实类别', fontsize=13)
    ax.set_title('LeNet-5 混淆矩阵 (Fashion-MNIST 测试集)', fontsize=14)
    ax.tick_params(axis='x', rotation=45, labelsize=9)
    ax.tick_params(axis='y', rotation=0, labelsize=9)

    plt.tight_layout()
    plt.savefig('./confusion_matrix.png', dpi=300, bbox_inches='tight')
    print(">> 混淆矩阵已保存: ./confusion_matrix.png")
    plt.close()

    # 打印分类报告
    report = classification_report(all_labels, all_preds, target_names=CLASS_NAMES, digits=4)
    print("\n分类报告 (Classification Report):")
    print(report)
    return report


# ======================== 图2：错误样本可视化 ========================

def plot_misclassified(all_preds, all_labels, all_images, max_samples=20):
    """展示典型错误分类样本"""
    # 找到所有错误样本
    wrong_idx = np.where(all_preds != all_labels)[0]

    if len(wrong_idx) == 0:
        print(">> 没有错误样本！")
        return

    # 随机选择最多 max_samples 个
    np.random.seed(42)
    selected = np.random.choice(wrong_idx, min(max_samples, len(wrong_idx)), replace=False)

    cols = 5
    rows = (len(selected) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(15, 3 * rows))

    for i, idx in enumerate(selected):
        ax = axes[i // cols, i % cols] if rows > 1 else axes[i]
        ax.imshow(all_images[idx].squeeze(), cmap='gray')
        true_label = CLASS_NAMES[all_labels[idx]]
        pred_label = CLASS_NAMES[all_preds[idx]]
        ax.set_title(f'真实: {true_label}\n预测: {pred_label}',
                      fontsize=8, color='red')
        ax.axis('off')

    # 隐藏多余的子图
    for i in range(len(selected), rows * cols):
        ax = axes[i // cols, i % cols] if rows > 1 else axes[i]
        ax.axis('off')

    plt.suptitle(f'错误分类样本 (共 {len(wrong_idx)} 个，展示 {len(selected)} 个)', fontsize=14)
    plt.tight_layout()
    plt.savefig('./misclassified_samples.png', dpi=300, bbox_inches='tight')
    print(f">> 错误样本图已保存: ./misclassified_samples.png (共{len(wrong_idx)}个错误)")
    plt.close()


# ======================== 图3：特征图可视化 ========================

def plot_feature_maps(model):
    """可视化第一个卷积层和池化层的特征图"""
    # 获取一张测试图片
    test_data = FashionMNIST(
        root='./data', train=False,
        transform=transforms.Compose([transforms.Resize(size=28), transforms.ToTensor()]),
        download=True
    )
    img, label = test_data[0]
    img = img.unsqueeze(0).to(DEVICE)  # 添加 batch 维度

    # 提取中间层输出
    model.eval()
    with torch.no_grad():
        # C1 卷积 + Sigmoid
        c1_out = model.sig(model.c1(img))
        # S3 池化
        s3_out = model.s3(c1_out)
        # C4 卷积 + Sigmoid
        c4_out = model.sig(model.c4(s3_out))
        # S5 池化
        s5_out = model.s5(c4_out)

    fig, axes = plt.subplots(2, 6, figsize=(16, 6))

    # 第一行：C1 卷积层输出的 6 个特征图
    for i in range(6):
        ax = axes[0, i]
        feature = c1_out[0, i].cpu().numpy()
        ax.imshow(feature, cmap='viridis')
        ax.set_title(f'C1 通道 {i + 1}', fontsize=9)
        ax.axis('off')

    # 第二行：S3 池化层输出的 6 个特征图
    for i in range(6):
        ax = axes[1, i]
        feature = s3_out[0, i].cpu().numpy()
        ax.imshow(feature, cmap='viridis')
        ax.set_title(f'S3 通道 {i + 1}', fontsize=9)
        ax.axis('off')

    plt.suptitle(f'卷积层特征图可视化（输入: {CLASS_NAMES[label]}）', fontsize=13)
    plt.tight_layout()
    plt.savefig('./feature_maps.png', dpi=300, bbox_inches='tight')
    print(">> 特征图已保存: ./feature_maps.png")
    plt.close()


# ======================== 图4：各类别准确率 ========================

def plot_class_accuracy(all_preds, all_labels):
    """各类别准确率柱状图"""
    class_acc = []
    for i in range(10):
        mask = all_labels == i
        if mask.sum() > 0:
            acc = (all_preds[mask] == all_labels[mask]).sum() / mask.sum() * 100
        else:
            acc = 0
        class_acc.append(acc)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.RdYlGn(np.array(class_acc) / 100)
    bars = ax.bar(CLASS_NAMES, class_acc, color=colors, edgecolor='white')

    # 标注数值
    for bar, acc in zip(bars, class_acc):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)

    # 总体准确率参考线
    overall_acc = (all_preds == all_labels).sum() / len(all_labels) * 100
    ax.axhline(y=overall_acc, color='r', linestyle='--', linewidth=1.5,
               label=f'总体准确率: {overall_acc:.2f}%')

    ax.set_xlabel('类别', fontsize=12)
    ax.set_ylabel('准确率 (%)', fontsize=12)
    ax.set_title('LeNet-5 各类别准确率 (Fashion-MNIST 测试集)', fontsize=14)
    ax.set_ylim(0, 105)
    ax.legend(fontsize=11)
    ax.tick_params(axis='x', rotation=30, labelsize=9)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('./class_accuracy.png', dpi=300, bbox_inches='tight')
    print(">> 各类准确率图已保存: ./class_accuracy.png")
    plt.close()


# ======================== 主流程 ========================

if __name__ == '__main__':
    print("=" * 60)
    print("LeNet 实验可视化")
    print("=" * 60)

    model, all_preds, all_labels, all_images = load_model_and_data()
    overall_acc = (all_preds == all_labels).sum() / len(all_labels) * 100
    print(f"测试集准确率: {overall_acc:.2f}% ({(all_preds == all_labels).sum()}/{len(all_labels)})")

    plot_confusion_matrix(all_preds, all_labels)
    plot_misclassified(all_preds, all_labels, all_images)
    plot_feature_maps(model)
    plot_class_accuracy(all_preds, all_labels)

    print("\n=== 所有可视化图表生成完毕 ===")
