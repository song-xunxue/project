"""
PCA人脸识别测试脚本 — 版本三：PCA + SVM 支持向量机

分类策略：
    在 PCA 降维后的低维特征空间上，训练一个 SVM（支持向量机）分类器。
    相比 1-NN 方法，SVM 能学习到类别间的决策边界，对噪声和异常值更具鲁棒性。

    本版本使用 sklearn 的 SVC，核函数为线性核（linear），在 PCA 子空间中
    寻找最优超平面来区分类别。

运行方式：
    python test_model3.py

作者: 李文煜
日期: 2026-03-11
"""

import os
import cv2
import torch
import numpy as np
from sklearn.svm import SVC
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


def test_model3_svm_process(model, test_x, test_y, train_features, train_labels):
    """
    使用 PCA + SVM 进行人脸识别测试

    流程：
        1. 将测试集通过 PCA 投影到低维空间
        2. 将 PyTorch 张量转为 NumPy 数组（sklearn 接口要求）
        3. 在训练集特征上训练 SVM 线性分类器
        4. 对测试集进行预测并统计准确率

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
    print("=" * 40)
    print("模型开始测试 [方法三：PCA降维 + SVM支持向量机] ...")
    print("=" * 40)

    test_x = test_x.to(device)

    # 步骤1：将测试集通过 PCA 投影到低维空间
    test_features = model.transform(test_x)

    # 步骤2：将 PyTorch 张量转为 NumPy 数组（sklearn 不支持张量输入）
    X_train = train_features.cpu().numpy()
    Y_train = train_labels.cpu().numpy()
    X_test = test_features.cpu().numpy()
    Y_test = test_y.numpy()

    # 步骤3：初始化 SVM 分类器
    #   kernel='linear'：在PCA子空间中使用线性核，对人脸识别效果好
    #   C=1.0：正则化惩罚系数，控制对误分类的容忍度
    svm_classifier = SVC(kernel='linear', C=1.0)

    # 步骤4：在训练集特征上训练 SVM（维度已降到 K=50，训练非常快）
    svm_classifier.fit(X_train, Y_train)

    # 步骤5：对测试集进行预测
    predictions = svm_classifier.predict(X_test)

    # 步骤6：统计准确率并输出每个样本的预测结果
    test_corrects = 0
    test_num = len(Y_test)

    for i in range(test_num):
        pre_lab = predictions[i]
        real_lab = Y_test[i]

        if pre_lab == real_lab:
            test_corrects += 1
            print(f"✅ 测试样本 {i + 1:02d} | 预测: s{pre_lab:02d} ---- 真实: s{real_lab:02d}")
        else:
            print(f"❌ 测试样本 {i + 1:02d} | 预测: s{pre_lab:02d} ---- 真实: s{real_lab:02d}")

    test_acc = test_corrects / test_num
    print("=" * 40)
    print(f"[PCA + SVM 分类器] 模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 40)
    return test_acc


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载已保存的 PCA 模型参数
    save_dict = torch.load('pca_model.pth')

    # 实例化模型并加载参数
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    # 加载训练集特征库
    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 测试集编号
    TEST_IMAGE_INDEX = [9, 10]

    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 运行 PCA + SVM 测试
    test_model3_svm_process(model, test_x, test_y, train_features, train_labels)