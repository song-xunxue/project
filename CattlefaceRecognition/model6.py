import os
import random
import math
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
基于孪生网络的牛脸验证系统
使用对比损失(Contrastive Loss)训练ResNet18嵌入网络，判断两张牛脸图像是否属于同一只牛
"""

# -----------------------------
# 数据集与配对生成
# -----------------------------

class CowFaceDatasetSingle(Dataset):
    """单张图像数据集（用于生成配对）

   按牛ID组织图像，为每只牛分配唯一标签
    提前建立图像路径和标签的映射，避免在训练时频繁文件操作
    """

    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []  # 存储所有图像路径
        self.labels = []  # 存储对应的标签
        self.cow_id_to_label = {}  # 牛ID到数字标签的映射
        label_counter = 0

        # 遍历目录结构，组织数据
        for cow_id in sorted(os.listdir(root_dir)):
            cow_dir = os.path.join(root_dir, cow_id)
            if not os.path.isdir(cow_dir):
                continue

            # 为每只牛分配唯一标签
            self.cow_id_to_label[cow_id] = label_counter

            # 收集该牛的所有图像
            for img_name in os.listdir(cow_dir):
                self.image_paths.append(os.path.join(cow_dir, img_name))
                self.labels.append(label_counter)

            label_counter += 1

        self.num_classes = label_counter  # 总类别数（牛的数量）

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        """获取单张图像、标签和路径"""
        path = self.image_paths[idx]
        img = Image.open(path).convert('RGB')  # 确保RGB格式
        if self.transform:
            img = self.transform(img)
        lbl = self.labels[idx]
        return img, lbl, path


def generate_pairs(image_paths, labels, num_pairs=15000):
    """在给定单张图列表上生成配对（平衡正负样本）

    平衡的正负样本对生成

    - 正样本：同一只牛的不同图像
    - 负样本：不同牛的图像
    - 确保数据平衡，避免模型偏向某一类
    """
    pairs = []  # 存储图像对
    pair_labels = []  # 存储配对标签（1=相同，0=不同）
    n = len(image_paths)

    # 按标签组织索引 - 重要：提高正样本生成效率
    by_label = {}
    for idx, l in enumerate(labels):
        by_label.setdefault(l, []).append(idx)

    # 生成正样本对 - 同一类别内的不同图像
    num_pos = num_pairs // 2
    num_neg = num_pairs - num_pos

    print(f"生成 {num_pos} 个正样本和 {num_neg} 个负样本...")

    # 正样本生成：从同一类中随机选择两个不同图像
    for _ in range(num_pos):
        # 只选择拥有至少2张图像的类别
        valid_labels = [l for l, idxs in by_label.items() if len(idxs) >= 2]
        lbl = random.choice(valid_labels)
        a, b = random.sample(by_label[lbl], 2)  # 随机选择两个不同索引
        pairs.append((image_paths[a], image_paths[b]))
        pair_labels.append(1)  # 标签1表示相同个体

    # 负样本生成：从不同类别中随机选择图像
    for _ in range(num_neg):
        a = random.randrange(n)
        b = random.randrange(n)
        # 确保选择不同类别的图像
        while labels[a] == labels[b]:
            b = random.randrange(n)
        pairs.append((image_paths[a], image_paths[b]))
        pair_labels.append(0)  # 标签0表示不同个体

    # 打乱数据 - 重要：避免训练时连续看到同类样本
    combined = list(zip(pairs, pair_labels))
    random.shuffle(combined)
    pairs, pair_labels = zip(*combined)

    return list(pairs), list(pair_labels)


class PairDataset(Dataset):
    """配对数据集类
    专门为孪生网络设计，同时加载和变换图像对
    """

    def __init__(self, pairs, labels, transform=None):
        self.pairs = pairs  # 图像对列表
        self.labels = labels  # 对应标签
        self.transform = transform  # 图像变换

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        """返回一对图像和它们的相似性标签"""
        p = self.pairs[idx]
        # 加载两张图像
        img1 = Image.open(p[0]).convert('RGB')
        img2 = Image.open(p[1]).convert('RGB')

        # 应用相同的变换（重要：保持数据一致性）
        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)

        lbl = torch.tensor(self.labels[idx], dtype=torch.float32)
        return img1, img2, lbl


# -----------------------------
# 网络架构：轻量的孪生网络（ResNet18 + projection head）
# -----------------------------

class EmbeddingNet(nn.Module):
    """嵌入网络 - 核心特征提取器
    - 使用预训练ResNet18作为backbone
    - 添加projection head将特征映射到低维空间
    - L2归一化便于距离计算
    """

    def __init__(self, emb_dim=128, pretrained=True):
        super().__init__()
        # 使用预训练的ResNet18骨干网络
        resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)

        # 移除原始的全连接层 - 重要：保留特征提取能力
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])  # 输出 (batch, 512, 1, 1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        # Projection Head - 关键：将512维特征映射到指定维度
        self.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),  # 批归一化：加速收敛，提高稳定性
            nn.ReLU(inplace=True),  # 激活函数：引入非线性
            nn.Dropout(0.2),  # Dropout：防止过拟合
            nn.Linear(256, emb_dim)  # 最终嵌入维度
        )

    def forward(self, x):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)  # 展平特征图 (batch, 512)
        x = self.fc(x)
        x = F.normalize(x, p=2, dim=1)  # L2归一化 - 重要：便于计算余弦相似度
        return x


class SiameseModel(nn.Module):
    """孪生网络模型
    共享权重的双分支网络，学习有区分度的特征表示
    """

    def __init__(self, emb_dim=128):
        super().__init__()
        self.embed_net = EmbeddingNet(emb_dim=emb_dim)

    def forward(self, x1, x2):
        # 两个输入共享相同的嵌入网络
        e1 = self.embed_net(x1)
        e2 = self.embed_net(x2)
        return e1, e2


# -----------------------------
# 损失函数：Contrastive loss（常用于孪生网络）
# -----------------------------

def contrastive_loss(e1, e2, label, margin=1.0):
    """对比损失函数

    - 正样本：最小化嵌入空间中的距离
    - 负样本：最大化距离，但超过margin后不再惩罚


    - 直接优化特征空间的结构
    - 对样本不平衡不敏感
    """
    # 计算欧氏距离
    dist = F.pairwise_distance(e1, e2, keepdim=False)

    # 正样本损失：距离越小越好
    loss_pos = label * torch.pow(dist, 2)

    # 负样本损失：距离大于margin时损失为0
    loss_neg = (1 - label) * torch.pow(torch.clamp(margin - dist, min=0.0), 2)

    # 总损失
    loss = 0.5 * (loss_pos + loss_neg)
    return loss.mean()


# -----------------------------
# 训练/验证流程
# -----------------------------

def evaluate(model, dataloader, device):
    """验证函数 - 评估模型在验证集上的表现"""
    model.eval()  # 重要：设置为评估模式
    total_loss = 0.0
    total = 0

    with torch.no_grad():  # 关键：禁用梯度计算，节省内存
        for x1, x2, y in dataloader:
            x1 = x1.to(device);
            x2 = x2.to(device);
            y = y.to(device)
            e1, e2 = model(x1, x2)
            loss = contrastive_loss(e1, e2, y)
            total_loss += loss.item() * y.size(0)
            total += y.size(0)

    return total_loss / (total + 1e-12)  # 防止除零


def train(model, train_loader, val_loader, device, epochs=30, lr=3e-4, weight_decay=1e-4):
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    scaler = torch.amp.GradScaler('cuda') if device.type == 'cuda' else None

    best_val_loss = float('inf')
    patience = 6
    counter = 0

    # 修复：在训练开始前确定最佳模型的文件名
    best_model_filename = filename('best_model', 'pth')

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        total = 0
        total_batches = len(train_loader)

        print(f"\n=== Epoch {epoch}/{epochs} ===")

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

            if batch_idx % 50 == 0 or batch_idx == total_batches:
                avg_batch_loss = running_loss / total
                progress = batch_idx / total_batches * 100
                current_lr = optimizer.param_groups[0]['lr']
                print(f"Epoch {epoch:2d}/{epochs} | Batch {batch_idx:4d}/{total_batches} "
                      f"({progress:5.1f}%) | Loss: {avg_batch_loss:.4f} | LR: {current_lr:.6f}")

        scheduler.step()
        train_loss = running_loss / (total + 1e-12)
        val_loss = evaluate(model, val_loader, device)

        print(f"\nEpoch {epoch:2d} 总结:")
        print(f"  训练损失: {train_loss:.4f}")
        print(f"  验证损失: {val_loss:.4f}")
        print(f"  学习率: {optimizer.param_groups[0]['lr']:.6f}")

        # 修复：使用固定的文件名保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            counter = 0
            torch.save(model.state_dict(), best_model_filename)  # 使用固定的文件名
            print(f"   保存最佳模型到 {best_model_filename} (验证损失: {val_loss:.4f})")
        else:
            counter += 1
            print(f" 无改善 (计数: {counter}/{patience})")
            if counter >= patience:
                print(" 触发早停")
                break

    # 修复：加载时使用相同的文件名
    if os.path.exists(best_model_filename):
        model.load_state_dict(torch.load(best_model_filename))
        print(f"加载最佳模型: {best_model_filename}")
    else:
        print(f"警告: 最佳模型文件 {best_model_filename} 不存在，使用当前模型")

    return model

# -----------------------------
# 测试/预测函数
# -----------------------------

def predict_pairs(model, test_pairs, test_dir, device, transform, batch_size=32):
    """预测函数 - 对测试图像对进行分类
    批量处理提高推理速度，距离阈值可调
    """
    model.eval()
    # 创建测试数据集（标签为虚拟值）
    ds = PairDataset(test_pairs, [0] * len(test_pairs), transform=transform)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=4)

    preds = []
    with torch.no_grad():
        for x1, x2, _ in loader:
            x1 = x1.to(device);
            x2 = x2.to(device)
            e1, e2 = model(x1, x2)
            dist = F.pairwise_distance(e1, e2)  # 计算欧氏距离

            # 关键：基于距离的决策阈值（可调超参数）
            # 距离小 -> 相同个体，距离大 -> 不同个体
            preds.extend((dist < 0.8).cpu().numpy().astype(int).tolist())

    return preds


# -----------------------------
# 主函数
# -----------------------------
#
# def main():
#     """主执行函数 - 整合整个训练和推理流程"""
#     # 设置随机种子 - 重要：保证实验可重复性
#     random.seed(42)
#     torch.manual_seed(42)
#
#     # 设备配置 - 自动检测GPU
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#     print("Device:", device)
#
#     # 数据增强变换 - 关键：提高模型泛化能力
#     train_transform = transforms.Compose([
#         transforms.Resize((256, 256)),  # 调整大小
#         transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),  # 随机裁剪
#         transforms.RandomHorizontalFlip(p=0.5),  # 水平翻转
#         transforms.RandomApply([transforms.ColorJitter(0.3, 0.3, 0.2, 0.05)], p=0.5),  # 颜色抖动
#         transforms.RandomRotation(10),  # 随机旋转
#         transforms.ToTensor(),  # 转换为张量
#         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet标准化
#         transforms.RandomErasing(p=0.4, scale=(0.02, 0.2), ratio=(0.3, 3.3))  # 随机擦除
#     ])
#
#     # 验证集变换 - 不需要数据增强
#     val_transform = transforms.Compose([
#         transforms.Resize((224, 224)),  # 固定大小
#         transforms.ToTensor(),
#         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
#     ])
#
#     # 数据路径配置
#     train_dir = 'cowface-verification-U/train/train'
#     test_dir = 'cowface-verification-U/test/test'
#     test_csv = 'cowface-verification-U/test-0930.csv'  # 测试集定义文件
#
#     # 加载单张数据集并生成配对
#     print("加载单张图像数据集...")
#     single_ds = CowFaceDatasetSingle(train_dir, transform=None)
#     print(f"找到 {len(single_ds)} 张图像, {single_ds.num_classes} 只牛.")
#
#     # 生成配对数据并划分训练集/验证集
#     # 重要：分层抽样保证正负样本比例一致
#     pairs, labels = generate_pairs(single_ds.image_paths, single_ds.labels, num_pairs=20000)
#     p_train, p_val, l_train, l_val = train_test_split(
#         pairs, labels, test_size=0.2, stratify=labels, random_state=42
#     )
#
#     # 创建配对数据集和数据加载器
#     train_ds = PairDataset(p_train, l_train, transform=train_transform)
#     val_ds = PairDataset(p_val, l_val, transform=val_transform)
#
#     train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
#     val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=4, pin_memory=True)
#
#     # 初始化模型
#     # model = SiameseModel(emb_dim=128).to(device)
#
#     # 训练模型
#     print("开始训练模型...")
#     # model = train(model, train_loader, val_loader, device, epochs=30, lr=3e-4, weight_decay=1e-4)
#
#     # 如果存在测试CSV，执行预测
#     if os.path.exists(test_csv):
#         print("对测试图像对进行推理...")
#         test_df = pd.read_csv(test_csv)
#         test_pairs_str = test_df['ID_ID'].tolist()
#
#         # 解析测试对并构建完整路径
#         test_pairs = []
#         for s in test_pairs_str:
#             a, b = s.split('_')
#             test_pairs.append((
#                 os.path.join(test_dir, f"{a}.jpg"),
#                 os.path.join(test_dir, f"{b}.jpg")
#             ))
#
#         # 执行预测
#         preds = predict_pairs(model, test_pairs, test_dir, device, val_transform, batch_size=64)
#
#         # 保存结果
#         sub_df = pd.DataFrame({'ID_ID': test_pairs_str, 'TARGET': preds})
#         out_file = filename('submission', 'csv')
#         sub_df.to_csv(out_file, index=False)
#         print("预测结果保存至", out_file)
#     else:
#         print("未找到测试CSV文件；跳过推理步骤.")
#
#     # 最终保存模型
#     model_file = filename('model', 'pth')
#     torch.save(model.state_dict(), model_file)
#     print("模型保存至", model_file)


def main_train(model_path=None,train_epochs=30,train_dir = 'cowface-verification-U/train/train'):
    """训练模型并保存

    参数:
        model_path: 预训练模型路径，如果提供则加载继续训练
    """
    # 设置随机种子
    random.seed(42)
    torch.manual_seed(42)

    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("Device:", device)

    # 数据增强变换
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomApply([transforms.ColorJitter(0.3, 0.3, 0.2, 0.05)], p=0.5),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.4, scale=(0.02, 0.2), ratio=(0.3, 3.3))
    ])

    # 验证集变换
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])



    # 加载单张数据集并生成配对
    print("加载单张图像数据集...")
    single_ds = CowFaceDatasetSingle(train_dir, transform=None)
    print(f"找到 {len(single_ds)} 张图像, {single_ds.num_classes} 只牛.")

    # 生成配对数据并划分训练集/验证集
    pairs, labels = generate_pairs(single_ds.image_paths, single_ds.labels, num_pairs=20000)
    p_train, p_val, l_train, l_val = train_test_split(
        pairs, labels, test_size=0.2, stratify=labels, random_state=42
    )

    # 创建配对数据集和数据加载器
    train_ds = PairDataset(p_train, l_train, transform=train_transform)
    val_ds = PairDataset(p_val, l_val, transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=4, pin_memory=True)

    # 初始化模型
    model = SiameseModel(emb_dim=128).to(device)

    # 如果提供了预训练模型，则加载
    if model_path and os.path.exists(model_path):
        print(f"加载预训练模型: {model_path}")
        model.load_state_dict(torch.load(model_path, map_location=device))

    # 训练模型
    print("开始训练模型...")
    model = train(model, train_loader, val_loader, device, epochs=train_epochs, lr=3e-4, weight_decay=1e-4)

    # 保存最终模型
    final_model_file = filename('best_model', 'pth')
    torch.save(model.state_dict(), 'model_train/'+final_model_file)
    print("最终模型保存至", 'model_train/'+final_model_file)

    return model


def main_predict(model_path=None, test_csv_path=None, test_dir_path=None, output_name='submission'):
    """使用训练好的模型进行预测
    参数:
        model_path: 训练好的模型路径
        test_csv_path: 测试CSV文件路径
        test_dir_path: 测试图像目录路径
        output_name: 输出文件名前缀
    """
    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("Device:", device)

    # 默认路径
    if test_csv_path is None:
        test_csv_path = 'cowface-verification-U/test-0930.csv'
    if test_dir_path is None:
        test_dir_path = 'cowface-verification-U/test/test'

    # 验证集变换
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 如果没有指定模型路径，查找最新的模型文件
    if model_path is None:
        # 查找所有模型文件
        model_files = [f for f in os.listdir('.') if f.endswith('.pth') and ('model_' in f or 'best_model_' in f)]
        if model_files:
            # 按修改时间排序，选择最新的
            model_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            model_path = model_files[0]
            print(f"自动选择最新模型: {model_path}")
        else:
            print("错误: 未找到任何模型文件，请指定模型路径")
            return

    # 检查模型文件是否存在
    if not os.path.exists(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        return

    # 检查测试文件是否存在
    if not os.path.exists(test_csv_path):
        print(f"错误: 测试CSV文件不存在: {test_csv_path}")
        return

    # 加载模型
    print(f"加载模型: {model_path}")
    model = SiameseModel(emb_dim=128).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # 读取测试数据
    print("读取测试数据...")
    test_df = pd.read_csv(test_csv_path)
    test_pairs_str = test_df['ID_ID'].tolist()

    # 解析测试对并构建完整路径
    test_pairs = []
    for s in test_pairs_str:
        a, b = s.split('_')
        test_pairs.append((
            os.path.join(test_dir_path, f"{a}.jpg"),
            os.path.join(test_dir_path, f"{b}.jpg")
        ))

    # 执行预测
    print("执行预测...")
    preds = predict_pairs(model, test_pairs, test_dir_path, device, val_transform, batch_size=64)

    # 保存结果
    sub_df = pd.DataFrame({'ID_ID': test_pairs_str, 'TARGET': preds})
    out_file = filename(output_name, 'csv')
    sub_df.to_csv(out_file, index=False)
    print(f"预测结果保存至: {out_file}")


    return preds