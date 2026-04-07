"""
PCA人脸识别 — 全部对比实验运行脚本

依次执行三种分类方法的测试，将结果同时输出到控制台和日志文件。
每次运行会在 experiment_results.log 中追加一条带时间戳的记录。

分类方法：
    1. 欧氏距离 1-NN（test_model.py）
    2. 余弦相似度 1-NN（test_model2.py）
    3. PCA + SVM 支持向量机（test_model3.py）

运行方式：
    python run_all_test.py
    （需先运行 model_train.py 生成 pca_model.pth）

作者: 李文煜
日期: 2026-03-13
"""

import sys
import datetime
import torch
from model.model import PCAFaceModel

# 从三个测试模块中导入测试函数和数据处理函数
from model.test_model import test_data_process, test_model_process
from model.test_model2 import test_model2_process
from model.test_model3 import test_model3_svm_process


class Logger(object):
    """
    双向输出 Logger：同时将内容写入控制台和日志文件

    通过替换 sys.stdout，拦截所有 print 输出，
    使其既显示在屏幕上，又实时追加到日志文件中。

    参数:
        filename (str): 日志文件路径，默认 "experiment_results.log"
    """

    def __init__(self, filename="experiment_results.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # 确保每条输出都实时写入文件

    def flush(self):
        pass


if __name__ == "__main__":
    # 步骤1：启动日志记录（拦截 sys.stdout）
    sys.stdout = Logger("experiment_results.log")

    # 打印本次实验的时间戳头部
    print("\n" + "=" * 60)
    print(f"=== PCA人像识别 实验测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("=" * 60)

    # 步骤2：加载已训练的 PCA 模型和训练集特征库
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"当前使用的计算设备: {device}\n")

    save_dict = torch.load('pca_model.pth')
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 步骤3：加载测试集（编号与训练时互补）
    TEST_IMAGE_INDEX = [9, 10]
    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 步骤4：依次执行三种分类方法的对比实验

    # 【方法一】欧氏距离 1-NN
    test_model_process(model, test_x, test_y, train_features, train_labels)
    print("\n" + "-" * 60 + "\n")

    # 【方法二】余弦相似度 1-NN
    test_model2_process(model, test_x, test_y, train_features, train_labels)
    print("\n" + "-" * 60 + "\n")

    # 【方法三】PCA + SVM 支持向量机
    test_model3_svm_process(model, test_x, test_y, train_features, train_labels)
    print("\n")

    print("=== 所有对比实验执行完毕，结果已保存至 experiment_results.log ===")