import os
import random
import time
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
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
基于 ArcFace 的牛脸识别系统 - Model Iteration 10.1 (Stable & Log Fix)
修复与改进：
1. [严重] 修复 Loss: nan 问题 (增加 cosine.clamp 防止数值溢出)。
2. [优化] 日志格式对齐之前的风格，显示 LR、Loss、Acc、Speed。
3. [架构] 保持 ResNet50 + ArcFace + AdamW。
"""


# -----------------------------
# 1. 数据集
# -----------------------------

class CowFaceClassificationDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        path = self.image_paths[idx]
        label = self.labels[idx]
        try:
            img = Image.open(path).convert('RGB')
            if self.transform:
                img = self.transform(img)
        except Exception as e:
            print(f"Error loading: {path}")
            img = torch.zeros((3, 224, 224))
        return img, label


def load_data_and_split(root_dir):
    image_paths = []
    labels = []
    label_counter = 0

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在扫描数据集: {root_dir} ...")
    for cow_id in sorted(os.listdir(root_dir)):
        cow_dir = os.path.join(root_dir, cow_id)
        if not os.path.isdir(cow_dir):
            continue
        for img_name in os.listdir(cow_dir):
            image_paths.append(os.path.join(cow_dir, img_name))
            labels.append(label_counter)
        label_counter += 1

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 扫描完成: {len(image_paths)} 图, {label_counter} 类。")

    try:
        X_train, X_val, y_train, y_val = train_test_split(
            image_paths, labels, test_size=0.1, random_state=42, stratify=labels
        )
    except ValueError:
        print("⚠️ 警告：无法分层划分，使用随机划分。")
        X_train, X_val, y_train, y_val = train_test_split(
            image_paths, labels, test_size=0.1, random_state=42
        )

    return X_train, y_train, X_val, y_val, label_counter


# -----------------------------
# 2. ArcFace (稳定性修复版)
# -----------------------------

class ArcMarginProduct(nn.Module):
    def __init__(self, in_features, out_features, s=30.0, m=0.50, easy_margin=False):
        super(ArcMarginProduct, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)

        self.easy_margin = easy_margin
        self.cos_m = np.cos(m)
        self.sin_m = np.sin(m)
        self.th = np.cos(np.pi - m)
        self.mm = np.sin(np.pi - m) * m

    def forward(self, input, label):
        # 强制 FP32 以保证数值精度
        input = input.float()
        weight = self.weight.float()

        # 1. Cosine
        cosine = F.linear(F.normalize(input), F.normalize(weight))

        # --- 关键修复: 防止 acos/sqrt 出现 nan ---
        cosine = cosine.clamp(-1.0 + 1e-7, 1.0 - 1e-7)
        # ---------------------------------------

        # 2. Sine
        sine = torch.sqrt(1.0 - torch.pow(cosine, 2))

        # 3. Phi
        phi = cosine * self.cos_m - sine * self.sin_m

        if self.easy_margin:
            phi = torch.where(cosine > 0, phi, cosine)
        else:
            phi = torch.where(cosine > self.th, phi, cosine - self.mm)

        # 4. Output
        one_hot = torch.zeros_like(cosine)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1)

        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s

        return output


class CowFaceResNet50(nn.Module):
    def __init__(self, num_classes, emb_dim=512, pretrained=True):
        super(CowFaceResNet50, self).__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        self.bn1 = nn.BatchNorm1d(2048)
        self.dropout = nn.Dropout(0.4)
        self.fc = nn.Linear(2048, emb_dim)
        self.bn2 = nn.BatchNorm1d(emb_dim)

        self.arcface = ArcMarginProduct(emb_dim, num_classes, s=30.0, m=0.50)

    def forward(self, x, label=None):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        x = self.bn1(x)
        x = self.dropout(x)
        x = self.fc(x)
        x = self.bn2(x)

        if label is not None:
            return self.arcface(x, label)
        return F.normalize(x, p=2, dim=1)


# -----------------------------
# 3. 验证逻辑
# -----------------------------

def evaluate_verification(model, val_loader, device):
    model.eval()
    feats, labels = [], []
    with torch.no_grad():
        for img, label in val_loader:
            img = img.to(device)
            feat = model(img)
            feats.append(feat.cpu())
            labels.append(label)
    feats = torch.cat(feats, dim=0)
    labels = torch.cat(labels, dim=0)

    # 采样验证
    n = len(labels)
    label_to_idx = {}
    for i, l in enumerate(labels.tolist()):
        label_to_idx.setdefault(l, []).append(i)

    valid_classes = [l for l, idxs in label_to_idx.items() if len(idxs) >= 2]
    sims, targets = [], []

    # 3000 正样本
    for _ in range(3000):
        if not valid_classes: break
        cls = random.choice(valid_classes)
        idx1, idx2 = random.sample(label_to_idx[cls], 2)
        sim = F.cosine_similarity(feats[idx1].unsqueeze(0), feats[idx2].unsqueeze(0)).item()
        sims.append(sim)
        targets.append(1)

    # 3000 负样本
    for _ in range(3000):
        idx1, idx2 = random.randint(0, n - 1), random.randint(0, n - 1)
        while labels[idx1] == labels[idx2]: idx2 = random.randint(0, n - 1)
        sim = F.cosine_similarity(feats[idx1].unsqueeze(0), feats[idx2].unsqueeze(0)).item()
        sims.append(sim)
        targets.append(0)

    best_acc, best_thresh = 0, 0.5
    sims, targets = np.array(sims), np.array(targets)
    for th in np.arange(0.1, 0.9, 0.01):
        acc = ((sims > th).astype(int) == targets).mean()
        if acc > best_acc: best_acc, best_thresh = acc, th

    return best_acc, best_thresh


# -----------------------------
# 4. 训练循环 (日志格式已修复)
# -----------------------------

def train(model, train_loader, val_loader, device, epochs=30):
    optimizer = optim.AdamW([
        {'params': model.backbone.parameters(), 'lr': 1e-4},
        {'params': model.fc.parameters(), 'lr': 3e-4},
        {'params': model.arcface.parameters(), 'lr': 3e-4}
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scaler = torch.amp.GradScaler('cuda')

    best_val_acc = 0.0
    best_thresh = 0.5
    save_path = 'model_train/' + filename('best_model', 'pth')

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ArcFace (FP32 Fix) 训练开始... Epochs: {epochs}")

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        processed_count = 0  # 记录样本数用于准确计算 avg loss

        last_log_time = time.time()

        for batch_idx, (img, label) in enumerate(train_loader, 1):
            img, label = img.to(device), label.to(device)
            optimizer.zero_grad()

            with torch.amp.autocast('cuda'):
                outputs = model(img, label)
                loss = criterion(outputs, label)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5)
            scaler.step(optimizer)
            scaler.update()

            # 统计
            bs = label.size(0)
            running_loss += loss.item() * bs
            _, predicted = outputs.max(1)
            total += bs
            correct += predicted.eq(label).sum().item()
            processed_count += bs

            # --- 修复后的日志格式 ---
            if batch_idx % 20 == 0 or batch_idx == len(train_loader):
                elapsed = time.time() - last_log_time
                speed = elapsed / 20 if batch_idx > 20 else elapsed / batch_idx
                last_log_time = time.time()

                curr_lr = optimizer.param_groups[0]['lr']
                avg_loss = running_loss / processed_count
                curr_acc = 100. * correct / total
                time_str = datetime.now().strftime('%H:%M:%S')

                print(f"[{time_str}] Epoch {epoch} | Batch {batch_idx:3d}/{len(train_loader)} | "
                      f"Loss: {avg_loss:.4f} | Acc: {curr_acc:.2f}% | "
                      f"LR: {curr_lr:.6f} | {speed:.3f} s/it")

        scheduler.step()

        # 验证
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在验证...")
        val_acc, thresh = evaluate_verification(model, val_loader, device)

        print(f"=== Epoch {epoch} Result ===")
        print(f"Train Acc : {100. * correct / total:.2f}%")
        print(f"Val Acc   : {val_acc:.4f} (Thresh: {thresh:.2f})")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_thresh = thresh
            torch.save(model.state_dict(), save_path)
            print(f"🔥 Best Model Saved!")
        print("========================\n")

    return model, best_thresh


# -----------------------------
# 5. 入口
# -----------------------------

def main_train(model_path=None, train_epochs=30, train_dir='cowface-verification-U/train/train'):
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device('cuda')
    os.makedirs('model_train', exist_ok=True)

    X_train, y_train, X_val, y_val, num_classes = load_data_and_split(train_dir)

    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.3, 0.3, 0.3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2)
    ])
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    train_ds = CowFaceClassificationDataset(X_train, y_train, transform=train_transform)
    val_ds = CowFaceClassificationDataset(X_val, y_val, transform=val_transform)

    # drop_last=True 防止 batchnorm 报错
    train_loader = DataLoader(train_ds, batch_size=48, shuffle=True, num_workers=4, pin_memory=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=4)

    print(f"Initializing Model (FP32 Head Fix)...")
    model = CowFaceResNet50(num_classes=num_classes, emb_dim=512).to(device)

    model, best_thresh = train(model, train_loader, val_loader, device, epochs=train_epochs)
    return model, best_thresh


def main_predict(model_path=None, test_csv_path=None, test_dir_path=None, output_name='submission', threshold=0.3):
    device = torch.device('cuda')

    if model_path is None:
        search_dir = 'model_train'
        files = [f for f in os.listdir(search_dir) if f.endswith('.pth') and 'best_model' in f]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(search_dir, x)), reverse=True)
        model_path = os.path.join(search_dir, files[0])

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading Model: {model_path} (Thresh: {threshold})")

    label_counter = 5503
    if os.path.exists('cowface-verification-U/train/train'):
        dirs = [d for d in os.listdir('cowface-verification-U/train/train') if
                os.path.isdir(os.path.join('cowface-verification-U/train/train', d))]
        if len(dirs) > 0: label_counter = len(dirs)

    model = CowFaceResNet50(num_classes=label_counter, emb_dim=512).to(device)

    try:
        model.load_state_dict(torch.load(model_path))
    except:
        state = torch.load(model_path)
        model_dict = model.state_dict()
        pretrained = {k: v for k, v in state.items() if k in model_dict and v.size() == model_dict[k].size()}
        model_dict.update(pretrained)
        model.load_state_dict(model_dict)

    model.eval()

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    test_df = pd.read_csv(test_csv_path)
    ids = test_df['ID_ID'].tolist()
    preds = []

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Predicting with Thresh={threshold}...")

    with torch.no_grad():
        for i, pair_str in enumerate(ids):
            a, b = pair_str.split('_')
            p1, p2 = None, None
            for ext in ['.jpg', '.JPG', '.png']:
                t1 = os.path.join(test_dir_path, a + ext)
                if os.path.exists(t1): p1 = t1
                t2 = os.path.join(test_dir_path, b + ext)
                if os.path.exists(t2): p2 = t2

            if not p1 or not p2:
                preds.append(0)
                continue

            t1 = val_transform(Image.open(p1).convert('RGB')).unsqueeze(0).to(device)
            t2 = val_transform(Image.open(p2).convert('RGB')).unsqueeze(0).to(device)

            f1, f2 = model(t1), model(t2)
            sim = F.cosine_similarity(f1, f2).item()

            f1_f, f2_f = model(torch.flip(t1, [3])), model(torch.flip(t2, [3]))
            sim_f = F.cosine_similarity(f1_f, f2_f).item()

            final_sim = (sim + sim_f) / 2.0
            preds.append(1 if final_sim > threshold else 0)

            if i % 100 == 0:
                print(f"\rPredicting {i}/{len(ids)}", end="")

    sub_df = pd.DataFrame({'ID_ID': ids, 'TARGET': preds})
    out = filename(output_name, 'csv')
    sub_df.to_csv(out, index=False)
    print(f"\nDone. Saved to {out}")


if __name__ == '__main__':
    pass