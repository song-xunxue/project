import os
import cv2
import torch
import numpy as np
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from model import PCAFaceModel  # 导入自定义的 PCA 模型


# 1. 训练数据准备
def train_data_process(test_img_idx):
    """
    test_img_idx: 设定作为测试集的图像编号列表。例如 [9, 10] 表示每个s文件下的 9.pgm 和 10.pgm 作为测试集，其余作训练。
    """
    train_x, train_y = [], []

    # 遍历 40 个人的文件夹
    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        # 遍历每个人的 10 张图片
        for j in range(1, 11):
            if j in test_img_idx:
                continue  # 如果是测试集编号，跳过不加入训练集

            img_path = os.path.join(dir_path, f'{j}.pgm')
            # 采用灰度模式读取 pgm 图像
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # 将图片展平成 1D 向量
            img_flat = img.reshape(-1)
            train_x.append(img_flat)
            train_y.append(i)  # 类别标签即为文件夹编号 (1-40)

    # 转换为 PyTorch 的 Tensor
    train_x = torch.tensor(np.array(train_x), dtype=torch.float32)
    train_y = torch.tensor(np.array(train_y), dtype=torch.long)

    # 返回训练集张量和原始图像的宽高（方便画图还原）
    img_h, img_w = img.shape
    return train_x, train_y, img_h, img_w


# 2. 训练过程
def train_model_process(model, train_x, train_y):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 20)
    print("模型开始训练 (PCA降维) ...")

    # 把数据放到对应设备上
    train_x = train_x.to(device)
    train_y = train_y.to(device)

    # 训练PCA提取特征脸
    model.fit(train_x)

    # 计算训练集的投影特征（低维表示）
    train_features = model.transform(train_x)

    # 保存训练好的模型组件和训练集特征（用于测试时1-NN比对）
    save_dict = {
        'k': model.k,
        'mean_face': model.mean_face.cpu(),
        'eigen_faces': model.eigen_faces.cpu(),
        'train_features': train_features.cpu(),
        'train_labels': train_y.cpu()
    }
    torch.save(save_dict, './pca_model.pth')

    print("模型训练结束并已保存至 ./pca_model.pth")
    print("=" * 20)
    return model


# 3. 画图函数：展示平均脸和特征脸（用于实验报告）
def matplot_eigenfaces(model, img_h, img_w):
    plt.figure(figsize=(12, 6))

    # 画出平均脸
    plt.subplot(2, 5, 1)
    mean_img = model.mean_face.cpu().numpy().reshape(img_h, img_w)
    plt.imshow(mean_img, cmap='gray')
    plt.title("Mean Face")
    plt.axis('off')

    # 画出前 9 个特征脸
    eigen_faces_np = model.eigen_faces.cpu().numpy()
    for i in range(9):
        plt.subplot(2, 5, i + 2)
        # 取出对应的列向量并还原形状
        ef = eigen_faces_np[:, i].reshape(img_h, img_w)
        plt.imshow(ef, cmap='gray')
        plt.title(f"Eigenface {i + 1}")
        plt.axis('off')

    plt.tight_layout()
    plt.savefig('./eigenfaces_show.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    # 设定测试集编号，这里设为最后两张图像[9, 10]，剩下的 1-8 将用作训练
    TEST_IMAGE_INDEX = [9, 10]
    #TEST_IMAGE_INDEX = [10]

    # 实例化模型，设定保留的主成分数量 K=50
    pca_model = PCAFaceModel(k_components=50)

    # 加载并处理训练集
    train_x, train_y, img_h, img_w = train_data_process(test_img_idx=TEST_IMAGE_INDEX)
    print(f"训练集规模：{train_x.shape[0]} 张图片, 展平维度: {train_x.shape[1]}")

    # 开始训练并保存
    trained_model = train_model_process(pca_model, train_x, train_y)

    # 画图用于生成实验报告素材
    matplot_eigenfaces(trained_model, img_h, img_w)