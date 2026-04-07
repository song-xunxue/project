"""
PCA人脸识别模型训练脚本

本脚本完成以下工作：
    1. 从 ORL 人脸数据集中读取训练集图像（排除指定的测试集图像）
    2. 训练 PCA 模型，提取特征脸（Eigenfaces）
    3. 将模型参数和训练集低维特征保存到 pca_model.pth
    4. 可视化平均脸和前 9 个特征脸，保存为 eigenfaces_show.png

运行方式：
    python model_train.py

注意：运行前需先执行 plot.py 下载数据集

作者: 李文煜
日期: 2026-03-12
"""

import os
import cv2
import torch
import numpy as np
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from model.model import PCAFaceModel


def train_data_process(test_img_idx):
    """
    读取 ORL 人脸数据集，构建训练集

    遍历 s1~s40 共 40 个人的文件夹，读取每人 10 张 PGM 灰度图像。
    排除 test_img_idx 中指定编号的图像（留给测试集），其余全部作为训练集。

    参数:
        test_img_idx (list[int]): 测试集图像编号列表。
                                  例如 [9, 10] 表示每人的第 9、10 张作为测试集，
                                  第 1~8 张作为训练集。

    返回:
        train_x (torch.Tensor): 训练集图像，形状 (N, D)，N 为训练样本数，D 为像素维度
        train_y (torch.Tensor): 训练集标签，形状 (N,)，取值 1~40 对应人编号
        img_h (int): 图像高度（像素）
        img_w (int): 图像宽度（像素）
    """
    train_x, train_y = [], []

    # 遍历 40 个人的文件夹 s1 ~ s40
    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        # 遍历每个人的 10 张图片 1.pgm ~ 10.pgm
        for j in range(1, 11):
            if j in test_img_idx:
                continue  # 属于测试集编号，跳过

            img_path = os.path.join(dir_path, f'{j}.pgm')
            # 以灰度模式读取 PGM 图像
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # 将 2D 图像矩阵展平为 1D 向量（92×112 = 10304 维）
            img_flat = img.reshape(-1)
            train_x.append(img_flat)
            train_y.append(i)  # 标签即为文件夹编号 (1~40)

    # 将列表转换为 PyTorch 张量
    train_x = torch.tensor(np.array(train_x), dtype=torch.float32)
    train_y = torch.tensor(np.array(train_y), dtype=torch.long)

    # 记录图像的原始宽高，后续用于特征脸可视化时还原形状
    img_h, img_w = img.shape
    return train_x, train_y, img_h, img_w


def train_model_process(model, train_x, train_y):
    """
    训练 PCA 模型并保存

    将训练数据送入 PCA 模型进行拟合，提取特征脸后保存模型参数。
    保存内容：K值、平均脸、特征脸矩阵、训练集低维特征、训练集标签。

    参数:
        model (PCAFaceModel): PCA 模型实例
        train_x (torch.Tensor): 训练集图像数据
        train_y (torch.Tensor): 训练集标签

    返回:
        PCAFaceModel: 训练完成的模型（已计算 mean_face 和 eigen_faces）
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 20)
    print("模型开始训练 (PCA降维) ...")

    # 将数据转移到计算设备（GPU 或 CPU）
    train_x = train_x.to(device)
    train_y = train_y.to(device)

    # 训练 PCA：计算平均脸和特征脸
    model.fit(train_x)

    # 计算训练集在特征空间中的低维表示（用于测试时的 1-NN 比对）
    train_features = model.transform(train_x)

    # 打包模型参数和训练集特征，保存到文件
    save_dict = {
        'k': model.k,                         # 主成分数量
        'mean_face': model.mean_face.cpu(),    # 平均脸向量
        'eigen_faces': model.eigen_faces.cpu(),  # 特征脸矩阵
        'train_features': train_features.cpu(),  # 训练集低维特征
        'train_labels': train_y.cpu()           # 训练集标签（身份库）
    }
    torch.save(save_dict, './pca_model.pth')

    print("模型训练结束并已保存至 ./pca_model.pth")
    print("=" * 20)
    return model


def matplot_eigenfaces(model, img_h, img_w):
    """
    可视化平均脸和前 9 个特征脸

    生成 2×5 的子图布局：第一张为平均脸，后续 9 张为最重要的特征脸。
    保存为 eigenfaces_show.png（300 DPI），用于实验报告。

    参数:
        model (PCAFaceModel): 已训练的 PCA 模型
        img_h (int): 图像高度（像素），用于将 1D 向量还原为 2D 图像
        img_w (int): 图像宽度（像素）
    """
    plt.figure(figsize=(12, 6))

    # 子图 1：平均脸（所有训练样本的逐像素均值）
    plt.subplot(2, 5, 1)
    mean_img = model.mean_face.cpu().numpy().reshape(img_h, img_w)
    plt.imshow(mean_img, cmap='gray')
    plt.title("Mean Face")
    plt.axis('off')

    # 子图 2~10：前 9 个特征脸（方差最大的 9 个主成分方向）
    eigen_faces_np = model.eigen_faces.cpu().numpy()
    for i in range(9):
        plt.subplot(2, 5, i + 2)
        # 取出第 i 列（第 i 个主成分），还原为 2D 图像形状
        ef = eigen_faces_np[:, i].reshape(img_h, img_w)
        plt.imshow(ef, cmap='gray')
        plt.title(f"Eigenface {i + 1}")
        plt.axis('off')

    plt.tight_layout()
    plt.savefig('./eigenfaces_show.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    # 设定测试集图像编号：[9, 10] 表示每人的第 9、10 张图作测试，1~8 作训练
    TEST_IMAGE_INDEX = [9, 10]

    # 实例化 PCA 模型，保留前 50 个主成分
    pca_model = PCAFaceModel(k_components=50)

    # 加载并处理训练集
    train_x, train_y, img_h, img_w = train_data_process(test_img_idx=TEST_IMAGE_INDEX)
    print(f"训练集规模：{train_x.shape[0]} 张图片, 展平维度: {train_x.shape[1]}")

    # 训练并保存模型
    trained_model = train_model_process(pca_model, train_x, train_y)

    # 生成特征脸可视化图（用于实验报告）
    matplot_eigenfaces(trained_model, img_h, img_w)