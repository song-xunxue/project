# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

模式识别课程实验项目，包含三个独立实验，每个实验位于独立目录中，互不依赖。

| 目录 | 实验 | 核心算法 | 数据集 |
|------|------|----------|--------|
| `FaceRecognitionOnPCA/` | 实验一 | PCA降维 + 三种分类器 | ORL人脸库 (40人×10张, 92×112 PGM) |
| `Adaboost/` | 实验二 | 手动AdaBoost（二分类 + SAMME多分类） | Wine Quality (UCI, ~6k条) |
| `LeNet/` | 实验三 | LeNet-5 CNN | FashionMNIST (torchvision自动下载) |

## Run Commands

每个实验独立运行，无统一构建系统。

```bash
# 实验一：PCA人脸识别
cd FaceRecognitionOnPCA
python plot.py              # 下载ORL人脸数据集（首次运行）
python model_train.py       # 训练PCA模型 → pca_model.pth
python run_all_test.py      # 运行全部三种分类方法并记录日志

# 实验二：AdaBoost
cd Adaboost
python plot.py              # 下载Wine Quality数据集（首次运行）
python run_all_test.py      # 运行二分类 + 多分类测试

# 实验三：LeNet
cd LeNet
python polt.py              # 下载FashionMNIST（首次运行，文件名原样为polt）
python model_train.py       # 训练LeNet (20 epochs) → best_model.pth
python test_model.py        # 测试模型
```

## Architecture

三个实验共享相同的代码组织模式：

```
plot.py / polt.py    → 数据下载与预处理
model.py             → 模型定义
model_train.py       → 训练脚本
test_model*.py       → 不同测试方法（可多个）
run_all_test.py      → 聚合运行所有测试
data/                → 数据存储目录
```

### 实验一 - PCA人脸识别
`plot.py` 通过 kagglehub 下载 ORL 人脸库 → `model.py` 实现PCA降维 (K=50) → 三种分类器对比：
- `test_model.py` — 欧氏距离 1-NN
- `test_model2.py` — 余弦相似度 1-NN
- `test_model3.py` — PCA + SVM

结果写入 `experiment_results.log`（带时间戳）。

### 实验二 - AdaBoost
`model.py` 包含 `AdaBoostBinary`（手动实现 DecisionStump 弱分类器）和 `AdaBoostMulti`（SAMME 算法 + sklearn DecisionTreeClassifier）。

### 实验三 - LeNet
经典 LeNet-5：Conv2D(6) → Sigmoid → AvgPool2D → Conv2D(16) → Sigmoid → AvgPool2D → FC(120) → FC(84) → FC(10)。训练曲线保存为 `train_val_curve.png`。

## Key Dependencies

```
torch, torchvision, torchsummary
numpy, pandas, matplotlib
opencv-python (cv2)
scikit-learn
ucimlrepo, kagglehub
```

无 requirements.txt，依赖需手动安装。

## Notes

- 数据目录 `data/` 和模型文件 `.pth` 未纳入 git 跟踪
- LeNet 目录下的 `polt.py` 是原始文件名（非拼写错误，勿改名）
- 实验结果日志：`FaceRecognitionOnPCA/experiment_results.log`
