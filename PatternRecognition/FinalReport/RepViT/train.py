"""
RepViT-M0.6 在 Fashion-MNIST 上的训练脚本

训练配置:
  - 优化器: AdamW (lr=1e-3, weight_decay=0.02)
  - 学习率调度: CosineAnnealingLR
  - 数据增强: RandomHorizontalFlip, RandomCrop
  - 训练轮次: 30 epochs
  - 批大小: 128

李文煜 1120233042
"""

import os
import sys
import json
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import repvit_m0_6


def get_dataloaders(data_dir, batch_size=128):
    """获取 Fashion-MNIST 数据加载器"""
    # 训练集数据增强
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(),    # 随机水平翻转
        transforms.RandomCrop(28, padding=4), # 随机裁剪（先填充4像素再裁回28）
        transforms.ToTensor(),                # 转为张量 [0,1]
        transforms.Normalize([0.5], [0.5]),   # 归一化到 [-1,1]
    ])
    # 测试集不做增强
    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ])

    train_dataset = datasets.FashionMNIST(
        root=data_dir, train=True, download=True, transform=train_transform)
    test_dataset = datasets.FashionMNIST(
        root=data_dir, train=False, download=True, transform=test_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, test_loader


def train_one_epoch(model, loader, criterion, optimizer, device):
    """训练一个 epoch"""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    """评估模型"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}")

    # 超参数
    batch_size = 128
    epochs = 30
    lr = 1e-3
    weight_decay = 0.02
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    save_dir = os.path.dirname(__file__)

    # 数据
    train_loader, test_loader = get_dataloaders(data_dir, batch_size)
    print(f"训练集: {len(train_loader.dataset)} 张, 测试集: {len(test_loader.dataset)} 张")

    # 模型
    model = repvit_m0_6(in_channels=1, num_classes=10).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"RepViT-M0.6 参数量: {total_params:,}")

    # 损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # 训练记录
    history = {
        'train_loss': [], 'train_acc': [],
        'test_loss': [], 'test_acc': [],
        'lr': []
    }
    best_acc = 0.0

    print(f"\n{'='*60}")
    print(f"开始训练: {epochs} epochs, batch_size={batch_size}, lr={lr}")
    print(f"{'='*60}")

    for epoch in range(1, epochs + 1):
        start = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        test_loss, test_acc = evaluate(model, test_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - start
        current_lr = optimizer.param_groups[0]['lr']

        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['test_loss'].append(test_loss)
        history['test_acc'].append(test_acc)
        history['lr'].append(current_lr)

        # 保存最优模型
        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), os.path.join(save_dir, 'best_model.pth'))

        print(f"Epoch [{epoch:2d}/{epochs}] "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.2f}% | "
              f"Test Loss: {test_loss:.4f} Acc: {test_acc*100:.2f}% | "
              f"LR: {current_lr:.6f} | Time: {elapsed:.1f}s")

    print(f"\n{'='*60}")
    print(f"训练完成! 最佳测试准确率: {best_acc*100:.2f}%")
    print(f"模型已保存至: {os.path.join(save_dir, 'best_model.pth')}")
    print(f"{'='*60}")

    # 保存训练历史
    history_path = os.path.join(save_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"训练历史已保存至: {history_path}")


if __name__ == '__main__':
    main()
