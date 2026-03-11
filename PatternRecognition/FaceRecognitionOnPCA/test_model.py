import os
import cv2
import torch
import numpy as np
from model import PCAFaceModel  # 导入自定义的PCA模型


# 1. 测试数据准备
def test_data_process(test_img_idx):
    """
    与训练集对应，只读取选定作为测试集的图片编号
    """
    test_x, test_y = [], []

    for i in range(1, 41):
        dir_path = f'./data/s{i}'
        for j in range(1, 11):
            # 仅处理被选为测试的编号
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


# 2. 测试过程与比对 (1-NN 欧氏距离)
def test_model_process(model, test_x, test_y, train_features, train_labels):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 20)
    print("模型开始测试 ...")

    # 转移到设备
    test_x = test_x.to(device)
    test_y = test_y.to(device)
    train_features = train_features.to(device)
    train_labels = train_labels.to(device)

    test_corrects = 0
    test_num = test_x.size(0)

    # 将测试集映射到低维空间，获得测试特征
    test_features = model.transform(test_x)

    # 逐一比对特征距离
    for i in range(test_num):
        # 取出当前测试样本的低维特征
        current_test_feature = test_features[i]

        # 计算该测试样本与所有训练样本的欧氏距离 (广播机制)
        distances = torch.norm(train_features - current_test_feature, dim=1)

        # 寻找距离最近（最小）的训练样本索引
        min_idx = torch.argmin(distances)

        # 提取预测的标签
        pre_lab = train_labels[min_idx]
        real_lab = test_y[i]

        if pre_lab == real_lab:
            test_corrects += 1
            print(f"✅ 测试样本 {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d}")

        else:
            # 为了方便对比，预测错误的样本W加个显眼的提示
            print(f"测试样本❌ {i + 1:02d} | 预测: s{pre_lab.item():02d} ---- 真实: s{real_lab.item():02d}")


    # 计算最后的准确率
    test_acc = test_corrects / test_num
    print("=" * 20)
    print(f"模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 20)


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载模型参数与训练库特征
    save_dict = torch.load('pca_model.pth')

    # 实例化模型并挂载保存的参数
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    # 获取当时保存的训练集低维特征和对应标签（身份库）
    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 设定测试集的提取范围，这里必须与训练时的设定互补！
    # 比如这里设定[9, 10]，就意味着测试集包含了所有人的第9和第10张图。
    TEST_IMAGE_INDEX = [9, 10]
    # TEST_IMAGE_INDEX = [10]

    # 加载测试数据集
    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 开始测试
    test_model_process(model, test_x, test_y, train_features, train_labels)