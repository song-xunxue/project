import os
import re
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from function import get_next_filename as filename
import torch.nn.functional as F
import math


# 数据预处理和加载
class CowFaceDataset(Dataset):
    def __init__(self, train_dir, csv_file=None, transform=None, is_train=True, pair_list=None, labels=None):
        """
        Args:
            train_dir (str): 训练集目录路径，包含子目录（牛ID）。
            csv_file (str): 测试CSV文件路径（用于测试集）。
            transform: 图像预处理。
            is_train (bool): 是否为训练模式。
            pair_list (list): 图像对列表（用于测试集）。
            labels (list): 图像对标签（用于测试集）。
        """
        self.transform = transform
        self.is_train = is_train
        if is_train:
            # 训练模式：加载训练集图像和牛ID
            self.image_paths = []
            self.labels = []
            self.cow_id_to_label = {}
            label_counter = 0
            for cow_id in os.listdir(train_dir):
                cow_dir = os.path.join(train_dir, cow_id)
                if os.path.isdir(cow_dir):
                    self.cow_id_to_label[cow_id] = label_counter
                    for img_name in os.listdir(cow_dir):
                        self.image_paths.append(os.path.join(cow_dir, img_name))
                        self.labels.append(label_counter)
                    label_counter += 1
            self.num_classes = label_counter
        else:
            # 测试模式：使用提供的图像对和标签
            self.pair_list = pair_list
            self.labels = labels
            self.image_dir = train_dir  # 测试图像目录

    def __len__(self):
        if self.is_train:
            return len(self.image_paths)
        else:
            return len(self.pair_list)

    def __getitem__(self, idx):
        if self.is_train:
            # 训练模式：返回单个图像和标签（用于生成对）
            img_path = self.image_paths[idx]
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            label = self.labels[idx]
            return image, label
        else:
            # 测试模式：返回图像对和标签
            pair = self.pair_list[idx]
            img1_name, img2_name = pair.split('_')
            img1_path = os.path.join(self.image_dir, f"{img1_name}.jpg")
            img2_path = os.path.join(self.image_dir, f"{img2_name}.jpg")
            image1 = Image.open(img1_path).convert('RGB')
            image2 = Image.open(img2_path).convert('RGB')
            if self.transform:
                image1 = self.transform(image1)
                image2 = self.transform(image2)
            label = self.labels[idx]
            return image1, image2, label


# 从训练集生成图像对
def generate_pairs_from_train(train_dataset, num_pairs=15000):
    pairs = []
    labels = []
    image_paths = train_dataset.image_paths
    image_labels = train_dataset.labels
    for _ in range(num_pairs):
        idx1 = torch.randint(0, len(image_paths), (1,)).item()
        idx2 = torch.randint(0, len(image_paths), (1,)).item()
        label1 = image_labels[idx1]
        label2 = image_labels[idx2]
        pairs.append((image_paths[idx1], image_paths[idx2]))
        labels.append(1 if label1 == label2 else 0)
    return pairs, labels


# 自定义数据集用于图像对
class PairDataset(Dataset):
    def __init__(self, pairs, labels, transform=None):
        self.pairs = pairs
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        img1_path, img2_path = self.pairs[idx]
        image1 = Image.open(img1_path).convert('RGB')
        image2 = Image.open(img2_path).convert('RGB')
        if self.transform:
            image1 = self.transform(image1)
            image2 = self.transform(image2)
        label = self.labels[idx]
        return image1, image2, label


# 简化的Transformer编码器层
class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward=2048, dropout=0.1):
        super(TransformerEncoderLayer, self).__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout)
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.activation = nn.ReLU()

    def forward(self, src, src_mask=None, src_key_padding_mask=None):
        src2 = self.self_attn(src, src, src, attn_mask=src_mask,
                              key_padding_mask=src_key_padding_mask)[0]
        src = src + self.dropout1(src2)
        src = self.norm1(src)
        src2 = self.linear2(self.dropout(self.activation(self.linear1(src))))
        src = src + self.dropout2(src2)
        src = self.norm2(src)
        return src


# 位置编码
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


# 修复的混合模型架构
class HybridModel(nn.Module):
    def __init__(self, feature_dim=512, transformer_layers=2, transformer_heads=8, lstm_hidden=256, output_size=256):
        super(HybridModel, self).__init__()

        # 使用预训练的ResNet作为特征提取器
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])  # 移除最后两层

        # 自适应池化
        self.adaptive_pool = nn.AdaptiveAvgPool2d((7, 7))

        # 特征投影层 - 修复维度问题
        self.resnet_output_channels = 2048  # ResNet50的输出通道数
        self.feature_projection = nn.Linear(self.resnet_output_channels, feature_dim)

        # Transformer编码器
        self.transformer_layers = transformer_layers
        self.transformer_heads = transformer_heads
        self.feature_dim = feature_dim

        self.positional_encoding = PositionalEncoding(feature_dim)
        self.transformer_encoder = nn.ModuleList([
            TransformerEncoderLayer(feature_dim, transformer_heads, feature_dim * 4)
            for _ in range(transformer_layers)
        ])

        # BiLSTM
        self.lstm_hidden = lstm_hidden
        self.bilstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=lstm_hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2
        )

        # 输出层
        self.output_layers = nn.Sequential(
            nn.Linear(lstm_hidden * 2, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, output_size)
        )

    def forward(self, x):
        # ResNet特征提取
        batch_size = x.size(0)
        features = self.backbone(x)  # (batch, 2048, H, W)
        features = self.adaptive_pool(features)  # (batch, 2048, 7, 7)

        # 重塑为序列 - 修复维度问题
        features = features.view(batch_size, self.resnet_output_channels, -1)  # (batch, 2048, 49)
        features = features.transpose(1, 2)  # (batch, 49, 2048)

        # 投影到特征维度
        features = self.feature_projection(features)  # (batch, 49, feature_dim)

        # Transformer编码
        features = features.transpose(0, 1)  # (seq_len, batch, feature_dim)
        features = self.positional_encoding(features)

        for layer in self.transformer_encoder:
            features = layer(features)

        features = features.transpose(0, 1)  # (batch, seq_len, feature_dim)

        # BiLSTM处理
        lstm_out, (h_n, c_n) = self.bilstm(features)

        # 使用最后一个时间步的输出
        lstm_out = lstm_out[:, -1, :]  # (batch, lstm_hidden * 2)

        # 输出层
        output = self.output_layers(lstm_out)  # (batch, output_size)

        return output


