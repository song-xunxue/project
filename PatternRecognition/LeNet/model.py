"""
LeNet-5 卷积神经网络模型定义

经典 LeNet-5 架构（Yann LeCun, 1998），适配 Fashion-MNIST 数据集（28×28 灰度图）。

网络结构：
    输入 (1×28×28) → C1 Conv(6) → Sigmoid → S3 AvgPool → C4 Conv(16) → Sigmoid
    → S5 AvgPool → Flatten → F6 Linear(120) → F7 Linear(84) → F8 Linear(10)

    - C1: 卷积层，6个5×5卷积核，padding=2 保持尺寸
    - S3: 平均池化层，2×2，步长2，尺寸减半
    - C4: 卷积层，16个5×5卷积核
    - S5: 平均池化层，2×2，步长2
    - F6-F8: 三个全连接层，最终输出10类

运行方式：
    python model.py
    打印模型结构和参数量

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 添加模块文档字符串和详细中文注释
"""

import torch
from torch import nn
from torchsummary import summary


class LeNet(nn.Module):
    """
    LeNet-5 卷积神经网络

    继承 PyTorch 的 nn.Module 基类，需重写 __init__（定义网络层）
    和 forward（定义前向传播逻辑）方法。

    架构细节：
        C1: Conv2d(1→6, kernel=5×5, padding=2, stride=1) + Sigmoid
        S3: AvgPool2d(kernel=2, stride=2)
        C4: Conv2d(6→16, kernel=5×5) + Sigmoid
        S5: AvgPool2d(kernel=2, stride=2)
        F6: Linear(400→120)
        F7: Linear(120→84)
        F8: Linear(84→10) — 10类输出
    """

    def __init__(self):
        """初始化 LeNet-5 的各网络层"""
        super(LeNet, self).__init__()  # 调用父类 nn.Module 的初始化方法

        # === 特征提取部分（卷积 + 池化）===

        # C1 卷积层：输入1通道（灰度图），输出6通道，5×5卷积核，padding=2保持28×28尺寸
        self.c1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, padding=2, stride=1)
        # Sigmoid 激活函数（LeNet 原始设计使用 Sigmoid，现代网络多用 ReLU）
        self.sig = nn.Sigmoid()

        # S3 平均池化层：2×2窗口，步长2，将28×28下采样为14×14
        self.s3 = nn.AvgPool2d(kernel_size=2, stride=2)

        # C4 卷积层：输入6通道，输出16通道，5×5卷积核（无padding，14-5+1=10，输出10×10）
        self.c4 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5)

        # S5 平均池化层：2×2窗口，步长2，将10×10下采样为5×5
        self.s5 = nn.AvgPool2d(kernel_size=2, stride=2)

        # === 分类器部分（全连接层）===

        # Flatten 层：将多维特征展平为一维向量（16×5×5=400）
        self.flatten = nn.Flatten()

        # F6 全连接层：400→120
        self.f6 = nn.Linear(in_features=400, out_features=120)
        # F7 全连接层：120→84
        self.f7 = nn.Linear(in_features=120, out_features=84)
        # F8 输出层：84→10（对应 Fashion-MNIST 的 10 个类别）
        self.f8 = nn.Linear(in_features=84, out_features=10)

    def forward(self, input):
        """
        前向传播：定义数据从输入到输出的计算流程

        参数:
            input (torch.Tensor): 输入图像张量，形状 (batch_size, 1, 28, 28)

        返回:
            torch.Tensor: 各类别的得分，形状 (batch_size, 10)
        """
        out2 = self.sig(self.c1(input))   # C1 卷积 + Sigmoid: (1,28,28) → (6,28,28)
        out3 = self.s3(out2)               # S3 池化: (6,28,28) → (6,14,14)
        out4 = self.sig(self.c4(out3))     # C4 卷积 + Sigmoid: (6,14,14) → (16,10,10)
        out5 = self.s5(out4)               # S5 池化: (16,10,10) → (16,5,5)

        out5 = self.flatten(out5)          # 展平: (16,5,5) → (400,)
        out6 = self.f6(out5)               # F6 全连接: 400 → 120
        out7 = self.f7(out6)               # F7 全连接: 120 → 84
        final_out = self.f8(out7)          # F8 输出层: 84 → 10
        return final_out


if __name__ == '__main__':
    # 检测运行设备（优先使用 GPU 加速）
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    # 实例化模型并移至设备
    test_model = LeNet().to(device)
    # 打印模型结构和参数统计（输入尺寸：1×28×28）
    print(summary(test_model, (1, 28, 28)))
