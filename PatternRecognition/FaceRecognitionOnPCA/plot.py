"""
ORL人脸数据集下载脚本

从 Kaggle 平台下载 AT&T Laboratories Cambridge 的人脸数据库（ORL数据集）。
数据集包含 40 个人，每人 10 张不同姿态/表情的灰度图像，分辨率 92×112。

下载后存放在 ./data/ 目录下，结构为：
    data/s1/1.pgm ~ 10.pgm
    data/s2/1.pgm ~ 10.pgm
    ...
    data/s40/1.pgm ~ 10.pgm

运行方式：python plot.py
前置条件：pip install kagglehub

作者: 李文煜
日期: 2026-03-11
"""

import kagglehub
import os

# 数据集下载目标路径（相对于当前脚本所在目录）
target_path = "./data"

# 确保目标目录存在，不存在则自动创建
os.makedirs(target_path, exist_ok=True)

# 通过 kagglehub 从 Kaggle 下载 ORL 人脸数据集
# handle 参数为 Kaggle 上的数据集唯一标识符
dataset_path = kagglehub.dataset_download(
    handle="sarfarazansari/att-database-of-faces",
    path=target_path
)

# 打印下载结果并验证文件是否存在
print("数据集下载成功！")
print("数据集本地路径:", dataset_path)
print("路径是否存在:", os.path.exists(dataset_path))
