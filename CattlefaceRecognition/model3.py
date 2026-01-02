import os
import re
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
from function import get_next_filename as filename
import torch.nn.functional as F


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
def generate_pairs_from_train(train_dataset, num_pairs=20000):
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


# 优化的模型架构：更深的CNN + 双向GRU
class CNNGRUModel(nn.Module):
    def __init__(self, input_channels=3, gru_hidden_size=256, num_layers=2, output_size=256):
        super(CNNGRUModel, self).__init__()
        # 更深的CNN特征提取器
        self.cnn = nn.Sequential(
            nn.Conv2d(input_channels, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((7, 7))  # 输出特征图大小: 512x7x7
        )
        # 双向GRU序列建模
        self.gru_input_size = 512  # CNN输出通道数
        self.gru_hidden_size = gru_hidden_size
        self.gru_num_layers = num_layers
        self.gru = nn.GRU(input_size=self.gru_input_size,
                          hidden_size=gru_hidden_size,
                          num_layers=num_layers,
                          batch_first=True,
                          bidirectional=True,
                          dropout=0.3)
        # 全连接层输出特征向量
        self.fc = nn.Sequential(
            nn.Linear(gru_hidden_size * 2, 512),  # 双向GRU输出是隐藏大小的2倍
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, output_size)
        )

    def forward(self, x):
        # CNN前向传播
        cnn_out = self.cnn(x)  # 形状: (batch, 512, 7, 7)
        # 重塑为序列: (batch, sequence_length, features)
        batch_size, channels, height, width = cnn_out.size()
        cnn_out = cnn_out.view(batch_size, channels, -1)  # (batch, 512, 49)
        cnn_out = cnn_out.transpose(1, 2)  # (batch, 49, 512)
        # GRU前向传播
        gru_out, _ = self.gru(cnn_out)  # gru_out: (batch, 49, gru_hidden_size * 2)
        # 取最后一个时间步的输出
        gru_out = gru_out[:, -1, :]  # (batch, gru_hidden_size * 2)
        # 全连接层
        output = self.fc(gru_out)  # (batch, output_size)
        return output


# 优化的孪生网络结构
class SiameseNetwork(nn.Module):
    def __init__(self, cnn_gru_net):
        super(SiameseNetwork, self).__init__()
        self.cnn_gru_net = cnn_gru_net
        # 更复杂的相似度计算网络
        self.fc_similarity = nn.Sequential(
            nn.Linear(256, 256),  # 输入是特征向量的维度256
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1)
        )

    def forward(self, x1, x2):
        # 提取特征向量
        out1 = self.cnn_gru_net(x1)  # (batch, 256)
        out2 = self.cnn_gru_net(x2)  # (batch, 256)
        # 计算特征绝对差，然后输入全连接层
        diff = torch.abs(out1 - out2)  # (batch, 256)
        similarity = self.fc_similarity(diff)  # (batch, 1)
        return similarity.squeeze()  # (batch)


# 改进的训练函数
def train_model(model, train_loader, criterion, optimizer, device, num_epochs=15):
    model.train()
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
            optimizer.step()
            running_loss += loss.item()
            # 计算准确率
            preds = torch.sigmoid(outputs) > 0.5
            correct += (preds.float() == labels).sum().item()
            total += labels.size(0)

            # 每100个batch打印一次进度
            if i % 100 == 0:
                batch_acc = (preds.float() == labels).sum().item() / labels.size(0)
                print(
                    f'Epoch [{epoch + 1}/{num_epochs}], Batch [{i}/{len(train_loader)}], Loss: {loss.item():.4f}, Batch Acc: {batch_acc:.4f}')

        epoch_loss = running_loss / len(train_loader)
        epoch_acc = correct / total
        print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}')





# 主函数
def main():
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # 数据预处理 - 添加数据增强
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

    # 路径设置（根据实际调整）
    train_dir = 'cowface-verification-U/train/train'  # 训练集目录
    test_dir = 'cowface-verification-U/test/test'  # 测试集目录
    test_csv = 'cowface-verification-U/test-0930.csv'  # 测试CSV文件

    # 加载测试对
    test_df = pd.read_csv(test_csv)
    test_pairs = test_df['ID_ID'].tolist()

    # 从训练集生成图像对用于训练 - 增加训练对数量
    print("=====准备训练数据=====")
    train_dataset_single = CowFaceDataset(train_dir, transform=train_transform, is_train=True)
    train_pairs, train_labels = generate_pairs_from_train(train_dataset_single, num_pairs=20000)

    # 创建训练数据集和加载器
    train_dataset = PairDataset(train_pairs, train_labels, transform=train_transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)

    # 初始化模型
    print("=====初始化模型=====")
    cnn_gru_net = CNNGRUModel(input_channels=3, gru_hidden_size=256, num_layers=2, output_size=256)
    model = SiameseNetwork(cnn_gru_net).to(device)

    # 损失函数和优化器 - 添加权重衰减
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

    # 添加学习率调度器
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # 训练模型 - 增加训练轮数
    print("=====开始训练=====")
    train_model(model, train_loader, criterion, optimizer, device, num_epochs=15)

    # 预测测试集并保存结果
    print("=====开始预测=====")
    test_labels_dummy = [0] * len(test_pairs)  # 伪标签，实际预测时不需要
    test_dataset = CowFaceDataset(test_dir, csv_file=test_csv, transform=test_transform, is_train=False,
                                  pair_list=test_pairs, labels=test_labels_dummy)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    model.eval()
    predictions = []
    with torch.no_grad():
        for images1, images2, _ in test_loader:
            images1, images2 = images1.to(device), images2.to(device)
            outputs = model(images1, images2)
            preds = torch.sigmoid(outputs) > 0.5
            predictions.extend(preds.cpu().numpy().astype(int))

    # 保存预测结果到CSV
    submission_df = pd.DataFrame({'ID_ID': test_pairs, 'TARGET': predictions})
    save_file = filename('submission', 'csv')
    submission_df.to_csv(save_file, index=False)
    print("=====预测完成=====")
    print(f"预测结果已保存到 {save_file}，共 {len(predictions)} 个预测")

    # 保存模型
    model_save_file = filename('model', 'pth')
    torch.save(model.state_dict(), model_save_file)
    print(f"模型已保存到 {model_save_file}")



