import torch


#定义基于PCA的人脸识别模型类
class PCAFaceModel:
    # 模型的初始化参数定义
    def __init__(self, k_components=50):
        self.k = k_components  # 降维后保留的主成分个数（特征维度）
        self.mean_face = None  # 平均脸
        self.eigen_faces = None  # 特征脸（投影矩阵）

    # 训练过程：计算平均脸和特征脸
    def fit(self, X):
        """
        X: 形状为 (样本数量 N, 展平后的像素特征 D) 的张量
        """
        # 1. 计算平均脸并去均值
        self.mean_face = torch.mean(X, dim=0)
        X_centered = X - self.mean_face

        # 2. 计算协方差矩阵 (采用 N x N 的技巧，降低计算量)
        # L = X_centered * X_centered^T
        cov = torch.mm(X_centered, X_centered.T)

        # 3. 计算特征值和特征向量
        eigenvalues, eigenvectors = torch.linalg.eigh(cov)

        # 4. 按特征值大小降序排列
        idx = torch.argsort(eigenvalues, descending=True)
        eigenvectors = eigenvectors[:, idx]

        # 5. 选取前 k 个主成分
        eigenvectors = eigenvectors[:, :self.k]

        # 6. 将特征向量映射回原始维度空间 (D x k)
        self.eigen_faces = torch.mm(X_centered.T, eigenvectors)

        # 7. 对特征脸进行L2归一化
        self.eigen_faces = torch.nn.functional.normalize(self.eigen_faces, p=2, dim=0)

    # 降维过程：将输入数据投影到特征空间
    def transform(self, X):
        X_centered = X - self.mean_face
        return torch.mm(X_centered, self.eigen_faces)

    # 前向传播：在PCA中即为降维投影
    def forward(self, x):
        return self.transform(x)


if __name__ == '__main__':
    # 简单的测试逻辑
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("当前设备：", device)
    model = PCAFaceModel(k_components=50)
    print(f"PCA模型初始化成功，保留特征维度：{model.k}")