"""
LeNet 实验聚合测试脚本

加载训练好的 LeNet-5 模型，在 Fashion-MNIST 测试集上进行完整评估，
输出逐类别 precision/recall/F1 和总体准确率，同时写入日志文件。

运行方式：
    python run_all_test.py
    （需先运行 model_train.py 训练模型生成 best_model.pth）

作者: 李文煜
日期: 2026-04-07
"""

import sys
import datetime
import torch
import numpy as np
from sklearn.metrics import classification_report
from torchvision.datasets import FashionMNIST
from torchvision import transforms
import torch.utils.data as Data

from model import LeNet

CLASS_NAMES = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']


class Logger(object):
    """双向输出 Logger：同时写入控制台和日志文件"""

    def __init__(self, filename="experiment_results.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        pass


if __name__ == '__main__':
    # 启动日志记录
    sys.stdout = Logger("experiment_results.log")

    print("=" * 60)
    print(f"=== LeNet-5 实验测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"计算设备: {device}")

    # 加载模型
    model = LeNet().to(device)
    model.load_state_dict(torch.load('./best_model.pth', map_location=device))
    model.eval()
    print("模型加载完成: ./best_model.pth")

    # 加载测试集（使用真正的测试集，train=False）
    test_data = FashionMNIST(
        root='./data', train=False,
        transform=transforms.Compose([transforms.Resize(size=28), transforms.ToTensor()]),
        download=True
    )
    test_loader = Data.DataLoader(dataset=test_data, batch_size=64, shuffle=False, num_workers=0)
    print(f"测试集样本数: {len(test_data)}")

    # 逐批次预测
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for b_x, b_y in test_loader:
            b_x = b_x.to(device)
            output = model(b_x)
            pre_lab = torch.argmax(output, dim=1)
            all_preds.extend(pre_lab.cpu().numpy())
            all_labels.extend(b_y.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # 总体准确率
    total = len(all_labels)
    correct = (all_preds == all_labels).sum()
    acc = correct / total * 100
    print(f"\n总体准确率: {acc:.2f}% ({correct}/{total})")

    # 逐类别准确率
    print("\n各类别准确率:")
    print(f"{'类别':<15} | {'正确数':>6} | {'总数':>6} | {'准确率':>8}")
    print("-" * 45)
    for i, name in enumerate(CLASS_NAMES):
        mask = all_labels == i
        cls_correct = (all_preds[mask] == i).sum()
        cls_total = mask.sum()
        cls_acc = cls_correct / cls_total * 100
        print(f"{name:<15} | {cls_correct:>6} | {cls_total:>6} | {cls_acc:>7.2f}%")

    # 分类报告
    print("\n详细分类报告 (Classification Report):")
    report = classification_report(all_labels, all_preds, target_names=CLASS_NAMES, digits=4)
    print(report)

    print("=== LeNet-5 测试完毕，结果已保存至 experiment_results.log ===")
