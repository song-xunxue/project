"""
PCA降维可视化脚本 — 2D / 3D 散点图

将 ORL 人脸数据集通过 PCA 分别降到 2 维和 3 维，绘制散点图。
不同人的样本用不同颜色标记，用于直观展示 PCA 的聚类效果。

输出文件：
    pca_2d_visualization.png — 二维散点图
    pca_3d_visualization.png — 三维散点图

运行方式：
    python visualize_pca.py
    （需先运行 model_train.py 下载数据）

作者: 李文煜
日期: 2026-04-07
"""

import os
import cv2
import torch
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# 配置中文字体，防止图表中的中文显示为方块/乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from model.model import PCAFaceModel


def load_all_data():
    """
    加载 ORL 数据集的全部图像（不区分训练/测试）

    返回:
        all_x (torch.Tensor): 全部图像，形状 (400, 10304)
        all_y (torch.Tensor): 全部标签，形状 (400,)
        img_h (int): 图像高度
        img_w (int): 图像宽度
    """
    all_x, all_y = [], []

    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        for j in range(1, 11):
            img_path = os.path.join(dir_path, f'{j}.pgm')
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            all_x.append(img.reshape(-1))
            all_y.append(i)

    all_x = torch.tensor(np.array(all_x), dtype=torch.float32)
    all_y = torch.tensor(np.array(all_y), dtype=torch.long)
    img_h, img_w = img.shape
    return all_x, all_y, img_h, img_w


def visualize_2d(model, all_x, all_y):
    """
    绘制 PCA 降到 2 维后的散点图

    每个类别（人）用不同颜色标记，用于观察不同人在 2D 空间中的分布。

    参数:
        model (PCAFaceModel): 已训练的 PCA 模型（K=2）
        all_x (torch.Tensor): 全部图像数据
        all_y (torch.Tensor): 全部标签
    """
    # 降维到 2D
    features_2d = model.transform(all_x).numpy()
    labels = all_y.numpy()

    plt.figure(figsize=(14, 10))

    # 为 40 个人生成不同的颜色
    cmap = plt.cm.get_cmap('tab20', 20)
    colors = [cmap(i % 20) if i <= 20 else plt.cm.get_cmap('tab20b')(i - 20) for i in range(1, 41)]

    # 逐类绘制（每个类别一个散点，便于图例显示）
    for person_id in range(1, 41):
        mask = labels == person_id
        plt.scatter(
            features_2d[mask, 0], features_2d[mask, 1],
            c=[colors[person_id - 1]],
            label=f's{person_id:02d}',
            s=40, alpha=0.8, edgecolors='k', linewidths=0.3
        )

    plt.title('PCA 降到 2 维 — ORL 人脸数据集聚类效果', fontsize=16)
    plt.xlabel('第一主成分 (PC1)', fontsize=13)
    plt.ylabel('第二主成分 (PC2)', fontsize=13)
    plt.grid(True, alpha=0.3)

    # 图例分两列显示，放在右侧
    plt.legend(
        bbox_to_anchor=(1.02, 1), loc='upper left',
        ncol=2, fontsize=7, framealpha=0.8
    )

    plt.tight_layout()
    plt.savefig('./pca_2d_visualization.png', dpi=300, bbox_inches='tight')
    print("2D 可视化已保存: ./pca_2d_visualization.png")
    plt.show()


def visualize_3d(model, all_x, all_y):
    """
    绘制 PCA 降到 3 维后的散点图

    交互式 3D 散点图，可用鼠标旋转查看不同角度的聚类情况。

    参数:
        model (PCAFaceModel): 已训练的 PCA 模型（K=3）
        all_x (torch.Tensor): 全部图像数据
        all_y (torch.Tensor): 全部标签
    """
    # 降维到 3D
    features_3d = model.transform(all_x).numpy()
    labels = all_y.numpy()

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    cmap = plt.cm.get_cmap('tab20', 20)
    colors = [cmap(i % 20) if i <= 20 else plt.cm.get_cmap('tab20b')(i - 20) for i in range(1, 41)]

    for person_id in range(1, 41):
        mask = labels == person_id
        ax.scatter(
            features_3d[mask, 0], features_3d[mask, 1], features_3d[mask, 2],
            c=[colors[person_id - 1]],
            label=f's{person_id:02d}',
            s=40, alpha=0.8, edgecolors='k', linewidths=0.3
        )

    ax.set_title('PCA 降到 3 维 — ORL 人脸数据集聚类效果', fontsize=16)
    ax.set_xlabel('第一主成分 (PC1)', fontsize=11)
    ax.set_ylabel('第二主成分 (PC2)', fontsize=11)
    ax.set_zlabel('第三主成分 (PC3)', fontsize=11)

    ax.legend(
        bbox_to_anchor=(1.05, 1), loc='upper left',
        ncol=2, fontsize=7, framealpha=0.8
    )

    plt.tight_layout()
    plt.savefig('./pca_3d_visualization.png', dpi=300, bbox_inches='tight')
    print("3D 可视化已保存: ./pca_3d_visualization.png")
    plt.show()


if __name__ == '__main__':
    # 加载全部 400 张人脸图像
    all_x, all_y, img_h, img_w = load_all_data()
    print(f"数据加载完成：{all_x.shape[0]} 张图片, 展平维度: {all_x.shape[1]}")

    # === 2D 可视化 ===
    print("\n--- PCA 降到 2 维 ---")
    model_2d = PCAFaceModel(k_components=2)
    model_2d.fit(all_x)
    visualize_2d(model_2d, all_x, all_y)

    # === 3D 可视化 ===
    print("\n--- PCA 降到 3 维 ---")
    model_3d = PCAFaceModel(k_components=3)
    model_3d.fit(all_x)
    visualize_3d(model_3d, all_x, all_y)
