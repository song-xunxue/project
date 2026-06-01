"""
RepViT-M0.6 在 Fashion-MNIST 上的测试脚本

测试内容:
  - 总体准确率和各类别准确率
  - 混淆矩阵
  - 与 LeNet-5 的对比（加载实验三的模型）

李文煜 1120233042
"""

import os
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np

from model import repvit_m0_6


# Fashion-MNIST 类别名
CLASS_NAMES = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']


def test_repvit(model_path, data_dir, batch_size=128):
    """测试 RepViT 模型"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载模型
    model = repvit_m0_6(in_channels=1, num_classes=10).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    # 测试数据（不做增强）
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ])
    test_dataset = datasets.FashionMNIST(
        root=data_dir, train=False, download=True, transform=transform)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # 总体准确率
    total_acc = (all_preds == all_labels).mean()
    print(f"RepViT-M0.6 测试准确率: {total_acc*100:.2f}% ({(all_preds == all_labels).sum()}/{len(all_labels)})")

    # 各类别准确率
    print(f"\n各类别准确率:")
    class_acc = {}
    for i, name in enumerate(CLASS_NAMES):
        mask = all_labels == i
        acc = (all_preds[mask] == all_labels[mask]).mean()
        class_acc[name] = acc
        print(f"  {name:15s}: {acc*100:.2f}%")

    # 混淆矩阵
    cm = confusion_matrix(all_labels, all_preds)
    print(f"\n混淆矩阵:")
    print(f"{'':>15s}", end='')
    for name in CLASS_NAMES:
        print(f"{name[:6]:>7s}", end='')
    print()
    for i, name in enumerate(CLASS_NAMES):
        print(f"{name:>15s}", end='')
        for j in range(10):
            print(f"{cm[i][j]:>7d}", end='')
        print()

    # 分类报告
    report = classification_report(all_labels, all_preds, target_names=CLASS_NAMES, digits=4)
    print(f"\n分类报告:\n{report}")

    # 保存结果
    results = {
        'model': 'RepViT-M0.6',
        'total_accuracy': float(total_acc),
        'class_accuracy': {k: float(v) for k, v in class_acc.items()},
        'confusion_matrix': cm.tolist()
    }

    save_dir = os.path.dirname(model_path)
    results_path = os.path.join(save_dir, 'test_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n结果已保存至: {results_path}")

    return results


if __name__ == '__main__':
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, 'best_model.pth')
    data_dir = os.path.join(base_dir, 'data')
    test_repvit(model_path, data_dir)
