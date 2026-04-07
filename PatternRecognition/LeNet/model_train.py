"""
LeNet-5 模型训练脚本

在 Fashion-MNIST 数据集上训练 LeNet-5 模型，包含：
    1. 数据加载与训练/验证集划分（80:20）
    2. 训练循环（Adam 优化器，交叉熵损失，20 epochs）
    3. 最优模型保存（按验证集准确率选择）
    4. 训练/验证损失和准确率曲线绘制

训练参数：
    - Epochs: 20
    - Batch Size: 64
    - Learning Rate: 0.001
    - Optimizer: Adam
    - Loss: CrossEntropyLoss

运行方式：
    python model_train.py
    输出：best_model.pth（最优模型权重）+ train_val_curve.png（训练曲线）

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 添加模块文档字符串和详细中文注释
"""

import copy
import time

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


def train_val_data_process():
    """
    加载 Fashion-MNIST 训练数据并划分训练集和验证集

    流程：
        1. 从 torchvision 下载/加载 Fashion-MNIST 训练集（60,000张）
        2. 按 80:20 比例随机划分为训练集（48,000）和验证集（12,000）
        3. 创建 DataLoader 进行批次加载

    返回:
        train_dataloader (DataLoader): 训练集数据加载器（batch=64, shuffle=True）
        val_dataloader (DataLoader): 验证集数据加载器（batch=64, shuffle=False）
    """
    # 加载 Fashion-MNIST 训练集，将图像调整为 28×28 并转为张量
    train_data = FashionMNIST(root='./data',
                              train=True,
                              transform=transforms.Compose([
                                  transforms.Resize(size=28),
                                  transforms.ToTensor()
                              ]),
                              download=True)

    # 按 8:2 比例划分训练集和验证集
    train_data, val_data = Data.random_split(
        train_data,
        [round(0.8 * len(train_data)), round(0.2 * len(train_data))]
    )

    # 创建训练集 DataLoader（打乱顺序以增加训练随机性）
    train_dataloader = Data.DataLoader(
        dataset=train_data,
        batch_size=64,
        shuffle=True,
        num_workers=2
    )
    # 创建验证集 DataLoader（不打乱，保持顺序以复现结果）
    val_dataloader = Data.DataLoader(
        dataset=val_data,
        batch_size=64,
        shuffle=False,
        num_workers=2
    )
    return train_dataloader, val_dataloader


