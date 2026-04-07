"""
Fashion-MNIST 数据集下载与样本可视化

从 torchvision 自动下载 Fashion-MNIST 数据集，
并展示第一个 batch 的 64 张样本图像及其类别标签。

注意：
    - 本脚本仅用于数据可视化，图像被放大到 224×224 以便观察细节
    - 实际训练使用 28×28 原始尺寸
    - 文件名为 polt.py（非拼写错误，保留原始命名）

运行方式：
    python polt.py

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 添加模块文档字符串和详细中文注释
"""

from torchvision.datasets import FashionMNIST
from torchvision import transforms
import torch.utils.data as Data
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # 强制使用 TkAgg 后端（高版本 matplotlib 兼容）
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Windows 多进程兼容：防止 DataLoader 在 Windows 上因 fork 方法报错
    import multiprocessing
    multiprocessing.freeze_support()

    # 下载 Fashion-MNIST 训练集
    # 图像放大到 224×224 仅用于可视化展示，训练时使用 28×28
    train_data = FashionMNIST(root='./data',
                              train=True,
                              transform=transforms.Compose([
                                  transforms.Resize(size=224),
                                  transforms.ToTensor()
                              ]),
                              download=True)

    # 按批次加载：每批 64 张图，打乱顺序，4个进程并行加载
    train_loader = Data.DataLoader(dataset=train_data,
                                   batch_size=64,
                                   shuffle=True,
                                   num_workers=4)

    # 仅获取第一个 batch 的数据用于可视化
    for step, (b_x, b_y) in enumerate(train_loader):
        if step > 0:
            break

    # 移除通道维度：(64, 1, 224, 224) → (64, 224, 224)，转为 NumPy 数组
    batch_x = b_x.squeeze().numpy()
    batch_y = b_y.numpy()
    class_label = train_data.classes
    # 类别列表: ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
    #           'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

    # 可视化：4行 × 16列 = 64 张图像
    plt.figure(figsize=(12, 5))
    for ii in np.arange(len(batch_y)):
        plt.subplot(4, 16, ii + 1)
        plt.imshow(batch_x[ii, :, :], 'gray')
        plt.title(class_label[batch_y[ii]], size=10)
        plt.axis("off")
        plt.subplots_adjust(wspace=0.05)
    plt.show()
