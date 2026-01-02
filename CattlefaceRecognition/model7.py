

import os
import random
import math
import numpy as np
import pandas as pd
from pathlib import Path
from function import get_next_filename as filename
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split

"""
基于孪生网络的牛脸验证系统 - Model Iteration 7
改进点：
1. 动态阈值搜索 (Dynamic Threshold Search)
2. 在线配对挖掘 (Online Pair Mining / Re-generation per Epoch)
3. 基于准确率的模型保存机制
4. 测试时增强 (TTA)
"""


# -----------------------------
# 数据集与配对生成
# -----------------------------

class CowFaceDatasetSingle(Dataset):
    """单张图像数据集（用于生成配对）"""

    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []
        self.labels = []
        self.cow_id_to_label = {}
        label_counter = 0

        for cow_id in sorted(os.listdir(root_dir)):
            cow_dir = os.path.join(root_dir, cow_id)
            if not os.path.isdir(cow_dir):
                continue

            self.cow_id_to_label[cow_id] = label_counter

            for img_name in os.listdir(cow_dir):
                self.image_paths.append(os.path.join(cow_dir, img_name))
                self.labels.append(label_counter)

            label_counter += 1

        self.num_classes = label_counter

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        path = self.image_paths[idx]
        img = Image.open(path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        lbl = self.labels[idx]
        return img, lbl, path


def generate_pairs(image_paths, labels, num_pairs=50000):
    """生成正负样本对"""
    pairs = []
    pair_labels = []
    n = len(image_paths)

    # 按标签组织索引
    by_label = {}
    for idx, l in enumerate(labels):
        by_label.setdefault(l, []).append(idx)

    num_pos = num_pairs // 2
    num_neg = num_pairs - num_pos

    # print(f"  [数据生成] 正样本: {num_pos}, 负样本: {num_neg}")

    # 正样本生成
    valid_labels = [l for l, idxs in by_label.items() if len(idxs) >= 2]
    for _ in range(num_pos):
        lbl = random.choice(valid_labels)
        a, b = random.sample(by_label[lbl], 2)
        pairs.append((image_paths[a], image_paths[b]))
        pair_labels.append(1)

    # 负样本生成
    for _ in range(num_neg):
        a = random.randrange(n)
        b = random.randrange(n)
        while labels[a] == labels[b]:
            b = random.randrange(n)
        pairs.append((image_paths[a], image_paths[b]))
        pair_labels.append(0)

    combined = list(zip(pairs, pair_labels))
    random.shuffle(combined)
    pairs, pair_labels = zip(*combined)

    return list(pairs), list(pair_labels)


class PairDataset(Dataset):
    """配对数据集类"""

    def __init__(self, pairs, labels, transform=None):
        self.pairs = pairs
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        p = self.pairs[idx]
        img1 = Image.open(p[0]).convert('RGB')
        img2 = Image.open(p[1]).convert('RGB')

        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)

        lbl = torch.tensor(self.labels[idx], dtype=torch.float32)
        return img1, img2, lbl


# -----------------------------
# 网络架构
# -----------------------------

class EmbeddingNet(nn.Module):
    def __init__(self, emb_dim=128, pretrained=True):
        super().__init__()
        # ResNet18 backbone
        resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        # Projection Head
        self.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, emb_dim)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        x = F.normalize(x, p=2, dim=1)  # L2 Normalize
        return x


class SiameseModel(nn.Module):
    def __init__(self, emb_dim=128):
        super().__init__()
        self.embed_net = EmbeddingNet(emb_dim=emb_dim)

    def forward(self, x1, x2):
        e1 = self.embed_net(x1)
        e2 = self.embed_net(x2)
        return e1, e2


# -----------------------------
# 损失函数 & 评估工具
# -----------------------------

def contrastive_loss(e1, e2, label, margin=1.0):
    dist = F.pairwise_distance(e1, e2, keepdim=False)
    loss_pos = label * torch.pow(dist, 2)
    loss_neg = (1 - label) * torch.pow(torch.clamp(margin - dist, min=0.0), 2)
    loss = 0.5 * (loss_pos + loss_neg)
    return loss.mean()


def find_best_threshold(distances, labels, thresholds):
    """
    给定距离和真实标签，遍历阈值列表，找到准确率最高的阈值
    """
    best_acc = 0
    best_thresh = 0.5

    # 转换为 numpy 数组以加速计算
    distances = np.array(distances)
    labels = np.array(labels)

    for thresh in thresholds:
        # 距离 < 阈值 => 预测为1 (同类)
        predictions = (distances < thresh).astype(int)
        accuracy = (predictions == labels).mean()

        if accuracy > best_acc:
            best_acc = accuracy
            best_thresh = thresh

    return best_acc, best_thresh