def train_model_process(model, train_dataloader, val_dataloader, num_epochs):
    """
    训练 LeNet-5 模型

    每轮（epoch）包含两个阶段：
        - 训练阶段：前向传播 → 计算损失 → 反向传播 → 更新参数
        - 验证阶段：仅前向传播，评估模型在未见数据上的表现
    训练结束后保存验证集准确率最高的模型权重。

    参数:
        model (LeNet): 待训练的 LeNet 模型实例
        train_dataloader (DataLoader): 训练集数据加载器
        val_dataloader (DataLoader): 验证集数据加载器
        num_epochs (int): 训练轮次

    返回:
        train_process_info (pd.DataFrame): 包含每轮训练/验证损失和准确率的 DataFrame
    """
    # 训练设备：优先使用 GPU（CUDA），否则使用 CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 20)
    print("模型开始训练，使用：", device)

    # Adam 优化器：自适应学习率优化，传入模型参数和学习率
    optimizer = torch.optim.Adam(model.parameters(), 0.001)
    # 交叉熵损失函数（适用于多分类任务，内部包含 Softmax）
    criterion = nn.CrossEntropyLoss()
    # 将模型移至计算设备
    model = model.to(device)
    # 深拷贝当前模型参数作为最优模型初始化
    best_model_wts = copy.deepcopy(model.state_dict())

    # === 训练过程记录 ===
    best_acc = 0.0                      # 最高验证集准确率（用于保存最优模型）
    train_loss_all = []                 # 每轮训练损失
    val_loss_all = []                   # 每轮验证损失
    train_acc_all = []                  # 每轮训练准确率
    val_acc_all = []                    # 每轮验证准确率
    since = time.time()                 # 训练开始时间

    # === 逐轮训练 ===
    for i in range(num_epochs):
        # 每轮初始化累加器
        train_loss = 0
        train_corrects = 0.0
        val_loss = 0
        val_corrects = 0.0
        train_nums = 0
        val_nums = 0

        print("=== 第{}轮 / 总轮次{} ===".format(i, num_epochs - 1))

        # ---- 训练阶段 ----
        for step, (b_x, b_y) in enumerate(train_dataloader):
            b_x = b_x.to(device)    # 特征移至设备
            b_y = b_y.to(device)    # 标签移至设备
            model.train()           # 设置为训练模式（启用 Dropout/BatchNorm 等）

            # 前向传播：输入一个 batch，输出各类别得分 (batch_size, 10)
            output = model(b_x)
            # 取得分最高的类别作为预测标签
            pre_lab = torch.argmax(output, dim=1)
            # 计算交叉熵损失
            loss = criterion(output, b_y)

            # 反向传播三步曲：
            optimizer.zero_grad()   # 1. 清零梯度（防止累积）
            loss.backward()         # 2. 反向传播计算梯度
            optimizer.step()        # 3. 根据梯度更新模型参数

            # 累加该 batch 的损失和正确数
            train_loss += loss.item() * b_x.size(0)  # 平均损失 × 样本数 = 总损失
            train_corrects += torch.sum(pre_lab == b_y.data)
            train_nums += b_x.size(0)

        # ---- 验证阶段 ----
        for step, (b_x, b_y) in enumerate(val_dataloader):
            b_x = b_x.to(device)
            b_y = b_y.to(device)
            model.eval()            # 设置为评估模式（关闭 Dropout/BatchNorm）

            output = model(b_x)
            pre_lab = torch.argmax(output, dim=1)
            loss = criterion(output, b_y)
            # 验证阶段不进行反向传播和参数更新

            val_loss += loss.item() * b_x.size(0)
            val_corrects += torch.sum(pre_lab == b_y.data)
            val_nums += b_x.size(0)

        # ---- 计算该轮平均损失和准确率 ----
        train_loss_all.append(train_loss / train_nums)
        train_acc_all.append(train_corrects.double().item() / train_nums)
        val_loss_all.append(val_loss / val_nums)
        val_acc_all.append(val_corrects.double().item() / val_nums)

        print("Train: loss:{:.4f}  acc:{:.4f}".format(train_loss_all[-1], train_acc_all[-1]))
        print(" Val : loss:{:.4f}  acc:{:.4f}".format(val_loss_all[-1], val_acc_all[-1]))

        # 该轮消耗时间
        time_use = time.time() - since
        print("第{:}轮消耗时间：{:.0f} m {:.0f}s".format(i, time_use // 60, time_use % 60))

        # ---- 保存最优模型 ----
        if val_acc_all[-1] > best_acc:
            best_acc = val_acc_all[-1]
            best_model_wts = copy.deepcopy(model.state_dict())

    # 加载最优模型参数并保存到文件
    model.load_state_dict(best_model_wts)
    torch.save(best_model_wts, './best_model.pth')

    time_use = time.time() - since
    print("===模型消耗总时间：{:.0f} m {:.0f}s===".format(time_use // 60, time_use % 60))

    # 将训练过程数据整理为 DataFrame
    train_process_info = pd.DataFrame(data={
        "epoch": range(num_epochs),
        "train_loss_all": train_loss_all,
        "train_acc_all": train_acc_all,
        "val_loss_all": val_loss_all,
        "val_acc_all": val_acc_all
    })

    print("模型训练结束")
    print("=" * 20)
    return train_process_info


def matplot_acc_loss(process_info):
    """
    绘制训练和验证的损失/准确率曲线

    生成 1×2 子图：
        - 左图：训练损失 vs 验证损失（随 epoch 变化）
        - 右图：训练准确率 vs 验证准确率（随 epoch 变化）

    参数:
        process_info (pd.DataFrame): 包含 epoch、train_loss_all、val_loss_all、
                                      train_acc_all、val_acc_all 列的 DataFrame
    """
    plt.figure(figsize=(12, 4))

    # 左图：损失曲线
    plt.subplot(1, 2, 1)
    plt.plot(process_info["epoch"], process_info["train_loss_all"], 'ro-', label="train_loss")
    plt.plot(process_info["epoch"], process_info["val_loss_all"], 'bs-', label="val_loss")
    plt.legend()
    plt.xlabel("epoch")
    plt.ylabel("loss")

    # 右图：准确率曲线
    plt.subplot(1, 2, 2)
    plt.plot(process_info["epoch"], process_info["train_acc_all"], 'ro-', label="train_acc")
    plt.plot(process_info["epoch"], process_info["val_acc_all"], 'bs-', label="val_acc")
    plt.legend()
    plt.xlabel("epoch")
    plt.ylabel("acc")

    plt.savefig('./train_val_curve.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    # 模型实例化
    LeNet = LeNet()
    # 加载并划分数据集
    train_data, val_data = train_val_data_process()
    # 训练模型（20 个 epoch）
    train_process_info = train_model_process(LeNet, train_data, val_data, 20)
    # 绘制训练曲线
    matplot_acc_loss(train_process_info)
