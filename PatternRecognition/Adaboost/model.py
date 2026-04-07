"""
AdaBoost 模型定义模块

包含三种核心组件：
    1. DecisionStump    — 单层决策树弱分类器，用于二分类 AdaBoost
    2. AdaBoostBinary   — 基础 AdaBoost 二分类实现
    3. AdaBoostMulti    — SAMME 算法多分类实现

算法概述：
    - 二分类：手动实现 DecisionStump，通过穷举特征阈值寻找最优切分
    - 多分类：SAMME 扩展，弱分类器使用 sklearn DecisionTreeClassifier(max_depth=1)
    - 核心思想：迭代训练弱分类器，每轮关注上一轮分类错误的样本，最终加权投票

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 添加模块级文档字符串和详细中文注释
  2. 补充算法公式说明和参数文档
"""

import numpy as np
from sklearn.tree import DecisionTreeClassifier


class DecisionStump:
    """
    单层决策树（弱分类器）

    仅根据单个特征的单个阈值进行二分类决策，是 AdaBoost 最基础的弱学习器。
    每个实例存储最优切分的特征索引、阈值、极性和对应的 alpha 权重。

    属性:
        polarity (int): 不等号方向，1 表示小于阈值判为 -1，-1 表示大于阈值判为 -1
        feature_idx (int): 选定的最优划分特征索引
        threshold (float): 最优划分阈值
        alpha (float): 该弱分类器在最终集成中的投票权重
    """

    def __init__(self):
        self.polarity = 1       # 极性：决定不等号方向 (1 或 -1)
        self.feature_idx = None  # 最优划分特征索引
        self.threshold = None    # 最优划分阈值
        self.alpha = None        # 该弱分类器在最终模型中的投票权重

    def predict(self, X):
        """
        根据当前参数进行预测

        参数:
            X (np.ndarray): 输入样本，形状 (n_samples, n_features)

        返回:
            np.ndarray: 预测标签，+1 或 -1，形状 (n_samples,)
        """
        n_samples = X.shape[0]
        X_column = X[:, self.feature_idx]
        predictions = np.ones(n_samples)

        # 根据极性和阈值进行分类：
        # polarity=1 时，特征值 < 阈值的样本判为 -1
        # polarity=-1 时，特征值 > 阈值的样本判为 -1
        if self.polarity == 1:
            predictions[X_column < self.threshold] = -1
        else:
            predictions[X_column > self.threshold] = -1

        return predictions


class AdaBoostBinary:
    """
    基础 AdaBoost 二分类器

    使用手动实现的 DecisionStump 作为弱分类器，通过迭代训练和加权投票
    实现二分类任务。标签需为 {-1, +1}。

    训练流程：
        1. 初始化样本权重为均匀分布
        2. 每轮穷举所有特征的候选阈值，找到加权误差最小的 DecisionStump
        3. 计算弱分类器权重 alpha = 0.5 * ln((1-err)/err)
        4. 更新样本权重：增大被错分样本的权重，减小被正确分类样本的权重
        5. 预测时加权求和所有弱分类器输出，取符号作为最终结果

    参数:
        n_clf (int): 弱分类器的最大数量，默认 30

    属性:
        clfs (list[DecisionStump]): 训练好的弱分类器列表
    """

    def __init__(self, n_clf=30):
        self.n_clf = n_clf
        self.clfs = []

    def fit(self, X, y):
        """
        训练 AdaBoost 二分类模型

        参数:
            X (np.ndarray): 训练样本，形状 (n_samples, n_features)
            y (np.ndarray): 训练标签，取值 {-1, +1}，形状 (n_samples,)
        """
        n_samples, n_features = X.shape
        # 1. 初始化样本权重，均分
        w = np.full(n_samples, (1 / n_samples))
        self.clfs = []

        for _ in range(self.n_clf):
            clf = DecisionStump()
            min_error = float('inf')

            # 遍历所有特征寻找最佳切分点
            for feature_i in range(n_features):
                X_column = X[:, feature_i]
                # 在特征的极值之间均匀取 19 个候选阈值（避免边界值）
                min_val, max_val = X_column.min(), X_column.max()
                step = (max_val - min_val) / 20
                thresholds = [min_val + step * i for i in range(1, 20)]

                for threshold in thresholds:
                    # 尝试两种极性方向
                    for p in [1, -1]:
                        predictions = np.ones(n_samples)
                        if p == 1:
                            predictions[X_column < threshold] = -1
                        else:
                            predictions[X_column > threshold] = -1

                        # 计算当前切分的加权误差
                        error = sum(w[y != predictions])

                        # 保留加权误差最小的决策树参数
                        if error < min_error:
                            clf.polarity = p
                            clf.threshold = threshold
                            clf.feature_idx = feature_i
                            min_error = error

            # 2. 计算弱分类器权重 alpha
            #    公式：alpha = 0.5 * ln((1 - err) / err)
            #    加上极小值 EPS 防止除零
            EPS = 1e-10
            clf.alpha = 0.5 * np.log((1.0 - min_error + EPS) / (min_error + EPS))

            # 3. 更新样本权重 w
            #    被正确分类的样本权重减小，被错分的样本权重增大
            #    公式：w_i *= exp(-alpha * y_i * h(x_i))
            predictions = clf.predict(X)
            w *= np.exp(-clf.alpha * y * predictions)
            w /= np.sum(w)  # 归一化，使权重之和为 1

            self.clfs.append(clf)

    def predict(self, X):
        """
        对输入样本进行预测

        将所有弱分类器的加权预测结果求和，取符号作为最终分类。

        参数:
            X (np.ndarray): 输入样本，形状 (n_samples, n_features)

        返回:
            np.ndarray: 预测标签，取值 {-1, +1}，形状 (n_samples,)
        """
        # 4. 汇总所有弱分类器的加权预测：H(x) = sign(Σ alpha_t * h_t(x))
        clf_preds = [clf.alpha * clf.predict(X) for clf in self.clfs]
        y_pred = np.sum(clf_preds, axis=0)
        return np.sign(y_pred)


