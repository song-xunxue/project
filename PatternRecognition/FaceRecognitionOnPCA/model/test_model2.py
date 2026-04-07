
"""
PCA人脸识别测试脚本 — 版本二：余弦相似度 1-NN

分类策略：
    与版本一（欧氏距离）不同，本版本使用余弦相似度衡量特征向量间的相似性。
    余弦相似度关注向量方向的夹角，不受向量幅度影响，对光照变化更具鲁棒性。

    余弦相似度公式：cos(θ) = (x · y) / (||x|| * ||y||)
    取值范围 [-1, 1]，值越大表示越相似，因此用 argmax 找最相似样本。

运行方式：
    python test_model2.py

作者: 李文煜
日期: 2026-03-11
"""

import os
import cv2
import torch
import numpy as np
from model import PCAFaceModel


def test_data_process(test_img_idx):
    """
    构建测试集（与 test_model.py 相同）

    参数:
        test_img_idx (list[int]): 测试集图像编号列表

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

            img_flat = img.reshape(-1)
            test_x.append(img_flat)
            test_y.append(i)

    test_x = torch.tensor(np.array(test_x), dtype=torch.float32)
    test_y = torch.tensor(np.array(test_y), dtype=torch.long)
    return test_x, test_y


def test_model2_process(model, test_x, test_y, train_features, train_labels):
    """
    使用余弦相似度 1-NN 进行人脸识别测试

    对每个测试样本：
        1. 通过 PCA 投影到低维空间
        2. 计算与所有训练样本特征的余弦相似度
        3. 取相似度最大的训练样本标签作为预测（argmax）

    参数:
        model (PCAFaceModel): 已训练的 PCA 模型
        test_x (torch.Tensor): 测试集图像
        test_y (torch.Tensor): 测试集真实标签
        train_features (torch.Tensor): 训练集的 PCA 低维特征
        train_labels (torch.Tensor): 训练集标签

    返回:
        float: 准确率（0~1）

    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 30)
    print("模型开始测试 [方法二：余弦相似度 1-NN] ...")
    print("=" * 30)

    # 将所有数据转移到计算设备
    test_x = test_x.to(device)
    test_y = test_y.to(device)
    train_features = train_features.to(device)
    train_labels = train_labels.to(device)

    test_corrects = 0
    test_num = test_x.size(0)

    # 将测试集投影到 PCA 低维特征空间
    test_features = model.transform(test_x)

    # 逐个测试样本进行最近邻比对
    for i in range(test_num):
        current_test_feature = test_features[i]

        # 核心区别：使用余弦相似度替代欧氏距离
        # unsqueeze(0) 将形状 [K] 扩展为 [1, K]，与 [N, K] 的 train_features 广播计算
        # dim=1 表示沿特征维度计算相似度
        similarities = torch.nn.functional.cosine_similarity(
            train_features, current_test_feature.unsqueeze(0), dim=1
        )

        # 余弦相似度越大越相似，因此取 argmax（欧氏距离取 argmin）
        max_idx = torch.argmax(similarities)

        pre_lab = train_labels[max_idx]
        real_lab = test_y[i]

        if pre_lab == real_lab:
            test_corrects += 1
            print(f"✅ 测试样本 {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d}")
        else:
            # 预测错误时额外输出相似度分数，便于分析
            print(
                f"测试样本❌ {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d} "
                f"(相似度: {similarities[max_idx]:.4f})")

    # 计算并输出准确率
    test_acc = test_corrects / test_num
    print("=" * 30)
    print(f"[余弦相似度 1-NN] 模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 30)
    return test_acc


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载已保存的 PCA 模型参数和训练集特征库
    save_dict = torch.load('pca_model.pth')

    # 实例化模型并加载训练好的参数
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    # 加载训练集的低维特征和标签
    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 测试集编号，与训练时互补
    TEST_IMAGE_INDEX = [9, 10]

    # 加载测试数据
    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 运行余弦相似度 1-NN 测试
    test_model2_process(model, test_x, test_y, train_features, train_labels)