def evaluate(model, dataloader, device):
    """验证函数：计算Loss并寻找最佳阈值"""
    model.eval()
    total_loss = 0.0
    total = 0

    all_dists = []
    all_labels = []

    with torch.no_grad():
        for x1, x2, y in dataloader:
            x1 = x1.to(device)
            x2 = x2.to(device)
            y = y.to(device)

            e1, e2 = model(x1, x2)
            loss = contrastive_loss(e1, e2, y)

            # 记录距离和标签
            dist = F.pairwise_distance(e1, e2, keepdim=False)
            all_dists.extend(dist.cpu().numpy().tolist())
            all_labels.extend(y.cpu().numpy().astype(int).tolist())

            total_loss += loss.item() * y.size(0)
            total += y.size(0)

    avg_loss = total_loss / (total + 1e-12)

    # 搜索最佳阈值 (0.1 ~ 3.0)
    thresholds = [x / 100.0 for x in range(10, 300, 2)]
    best_acc, best_thresh = find_best_threshold(all_dists, all_labels, thresholds)

    return avg_loss, best_acc, best_thresh


# -----------------------------
# 训练流程
# -----------------------------

def train(model, single_ds, val_loader, device, epochs=30, lr=3e-4, weight_decay=1e-4, train_transform=None):
    """
    Args:
        single_ds: 包含所有训练图片的Dataset，用于每轮重新生成配对
    """
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler('cuda') if device.type == 'cuda' else None

    # 状态记录
    best_val_acc = 0.0
    best_threshold_record = 0.8
    patience = 8
    counter = 0

    best_model_filename = filename('best_model', 'pth')

    print(f"训练开始。模型将根据 [验证集准确率] 保存至 {best_model_filename}")

    for epoch in range(1, epochs + 1):
        print(f"\n=== Epoch {epoch}/{epochs} ===")

        # --- 关键改进：每轮重新生成训练数据 ---
        # 增加 num_pairs 让模型看到更多组合 (建议 50000 - 100000)
        current_num_pairs = 60000
        pairs, labels = generate_pairs(single_ds.image_paths, single_ds.labels, num_pairs=current_num_pairs)

        train_ds = PairDataset(pairs, labels, transform=train_transform)
        train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=4, pin_memory=True)
        # -----------------------------------

        model.train()
        running_loss = 0.0
        total = 0
        total_batches = len(train_loader)

        for batch_idx, (x1, x2, y) in enumerate(train_loader, 1):
            x1 = x1.to(device)
            x2 = x2.to(device)
            y = y.to(device)

            optimizer.zero_grad()

            if scaler is not None:
                with torch.amp.autocast('cuda'):
                    e1, e2 = model(x1, x2)
                    loss = contrastive_loss(e1, e2, y)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                e1, e2 = model(x1, x2)
                loss = contrastive_loss(e1, e2, y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

            running_loss += loss.item() * y.size(0)
            total += y.size(0)

            if batch_idx % 100 == 0:
                print(
                    f"\r  Batch {batch_idx}/{total_batches} | Loss: {running_loss / total:.4f} | LR: {optimizer.param_groups[0]['lr']:.6f}",
                    end="")

        scheduler.step()

        # 验证阶段
        val_loss, val_acc, val_thresh = evaluate(model, val_loader, device)

        print(f"\n  [Epoch {epoch} 总结]")
        print(f"  训练损失: {running_loss / total:.4f}")
        print(f"  验证损失: {val_loss:.4f}")
        print(f"  验证准确率: {val_acc:.4f} (最佳阈值: {val_thresh:.2f})")

        # 保存策略：基于 Accuracy
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_threshold_record = val_thresh
            counter = 0
            torch.save(model.state_dict(), 'model_train/' + best_model_filename)
            print(f"  >>> 最佳模型已保存! Acc: {val_acc:.4f}, Thresh: {val_thresh:.2f}")
        else:
            counter += 1
            print(f"  无提升 ({counter}/{patience})")
            if counter >= patience:
                print("  Early Stopping Triggered.")
                break

    print(f"\n训练结束。")
    print(f"历史最佳验证准确率: {best_val_acc:.4f}")
    print(f"建议推理阈值 (Threshold): {best_threshold_record}")
    print(f"!!! 请务必记录上述阈值，并在预测时填入 main_predict 函数 !!!")

    return model, best_threshold_record


# -----------------------------
# 预测函数
# -----------------------------

def predict_pairs(model, test_pairs, device, transform, batch_size=64, threshold=0.8, tta=True):
    """
    预测函数
    Args:
        threshold: 判定阈值，建议使用训练结束时输出的 best_thresh
        tta: Test Time Augmentation, 是否开启水平翻转增强 (默认True)
    """
    model.eval()
    # 标签填0即可，仅用于占位
    ds = PairDataset(test_pairs, [0] * len(test_pairs), transform=transform)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=4)

    preds = []

    print(f"开始推理 (Threshold={threshold}, TTA={'On' if tta else 'Off'})...")

    with torch.no_grad():
        for x1, x2, _ in loader:
            x1 = x1.to(device)
            x2 = x2.to(device)

            # 原始预测
            e1, e2 = model(x1, x2)
            dist = F.pairwise_distance(e1, e2)

            # TTA (测试时增强): 计算翻转后的距离并取平均
            if tta:
                x1_flip = torch.flip(x1, [3])  # 水平翻转
                x2_flip = torch.flip(x2, [3])
                e1_f, e2_f = model(x1_flip, x2_flip)
                dist_f = F.pairwise_distance(e1_f, e2_f)
                dist = (dist + dist_f) / 2.0

            # 根据阈值生成 0/1
            batch_preds = (dist < threshold).cpu().numpy().astype(int).tolist()
            preds.extend(batch_preds)

    return preds


