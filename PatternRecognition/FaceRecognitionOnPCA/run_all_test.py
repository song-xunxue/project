import sys
import datetime
import torch
from model import PCAFaceModel

# 从已经写好的三个文件中导入测试函数和数据处理函数
from test_model import test_data_process, test_model_process
from test_model2 import test_model2_process
from test_model3 import test_model3_svm_process


# 定义一个双向输出的 Logger 类
# 它的作用是拦截 print 语句，让内容既显示在屏幕上，又写入文件
class Logger(object):
    def __init__(self, filename="experiment_results.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # 确保实时写入文件

    def flush(self):
        pass


if __name__ == "__main__":
    # 1. 启动日志记录拦截
    sys.stdout = Logger("experiment_results.log")

    print("\n" + "=" * 60)
    print(f"=== 实验测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("=" * 60)

    # 2. 准备设备和加载模型参数
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"当前使用的计算设备: {device}\n")

    save_dict = torch.load('pca_model.pth')
    model = PCAFaceModel(k_components=save_dict['k'])
    model.mean_face = save_dict['mean_face'].to(device)
    model.eigen_faces = save_dict['eigen_faces'].to(device)

    train_features = save_dict['train_features'].to(device)
    train_labels = save_dict['train_labels'].to(device)

    # 设定测试集
    TEST_IMAGE_INDEX = [9, 10]
    test_x, test_y = test_data_process(test_img_idx=TEST_IMAGE_INDEX)

    # 3. 依次执行三版对比实验

    # 【版本一】欧氏距离 1-NN
    test_model_process(model, test_x, test_y, train_features, train_labels)
    print("\n" + "-" * 60 + "\n")

    # 【版本二】余弦相似度 1-NN
    test_model2_process(model, test_x, test_y, train_features, train_labels)
    print("\n" + "-" * 60 + "\n")

    # 【版本三】PCA + SVM 机器学习分类
    test_model3_svm_process(model, test_x, test_y, train_features, train_labels)
    print("\n")

    print("=== 所有对比实验执行完毕，结果已安全保存至 experiment_results.log ===")