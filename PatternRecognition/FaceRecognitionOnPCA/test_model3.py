import os
import cv2
import torch
import numpy as np
from sklearn.svm import SVC
from model import PCAFaceModel  # 导入自定义的PCA模型


# 1. 测试数据准备 (与之前完全一致)
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


# 2. 测试过程：使用 sklearn 的 SVM 进行分类
def test_model3_svm_process(model, test_x, test_y, train_features, train_labels):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 40)
    print("模型开始测试 [进阶技术：PCA降维 + SVM支持向量机] ...")
    print("=" * 40)

    test_x = test_x.to(device)

    # 1. 获得测试集的 PCA 降维特征
    test_features = model.transform(test_x)

    # 2. 将 PyTorch Tensor 转换为 Numpy 数组，供 sklearn 机器学习库使用
    X_train = train_features.cpu().numpy()
    Y_train = train_labels.cpu().numpy()
    X_test = test_features.cpu().numpy()
    Y_test = test_y.numpy()

    # 3. 初始化 SVM 分类器
    # kernel='linear' 表示在PCA子空间中寻找线性边界，对于高维特征效果通常最好
    # C 是正则化惩罚系数，默认 1.0 即可
    svm_classifier = SVC(kernel='linear', C=1.0)

    # 4. 训练 SVM (这一步极快，因为特征维度已经降到了 K=50)
    svm_classifier.fit(X_train, Y_train)

    # 5. 进行预测
    predictions = svm_classifier.predict(X_test)

    # 6. 统计准确率
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
            continue


    test_acc = test_corrects / test_num
    print("=" * 40)
    print(f"【PCA + SVM 分类器】模型准确率：{test_acc * 100:.2f} %  ({test_corrects}/{test_num})")
    print("=" * 40)


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 直接加载已有的 PCA 模型参数与特征库，无需重新降维
    save_dict = torch.load('pca_model.pth')

    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 设定测试集 (使用第9和第10张图)
    TEST_IMAGE_INDEX = [9, 10]

    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 运行 SVM 测试
    test_model3_svm_process(model, test_x, test_y, train_features, train_labels)