# 修复的孪生网络结构
class SiameseNetwork(nn.Module):
    def __init__(self, hybrid_model):
        super(SiameseNetwork, self).__init__()
        self.hybrid_model = hybrid_model

        # 相似度计算网络
        self.similarity_net = nn.Sequential(
            nn.Linear(512, 256),  # 输入是两个256维特征拼接后的512维
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1)
        )

    def forward(self, x1, x2):
        # 提取特征向量
        out1 = self.hybrid_model(x1)  # (batch, 256)
        out2 = self.hybrid_model(x2)  # (batch, 256)

        # 拼接两个特征向量
        combined = torch.cat([out1, out2], dim=1)  # (batch, 512)

        # 计算相似度
        similarity = self.similarity_net(combined)  # (batch, 1)

        return similarity.squeeze()  # (batch)


# 改进的训练函数
def train_model(model, train_loader, criterion, optimizer, device, num_epochs=15):
    model.train()

    # 学习率调度器
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    for epoch in range(num_epochs):
        print(f"=====第 {epoch + 1} 次训练=====")
        running_loss = 0.0
        correct = 0
        total = 0

        for i, (images1, images2, labels) in enumerate(train_loader):
            images1, images2, labels = images1.to(device), images2.to(device), labels.to(device).float()
            optimizer.zero_grad()
            outputs = model(images1, images2)
            loss = criterion(outputs, labels)
            loss.backward()

            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item()
            # 计算准确率
            preds = torch.sigmoid(outputs) > 0.5
            correct += (preds.float() == labels).sum().item()
            total += labels.size(0)

            # 每50个batch打印一次进度
            if i % 50 == 0:
                batch_acc = (preds.float() == labels).sum().item() / labels.size(0)
                current_lr = optimizer.param_groups[0]['lr']
                print(f'Epoch [{epoch + 1}/{num_epochs}], Batch [{i}/{len(train_loader)}], '
                      f'Loss: {loss.item():.4f}, Batch Acc: {batch_acc:.4f}, LR: {current_lr:.6f}')

        # 更新学习率
        scheduler.step()

        epoch_loss = running_loss / len(train_loader)
        epoch_acc = correct / total
        print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}')


# 主函数
def main():
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # 数据预处理
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 路径设置
    train_dir = 'cowface-verification-U/train/train'
    test_dir = 'cowface-verification-U/test/test'
    test_csv = 'cowface-verification-U/test-0930.csv'

    # 加载测试对
    test_df = pd.read_csv(test_csv)
    test_pairs = test_df['ID_ID'].tolist()

    # 准备训练数据
    print("=====准备训练数据=====")
    train_dataset_single = CowFaceDataset(train_dir, transform=train_transform, is_train=True)
    train_pairs, train_labels = generate_pairs_from_train(train_dataset_single, num_pairs=15000)

    # 创建训练数据集和加载器
    train_dataset = PairDataset(train_pairs, train_labels, transform=train_transform)
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=4)

    # 初始化模型
    print("=====初始化模型=====")
    hybrid_model = HybridModel(
        feature_dim=512,
        transformer_layers=2,
        transformer_heads=8,
        lstm_hidden=256,
        output_size=256
    )
    model = SiameseNetwork(hybrid_model).to(device)

    # 损失函数和优化器
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.0001, weight_decay=1e-4)

    # 训练模型
    print("=====开始训练=====")
    train_model(model, train_loader, criterion, optimizer, device, num_epochs=15)

    # 预测测试集并保存结果
    print("=====开始预测=====")
    test_labels_dummy = [0] * len(test_pairs)
    test_dataset = CowFaceDataset(test_dir, csv_file=test_csv, transform=test_transform, is_train=False,
                                  pair_list=test_pairs, labels=test_labels_dummy)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    model.eval()
    predictions = []
    with torch.no_grad():
        for images1, images2, _ in test_loader:
            images1, images2 = images1.to(device), images2.to(device)
            outputs = model(images1, images2)
            preds = torch.sigmoid(outputs) > 0.5
            predictions.extend(preds.cpu().numpy().astype(int))

    # 保存预测结果
    submission_df = pd.DataFrame({'ID_ID': test_pairs, 'TARGET': predictions})
    save_file = filename('submission', 'csv')
    submission_df.to_csv(save_file, index=False)
    print("=====预测完成=====")
    print(f"预测结果已保存到 {save_file}，共 {len(predictions)} 个预测")

    # 保存模型
    model_save_file = filename('model', 'pth')
    torch.save(model.state_dict(), model_save_file)
    print(f"模型已保存到 {model_save_file}")


if __name__ == '__main__':
    main()