class AdaBoostMulti:
    """
    SAMME 多分类 AdaBoost

    将 AdaBoost 扩展到多分类场景，使用 sklearn DecisionTreeClassifier(max_depth=1)
    作为弱分类器。与二分类版本的关键区别：

    - Alpha 公式增加 log(K-1) 修正项：alpha = ln((1-err)/err) + ln(K-1)
    - 当弱分类器误差 >= (K-1)/K 时提前停止（弱于随机猜测）
    - 预测时采用加权投票机制，选择累计得分最高的类别

    参数:
        n_clf (int): 弱分类器的最大数量，默认 30

    属性:
        clfs (list): 训练好的 sklearn DecisionTreeClassifier 列表
        alphas (list[float]): 各弱分类器的投票权重
        classes (np.ndarray): 训练集中出现的所有类别
    """

    def __init__(self, n_clf=30):
        self.n_clf = n_clf
        self.clfs = []
        self.alphas = []
        self.classes = None

    def fit(self, X, y):
        """
        训练 SAMME 多分类 AdaBoost 模型

        参数:
            X (np.ndarray): 训练样本，形状 (n_samples, n_features)
            y (np.ndarray): 训练标签，多类别整数值，形状 (n_samples,)
        """
        self.classes = np.unique(y)
        K = len(self.classes)  # 类别数
        n_samples = X.shape[0]
        w = np.full(n_samples, (1 / n_samples))  # 初始化权重为均匀分布

        for _ in range(self.n_clf):
            # 弱分类器使用 sklearn 的深度为 1 的 CART 树
            # 传入 sample_weight 使其关注当前权重下难以分类的样本
            clf = DecisionTreeClassifier(max_depth=1)
            clf.fit(X, y, sample_weight=w)
            predictions = clf.predict(X)

            # 1. 计算加权误差率：err = Σ(w_i * I(h(x_i) ≠ y_i)) / Σ(w_i)
            err = np.sum(w * (predictions != y)) / np.sum(w)

            # 若误差率大于 (K-1)/K，说明弱于随机猜测，提前停止训练
            if err >= 1.0 - (1.0 / K):
                break

            # 2. 计算 Alpha（SAMME 多分类专属公式）
            #    相比二分类多了一个 log(K-1) 项，用于补偿多分类的难度
            #    当 K=2 时退化为标准 AdaBoost 公式
            EPS = 1e-10
            alpha = np.log((1.0 - err + EPS) / (err + EPS)) + np.log(K - 1)

            # 3. 更新样本权重：增大被错分样本的权重
            w *= np.exp(alpha * (predictions != y))
            w /= np.sum(w)  # 归一化

            self.clfs.append(clf)
            self.alphas.append(alpha)

    def predict(self, X):
        """
        对输入样本进行多分类预测

        每个弱分类器对其预测的类别累加 alpha 得分，
        最终选择每个样本上累计得分最高的类别。

        参数:
            X (np.ndarray): 输入样本，形状 (n_samples, n_features)

        返回:
            np.ndarray: 预测类别标签，形状 (n_samples,)
        """
        n_samples = X.shape[0]
        # 构造类别得分矩阵：(n_samples, K)，记录每个样本在每个类别上的累计加权投票
        class_scores = np.zeros((n_samples, len(self.classes)))

        # 4. 累加各个弱分类器的加权投票
        for alpha, clf in zip(self.alphas, self.clfs):
            predictions = clf.predict(X)
            for i in range(n_samples):
                # 找到预测类别在 classes 数组中的索引，累加 alpha 得分
                class_idx = np.where(self.classes == predictions[i])[0][0]
                class_scores[i, class_idx] += alpha

        # 返回每个样本上得分最高的类别
        return self.classes[np.argmax(class_scores, axis=1)]
