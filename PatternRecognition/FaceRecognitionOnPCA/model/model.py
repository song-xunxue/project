"""
PCA人脸识别模型模块

实现基于主成分分析（PCA）的人脸特征提取。
核心思路：将高维人脸图像投影到低维特征子空间（"特征脸"空间），
在该空间中人脸的类内距离更小、类间距离更大，从而提高识别准确率。

数学原理：
    1. 计算训练集的平均脸 μ = (1/N) * Σ x_i
    2. 去均值：x_centered = x - μ
    3. 构造协方差矩阵 C = X_centered * X_centered^T
    4. 对 C 进行特征分解，取前 K 个最大特征值对应的特征向量
    5. 将特征向量映射回原始维度并归一化，得到"特征脸"矩阵 W
    6. 降维投影：y = W^T * (x - μ)

作者: 李文煜
日期: 2026-03-11
"""

import torch


class PCAFaceModel:
    """
    基于PCA的人脸识别模型

    通过主成分分析将高维人脸图像投影到低维特征空间，
    利用特征脸（Eigenfaces）表示人脸身份特征。

    属性:
        k (int): 降维后保留的主成分个数
        mean_face (torch.Tensor): 训练集的平均脸，形状 (D,)
        eigen_faces (torch.Tensor): 特征脸投影矩阵，形状 (D, K)
    """

    def __init__(self, k_components=50):
        """
        初始化PCA模型

        参数:
            k_components (int): 降维后保留的主成分个数（特征维度）。
                                例如 k=2 降到二维用于可视化，k=50 用于识别。
        """
        self.k = k_components
        self.mean_face = None    # 平均脸向量，维度与输入图像展平后相同
        self.eigen_faces = None  # 特征脸矩阵，每列是一个主成分方向

    def fit(self, X):
        """
        训练PCA模型：从训练数据中计算平均脸和特征脸

        采用 N×N 协方差矩阵技巧：当样本数 N 远小于特征维度 D 时，
        计算 N×N 矩阵的特征分解比 D×D 矩阵高效得多。
        ORL数据集中 N=320, D=10304，因此此技巧非常适用。

        参数:
            X (torch.Tensor): 训练数据，形状 (N, D)
                              N 为样本数量，D 为展平后的像素特征维度
        """
        # 1. 计算平均脸：对所有训练样本取逐像素均值
        self.mean_face = torch.mean(X, dim=0)
        X_centered = X - self.mean_face

        # 2. 构造 N×N 的小型协方差矩阵（而非 D×D 的大型矩阵）
        #    L = X_centered @ X_centered^T，形状 (N, N)
        cov = torch.mm(X_centered, X_centered.T)

        # 3. 对协方差矩阵进行特征分解
        #    eigh 适用于对称矩阵，返回特征值和对应的特征向量
        eigenvalues, eigenvectors = torch.linalg.eigh(cov)

        # 4. 按特征值从大到小排序（特征值越大，对应的主成分携带的信息量越多）
        idx = torch.argsort(eigenvalues, descending=True)
        eigenvectors = eigenvectors[:, idx]

        # 5. 只保留前 K 个主成分对应的特征向量
        eigenvectors = eigenvectors[:, :self.k]

        # 6. 将 N 维特征向量映射回原始 D 维空间
        #    V = X_centered^T @ eigenvectors，形状 (D, K)
        self.eigen_faces = torch.mm(X_centered.T, eigenvectors)

        # 7. 对特征脸进行 L2 归一化（每列除以其范数），确保投影后的尺度一致
        self.eigen_faces = torch.nn.functional.normalize(self.eigen_faces, p=2, dim=0)

    def transform(self, X):
        """
        将输入数据投影到PCA特征空间（降维）

        参数:
            X (torch.Tensor): 待降维数据，形状 (N, D) 或 (D,)

        返回:
            torch.Tensor: 降维后的特征表示，形状 (N, K) 或 (K,)
        """
        X_centered = X - self.mean_face
        return torch.mm(X_centered, self.eigen_faces)

    def forward(self, x):
        """
        前向传播（等同于降维投影）

        参数:
            x (torch.Tensor): 输入数据

        返回:
            torch.Tensor: 降维后的特征
        """
        return self.transform(x)


if __name__ == '__main__':
    # 模块独立测试：验证模型能否正常初始化
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("当前设备：", device)
    model = PCAFaceModel(k_components=50)
    print(f"PCA模型初始化成功，保留特征维度：{model.k}")