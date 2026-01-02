

import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime  # 新增时间模块
from function import get_next_filename as filename
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image

"""
基于孪生网络的牛脸验证系统 - Model Iteration 8.5 (Speed Optimized)
优化点：
1. 降低单轮 Pair 数量至 10,000
2. 降低 Patience 至 5 (减少无效训练时间)
3. 日志增加时间戳，且不再覆盖打印
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
        label_counter = 0

        # 遍历目录，建立索引
        for cow_id in sorted(os.listdir(root_dir)):
            cow_dir = os.path.join(root_dir, cow_id)
            if not os.path.isdir(cow_dir):
                continue
            for img_name in os.listdir(cow_dir):
                self.image_paths.append(os.path.join(cow_dir, img_name))
                self.labels.append(label_counter)
            label_counter += 1

        self.num_classes = label_counter

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        return self.image_paths[idx], self.labels[idx]


def generate_pairs(image_paths, labels, num_pairs=30000):
    """
    在线生成配对数据
    """
    pairs = []
    pair_labels = []

    # 建立 label -> indices 的快速映射
    by_label = {}
    for idx, l in enumerate(labels):
        by_label.setdefault(l, []).append(idx)

    # 过滤掉只有1张图的类别
    valid_labels = [l for l, idxs in by_label.items() if len(idxs) >= 2]

    num_pos = num_pairs // 2
    num_neg = num_pairs - num_pos

    # 1. 生成正样本
    for _ in range(num_pos):
        lbl = random.choice(valid_labels)
        idx1, idx2 = random.sample(by_label[lbl], 2)
        pairs.append((image_paths[idx1], image_paths[idx2]))
        pair_labels.append(1)

    # 2. 生成负样本
    n = len(image_paths)
    for _ in range(num_neg):
        idx1 = random.randrange(n)
        idx2 = random.randrange(n)
        while labels[idx1] == labels[idx2]:
            idx2 = random.randrange(n)
        pairs.append((image_paths[idx1], image_paths[idx2]))
        pair_labels.append(0)

    # 打乱
    combined = list(zip(pairs, pair_labels))
    random.shuffle(combined)
    pairs, pair_labels = zip(*combined)

    return list(pairs), list(pair_labels)


class PairDataset(Dataset):
    """实际训练用的配对数据集"""

    def __init__(self, pairs, labels, transform=None):
        self.pairs = pairs
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        path1, path2 = self.pairs[idx]
        img1 = Image.open(path1).convert('RGB')
        img2 = Image.open(path2).convert('RGB')

        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)

        return img1, img2, torch.tensor(self.labels[idx], dtype=torch.float32)


# -----------------------------
# 网络架构 (ResNet50)
# -----------------------------

class EmbeddingNet(nn.Module):
    def __init__(self, emb_dim=256, pretrained=True):
        super().__init__()
        weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        # print(f"Loading ResNet50 weights: {weights}")
        resnet = models.resnet50(weights=weights)

        fc_input_dim = resnet.fc.in_features
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        # Projection Head
        self.fc = nn.Sequential(
            nn.Linear(fc_input_dim, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Linear(512, emb_dim)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        x = F.normalize(x, p=2, dim=1)
        return x


class SiameseModel(nn.Module):
    def __init__(self, emb_dim=256):
        super().__init__()
        self.embed_net = EmbeddingNet(emb_dim=emb_dim)

    def forward(self, x1, x2):
        e1 = self.embed_net(x1)
        e2 = self.embed_net(x2)
        return e1, e2


# -----------------------------
# 训练辅助函数
# -----------------------------

def contrastive_loss(e1, e2, label, margin=1.0):
    dist = F.pairwise_distance(e1, e2)
    loss_pos = label * torch.pow(dist, 2)
    loss_neg = (1 - label) * torch.pow(torch.clamp(margin - dist, min=0.0), 2)
    return (0.5 * (loss_pos + loss_neg)).mean()


def evaluate_and_find_threshold(model, dataloader, device):
    model.eval()
    total_loss = 0.0
    total_count = 0
    all_dists = []
    all_labels = []

    with torch.no_grad():
        for x1, x2, y in dataloader:
            x1, x2, y = x1.to(device), x2.to(device), y.to(device)
            e1, e2 = model(x1, x2)

            loss = contrastive_loss(e1, e2, y)
            total_loss += loss.item() * y.size(0)
            total_count += y.size(0)

            dist = F.pairwise_distance(e1, e2)
            all_dists.extend(dist.cpu().numpy())
            all_labels.extend(y.cpu().numpy())

    avg_loss = total_loss / (total_count + 1e-12)

    # 寻找最佳阈值
    all_dists = np.array(all_dists)
    all_labels = np.array(all_labels)

    best_acc = 0.0
    best_thresh = 0.8

    thresholds = np.arange(0.1, 2.5, 0.02)
    for t in thresholds:
        preds = (all_dists < t).astype(int)
        acc = (preds == all_labels).mean()
        if acc > best_acc:
            best_acc = acc
            best_thresh = t

    return avg_loss, best_acc, best_thresh


# -----------------------------
# 核心训练逻辑
# -----------------------------

def train(model, single_ds, val_loader, device, epochs=30, batch_size=112, train_transform=None):
    lr = 3e-4
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler('cuda')

    best_val_acc = 0.0
    best_thresh_record = 0.8
    patience = 5  # [优化] 降低耐心值，加速早停
    no_improve_count = 0

    save_path = 'model_train/' + filename('best_model', 'pth')

    print(f"开始训练 ResNet50 (快速版)... Batch Size: {batch_size}")
    print(f"模型将保存到: {save_path}")

    for epoch in range(1, epochs + 1):
        print(f"\n======== Epoch {epoch}/{epochs} ========")

        # [优化] 降低每轮的配对数量至 30000
        pairs_train, labels_train = generate_pairs(
            single_ds.image_paths, single_ds.labels, num_pairs=10000
        )

        train_ds = PairDataset(pairs_train, labels_train, transform=train_transform)
        train_loader = DataLoader(
            train_ds, batch_size=batch_size, shuffle=True,
            num_workers=4, pin_memory=True, persistent_workers=True
        )

        model.train()
        running_loss = 0.0
        processed_count = 0
        total_batches = len(train_loader)

        # 训练循环
        for batch_idx, (x1, x2, y) in enumerate(train_loader, 1):
            x1, x2, y = x1.to(device), x2.to(device), y.to(device)
            optimizer.zero_grad()

            with torch.amp.autocast('cuda'):
                e1, e2 = model(x1, x2)
                loss = contrastive_loss(e1, e2, y)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * y.size(0)
            processed_count += y.size(0)

            # [优化] 详细日志：带时间，换行打印
            if batch_idx % 50 == 0 or batch_idx == total_batches:
                curr_time = datetime.now().strftime("%H:%M:%S")
                avg_loss = running_loss / processed_count
                lr_curr = optimizer.param_groups[0]['lr']
                print(
                    f"[{curr_time}] Epoch {epoch} | Batch {batch_idx:3d}/{total_batches} | Avg Loss: {avg_loss:.4f} | LR: {lr_curr:.6f}")

        scheduler.step()

        # 验证与保存
        val_loss, val_acc, val_thresh = evaluate_and_find_threshold(model, val_loader, device)
        train_loss_avg = running_loss / (processed_count + 1e-12)

        print(f"-------- Epoch {epoch} 结果 --------")
        print(f"Train Loss: {train_loss_avg:.4f}")
        print(f"Val Loss  : {val_loss:.4f}")
        print(f"Val Acc   : {val_acc:.4f} (Best Thresh: {val_thresh:.3f})")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_thresh_record = val_thresh
            no_improve_count = 0
            torch.save(model.state_dict(), save_path)
            print(f"🔥 最佳模型已保存! Acc: {best_val_acc:.4f}")
        else:
            no_improve_count += 1
            print(f"⚠️ 无提升 ({no_improve_count}/{patience})")
            if no_improve_count >= patience:
                print("🛑 触发早停 (Early Stopping)")
                break

    print(f"\n训练结束。历史最佳验证准确率: {best_val_acc:.4f}")
    print(f"!!! 最终推荐阈值: {best_thresh_record:.3f} !!!")
    return model, best_thresh_record


# -----------------------------
# 预测函数
# -----------------------------

def predict_pairs(model, test_pairs, device, transform, batch_size=64, threshold=0.8, tta=True):
    model.eval()
    ds = PairDataset(test_pairs, [0] * len(test_pairs), transform=transform)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=4)

    preds = []
    print(f"开始推理... Threshold={threshold}, TTA={tta}")

    with torch.no_grad():
        for x1, x2, _ in loader:
            x1, x2 = x1.to(device), x2.to(device)

            e1, e2 = model(x1, x2)
            dist = F.pairwise_distance(e1, e2)

            if tta:
                x1_f = torch.flip(x1, [3])
                x2_f = torch.flip(x2, [3])
                e1_f, e2_f = model(x1_f, x2_f)
                dist_f = F.pairwise_distance(e1_f, e2_f)
                dist = (dist + dist_f) / 2.0

            batch_preds = (dist < threshold).cpu().numpy().astype(int).tolist()
            preds.extend(batch_preds)

    return preds


# -----------------------------
# 入口
# -----------------------------

def main_train(model_path=None, train_epochs=50, train_dir='cowface-verification-U/train/train'):
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    os.makedirs('model_train', exist_ok=True)

    print(f"Training on Device: {device}")

    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.5, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.RandomAffine(degrees=15, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.3)
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    print("索引数据集...")
    single_ds = CowFaceDatasetSingle(train_dir)
    print(f"共发现 {len(single_ds)} 张图片, {single_ds.num_classes} 个类别")

    print("生成固定验证集 (4000对)...")
    val_pairs, val_labels = generate_pairs(single_ds.image_paths, single_ds.labels, num_pairs=4000)
    val_ds = PairDataset(val_pairs, val_labels, transform=val_transform)
    val_loader = DataLoader(val_ds, batch_size=112, shuffle=False, num_workers=4)

    model = SiameseModel(emb_dim=256).to(device)
    if model_path and os.path.exists(model_path):
        print(f"Loading checkpoint: {model_path}")
        model.load_state_dict(torch.load(model_path, map_location=device))

    # [优化] 调用训练函数
    model, best_thresh = train(
        model, single_ds, val_loader, device,
        epochs=train_epochs,
        batch_size=112,
        train_transform=train_transform
    )

    return model, best_thresh


def main_predict(model_path=None, test_csv_path=None, test_dir_path=None, output_name='submission', threshold=None):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Predict Device: {device}")

    if test_csv_path is None: test_csv_path = 'cowface-verification-U/test-1118.csv'
    if test_dir_path is None: test_dir_path = 'cowface-verification-U/test/test'

    if model_path is None:
        search_dir = 'model_train' if os.path.exists('model_train') else '.'
        files = [f for f in os.listdir(search_dir) if f.endswith('.pth') and 'best_model' in f]
        if files:
            files.sort(key=lambda x: os.path.getmtime(os.path.join(search_dir, x)), reverse=True)
            model_path = os.path.join(search_dir, files[0])
            print(f"Auto-selected model: {model_path}")
        else:
            print("Error: No model found.")
            return

    if threshold is None:
        print("Warning: No threshold provided. Using default 0.8.")
        threshold = 0.8
    else:
        print(f"Using Best Threshold: {threshold}")

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    model = SiameseModel(emb_dim=256).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))

    test_df = pd.read_csv(test_csv_path)
    pairs_list = []
    ids = test_df['ID_ID'].tolist()
    for s in ids:
        a, b = s.split('_')
        pairs_list.append((
            os.path.join(test_dir_path, f"{a}.jpg"),
            os.path.join(test_dir_path, f"{b}.jpg")
        ))

    preds = predict_pairs(model, pairs_list, device, val_transform, batch_size=64, threshold=threshold, tta=True)

    sub_df = pd.DataFrame({'ID_ID': ids, 'TARGET': preds})
    out = filename(output_name, 'csv')
    sub_df.to_csv(out, index=False)
    print(f"Done. Saved to {out}")


if __name__ == '__main__':
    pass