# -----------------------------
# 主入口函数
# -----------------------------

def main_train(model_path=None, train_epochs=35, train_dir='cowface-verification-U/train/train'):
    # 设置随机种子
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("Device:", device)

    # 确保保存目录存在
    os.makedirs('model_train', exist_ok=True)

    # 强数据增强
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.5, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.3, scale=(0.02, 0.15))
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 1. 加载单张图像数据 (Index)
    print("正在索引训练集图像...")
    single_ds = CowFaceDatasetSingle(train_dir, transform=None)
    print(f"索引完成: {len(single_ds)} 张图片, {single_ds.num_classes} 个类别.")

    # 2. 生成固定的验证集 (Fixed Validation Set)
    # 为了验证曲线的稳定性，我们先从库中划分出一部分不做训练，或者简单的生成一批固定的Pair作为验证
    # 这里采用生成固定配对的方式
    print("生成固定验证集配对 (5000对)...")
    val_pairs, val_labels = generate_pairs(single_ds.image_paths, single_ds.labels, num_pairs=5000)
    val_ds = PairDataset(val_pairs, val_labels, transform=val_transform)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=4)

    # 3. 初始化模型
    model = SiameseModel(emb_dim=128).to(device)

    if model_path and os.path.exists(model_path):
        print(f"加载预训练模型: {model_path}")
        model.load_state_dict(torch.load(model_path, map_location=device))

    # 4. 开始训练
    # 注意：我们把 single_ds 传进去，train 函数内部会每轮动态生成训练配对
    model, best_thresh = train(model, single_ds, val_loader, device,
                               epochs=train_epochs,
                               train_transform=train_transform)

    return model, best_thresh


def main_predict(model_path=None, test_csv_path=None, test_dir_path=None, output_name='submission', threshold=None):
    """
    预测主函数
    Args:
        threshold: (重要) 必须填入训练时得到的最佳阈值，否则默认 0.8 可能不准
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Predict Device: {device}")

    # 默认参数处理
    if test_csv_path is None:
        test_csv_path = 'cowface-verification-U/test-1118.csv'
    if test_dir_path is None:
        test_dir_path = 'cowface-verification-U/test/test'

    # 自动查找最新模型
    if model_path is None:
        if os.path.exists('model_train'):
            search_dir = 'model_train'
        else:
            search_dir = '.'
        model_files = [f for f in os.listdir(search_dir) if f.endswith('.pth') and ('model' in f)]
        if model_files:
            model_files.sort(key=lambda x: os.path.getmtime(os.path.join(search_dir, x)), reverse=True)
            model_path = os.path.join(search_dir, model_files[0])
            print(f"自动选择最新模型: {model_path}")
        else:
            print("未找到模型文件。")
            return

    # 阈值检查
    if threshold is None:
        print("\n!!!!! 警告: 未指定 threshold (阈值) !!!!!")
        print("默认使用 0.8，但这可能不是最优的。请查看训练日志中的 '建议推理阈值'。")
        threshold = 0.8
    else:
        print(f"使用指定阈值: {threshold}")

    # 数据变换
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 加载模型
    model = SiameseModel(emb_dim=128).to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)

    # 读取CSV
    test_df = pd.read_csv(test_csv_path)
    test_pairs_str = test_df['ID_ID'].tolist()

    # 构建路径列表
    test_pairs = []
    for s in test_pairs_str:
        a, b = s.split('_')
        # 兼容可能的后缀差异
        p1 = os.path.join(test_dir_path, f"{a}.jpg")
        p2 = os.path.join(test_dir_path, f"{b}.jpg")
        test_pairs.append((p1, p2))

    # 执行预测 (开启 TTA)
    preds = predict_pairs(model, test_pairs, device, val_transform,
                          batch_size=64, threshold=threshold, tta=True)

    # 保存
    sub_df = pd.DataFrame({'ID_ID': test_pairs_str, 'TARGET': preds})
    out_file = filename(output_name, 'csv')
    sub_df.to_csv(out_file, index=False)
    print(f"预测完成，结果已保存至: {out_file}")


if __name__ == '__main__':
    # --- 训练阶段 ---
    # 1. 运行训练，留意控制台最后输出的 Best Threshold
    # trained_model, best_thresh = main_train(train_epochs=40)

    # --- 预测阶段 ---
    # 2. 将得到的阈值填入下面 (例如 threshold=0.65)
    # 取消注释并修改 threshold 即可运行预测

    # main_predict(
    #     model_path='model_train/best_model_01.pth',  # 你的模型路径
    #     threshold=0.8,  # <--- 在这里填入训练得到的最佳阈值
    #     output_name='submission_tta'
    # )
    pass