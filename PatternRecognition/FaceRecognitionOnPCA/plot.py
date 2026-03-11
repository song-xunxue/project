# 使用kagglehub 库从 Kaggle 平台下载名为 "att-database-of-faces"
import kagglehub
import os

# 1. 定义你想要的下载路径
target_path = "./data"

# 2. 确保目标目录存在
os.makedirs(target_path, exist_ok=True)

# 3. 指定 path 参数下载数据集到目标位置
dataset_path = kagglehub.dataset_download(
    handle="sarfarazansari/att-database-of-faces",  # 可用的数据集标识符
    path=target_path  # 指定下载路径
)

# 打印结果并验证
print("数据集下载成功！")
print("数据集本地路径:", dataset_path)
print("路径是否存在:", os.path.exists(dataset_path))
