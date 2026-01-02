import os
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
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

# 模型架构：CNN + GRU
class CNNGRUModel(nn.Module):
    def __init__(self, input_channels=3, gru_hidden_size=128, num_layers=1, output_size=128):
        super(CNNGRUModel, self).__init__()
        # CNN特征提取器
        self.cnn = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((7, 7))  # 输出特征图大小: 256x7x7
        )
        # GRU序列建模
        self.gru_input_size = 256  # CNN输出通道数
        self.gru_hidden_size = gru_hidden_size
        self.gru_num_layers = num_layers
        self.gru = nn.GRU(input_size=self.gru_input_size, hidden_size=gru_hidden_size,
                          num_layers=num_layers, batch_first=True, bidirectional=False)
        # 全连接层输出特征向量
        self.fc = nn.Linear(gru_hidden_size, output_size)

    def forward(self, x):
        # CNN前向传播
        cnn_out = self.cnn(x)  # 形状: (batch, 256, 7, 7)
        # 重塑为序列: (batch, sequence_length, features)
        batch_size, channels, height, width = cnn_out.size()
        cnn_out = cnn_out.view(batch_size, channels, -1)  # (batch, 256, 49)
        cnn_out = cnn_out.transpose(1, 2)  # (batch, 49, 256)
        # GRU前向传播
        gru_out, _ = self.gru(cnn_out)  # gru_out: (batch, 49, gru_hidden_size)
        # 取最后一个时间步的输出
        gru_out = gru_out[:, -1, :]  # (batch, gru_hidden_size)
        # 全连接层
        output = self.fc(gru_out)  # (batch, output_size)
        return output

# 孪生网络结构
class SiameseNetwork(nn.Module):
    def __init__(self, cnn_gru_net):
        super(SiameseNetwork, self).__init__()
        self.cnn_gru_net = cnn_gru_net
        # 全连接层用于相似度计算
        # self.fc_similarity = nn.Sequential(
        #     nn.Linear(256, 128),  # 输入是两个特征向量拼接后的维度
        #     nn.ReLU(inplace=True),
        #     nn.Linear(128, 1)
        # )
        # 配对了一下
        self.fc_similarity = nn.Sequential(
            nn.Linear(128, 64),  # 输入维度改为 128，输出 64
            nn.ReLU(inplace=True),
            nn.Linear(64, 1)  # 输出 1 维相似度分数
        )

    def forward(self, x1, x2):
        # 提取特征向量
        out1 = self.cnn_gru_net(x1)  # (batch, output_size)
        out2 = self.cnn_gru_net(x2)  # (batch, output_size)
        # 计算特征绝对差，然后输入全连接层
        diff = torch.abs(out1 - out2)  # (batch, output_size)
        similarity = self.fc_similarity(diff)  # (batch, 1)
        return similarity.squeeze()  # (batch)

# 训练和评估函数
def train_model(model, train_loader, criterion, optimizer, device, num_epochs=10):
    model.train()
    for epoch in range(num_epochs):
        print("=====第{:0} 次训练=====".format(epoch))
        running_loss = 0.0
        correct = 0
        total = 0
        for images1, images2, labels in train_loader:
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
        epoch_loss = running_loss / len(train_loader)
        epoch_acc = correct / total
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}')

def evaluate_model(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images1, images2, labels in test_loader:
            images1, images2, labels = images1.to(device), images2.to(device), labels.to(device).float()
            outputs = model(images1, images2)
            preds = torch.sigmoid(outputs) > 0.5
            correct += (preds.float() == labels).sum().item()
            total += labels.size(0)
    accuracy = correct / total
    print(f'Test Accuracy: {accuracy:.4f}')
    return accuracy

# 主函数
def main():
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # 数据预处理
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 路径设置（根据实际调整）
    train_dir = 'cowface-verification-U/train/train'  # 训练集目录
    test_dir = 'cowface-verification-U/test/test'    # 测试集目录
    test_csv = 'cowface-verification-U/test-0930.csv'  # 测试CSV文件

    # 加载测试对
    test_df = pd.read_csv(test_csv)
    test_pairs = test_df['ID_ID'].tolist()
    # 注意：测试CSV没有标签，这里假设需要从训练集生成验证集进行评估
    # 为演示，我们生成一个验证集从训练集

    # 从训练集生成图像对用于训练
    # 由于训练集没有直接提供对，我们随机生成正负样本对
    def generate_pairs_from_train(train_dataset, num_pairs=10000):
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

    # 创建训练数据集和加载器
    train_dataset_single = CowFaceDataset(train_dir, transform=transform, is_train=True)
    train_pairs, train_labels = generate_pairs_from_train(train_dataset_single, num_pairs=10000)

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

    train_dataset = PairDataset(train_pairs, train_labels, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)

    # 创建验证集（从训练集分割）
    val_size = int(0.2 * len(train_pairs))
    train_size = len(train_pairs) - val_size
    train_subset, val_subset = torch.utils.data.random_split(train_dataset, [train_size, val_size])
    train_loader = DataLoader(train_subset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_subset, batch_size=32, shuffle=False)

    # 初始化模型
    cnn_gru_net = CNNGRUModel(input_channels=3, gru_hidden_size=128, num_layers=1, output_size=128)
    model = SiameseNetwork(cnn_gru_net).to(device)

    # 损失函数和优化器
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 训练模型
    print("=====开始训练=====")
    train_model(model, train_loader, criterion, optimizer, device, num_epochs=10)

    # 评估模型
    print("=====在验证集上进行评估=====")
    accuracy = evaluate_model(model, val_loader, device)

    print("模型的目标准确率:",accuracy)


    # 预测测试集并保存结果
    # 注意：测试集没有标签，所以需要加载测试对并预测
    test_labels_dummy = [0] * len(test_pairs)  # 伪标签，实际预测时不需要
    test_dataset = CowFaceDataset(test_dir, csv_file=test_csv, transform=transform, is_train=False,
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
    submission_df.to_csv('submission.csv', index=False)
    print("预测结果保存至submission.csv")

if __name__ == '__main__':
    main()

