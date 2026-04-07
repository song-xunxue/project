"""
LeNet-5 模型测试脚本

加载训练好的 LeNet-5 模型权重（best_model.pth），
在 Fashion-MNIST 测试集上进行推理和准确率评估。

功能：
    1. 完整测试集准确率评估（test_model_process）
    2. 逐样本预测结果展示（main 主流程）

运行方式：
    python test_model.py
    （需先运行 model_train.py 生成 best_model.pth）

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 修复 test_data_process 中 train=True → train=False，使用真正的测试集
  2. 添加模块文档字符串和详细中文注释
"""

import pandas as pd
import torch
from torch import nn
from torchvision.datasets import FashionMNIST
from torchvision import transforms
import torch.utils.data as Data
import numpy as np
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from model import LeNet  # 导入自定义的 LeNet 模型

# Fashion-MNIST 的 10 个类别名称
CLASS_NAMES = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']


def test_data_process():
    """
    加载 Fashion-MNIST 测试集

    使用 train=False 加载官方测试集（10,000 张图像），
    按批次大小 1 加载以便逐样本预测。

    返回:
        test_dataloader (DataLoader): 测试集数据加载器
    """
    test_data = FashionMNIST(root='./data',
                              train=False,  # 使用测试集（非训练集）
                              transform=transforms.Compose([
                                  transforms.Resize(size=28),
                                  transforms.ToTensor()
                              ]),
                              download=True)

    # batch_size=1：逐样本加载，便于展示每个预测结果
    test_dataloader = Data.DataLoader(dataset=test_data,
                                      batch_size=1,
                                      shuffle=True,
                                      num_workers=0)
    return test_dataloader


def test_model_process(model, test_dataloader):
    """
    在完整测试集上评估模型准确率

    参数:
        model (LeNet): 加载了权重的 LeNet 模型
        test_dataloader (DataLoader): 测试集数据加载器
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 20)
    print("模型开始测试，使用：", device)
    model = model.to(device)

    # 初始化统计量
    test_corrects = 0.0
    test_num = 0

    # torch.no_grad()：关闭梯度计算，节省内存和加速推理
    with torch.no_grad():
        for test_data_x, test_data_y in test_dataloader:
            test_data_x = test_data_x.to(device)
            test_data_y = test_data_y.to(device)
            model.eval()  # 设置为评估模式

            # 前向传播得到预测
            output = model(test_data_x)
            pre_lab = torch.argmax(output, dim=1)

            # 累加正确预测数
            test_corrects += torch.sum(pre_lab == test_data_y.data)
            test_num += test_data_x.size(0)

    # 计算总体准确率
    test_acc = test_corrects.double().item() / test_num
    print("模型准确率：", test_acc)
    print("=" * 20)


if __name__ == "__main__":
    # 实例化模型
    model = LeNet()
    # 加载训练好的模型权重
    model.load_state_dict(torch.load('best_model.pth'))

    # 加载测试数据
    test_data = test_data_process()

    # 运行完整测试（取消注释以执行）
    # test_model_process(model, test_data)

    # 逐样本预测展示
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()

    with torch.no_grad():
        for b_x, b_y in test_data:
            b_x = b_x.to(device)
            b_y = b_y.to(device)

            output = model(b_x)
            pre_lab = torch.argmax(output, dim=1)
            result = pre_lab.item()   # 预测类别索引
            lab = b_y.item()          # 真实类别索引
            print("预测值：", CLASS_NAMES[result], "----真实值", CLASS_NAMES[lab])
