import os
import cv2
import torch
import numpy as np
from model import PCAFaceModel  # 导入自定义的PCA模型


# 1. 测试数据准备 (与 test_model.py 完全一致)
def test_data_process(test_img_idx):
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


# 2. 测试过程与比对 (核心修改：使用余弦相似度)
def test_model2_process(model, test_x, test_y, train_features, train_labels):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 30)
    print("模型开始测试[技术一：基于 余弦相似度 的 1-NN] ...")
    print("=" * 30)

    # 转移到设备
    test_x = test_x.to(device)
    test_y = test_y.to(device)
    train_features = train_features.to(device)
    train_labels = train_labels.to(device)

    test_corrects = 0
    test_num = test_x.size(0)

    # 将测试集映射到低维特征空间
    test_features = model.transform(test_x)

    # 逐一比对特征
    for i in range(test_num):
        current_test_feature = test_features[i]

        # 核心改动区：将欧氏距离替换为“余弦相似度”
        # 使用 unsqueeze(0) 将 [K] 变成[1, K]，以便与 [N, K] 的 train_features 广播计算
        # dim=1 表示在特征维度上计算相似度

        similarities = torch.nn.functional.cosine_similarity(train_features, current_test_feature.unsqueeze(0), dim=1)

        # 欧氏距离是找最小(argmin)，而余弦相似度越大越相似，所以找最大(argmax)
        max_idx = torch.argmax(similarities)

        # 提取预测的标签
        pre_lab = train_labels[max_idx]
        real_lab = test_y[i]

        if pre_lab == real_lab:
            test_corrects += 1
            print(f"✅ 测试样本 {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d}")
        else:
            # 为了方便对比，预测错误的样本W加个显眼的提示
            print(
                f"测试样本❌ {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d} (相似度: {similarities[max_idx]:.4f})")


    # 计算最后的准确率
    test_acc = test_corrects / test_num
    print("=" * 30)
    print(f"[余弦相似度]模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 30)


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 直接加载刚刚训练好的模型参数与训练库特征 (不需要重新训练)
    save_dict = torch.load('pca_model.pth')

    # 实例化模型并挂载保存的参数
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    # 获取当时保存的训练集低维特征和对应标签（身份库）
    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 设定测试集 (保持与之前一致，使用9,10作为测试)
    TEST_IMAGE_INDEX = [9, 10]

    # 加载测试数据集
    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 开始测试
    test_model2_process(model, test_x, test_y, train_features, train_labels)