"""
对student数据集进行2-8分割，8成训练2成测试，使用决策树预测学生G3的成绩

李文煜 1120233042
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split  # 数据集分割工具，将数据随机拆分为训练集和测试集
from sklearn.preprocessing import LabelEncoder        # 标签编码器，把文字类别（如"GP","MS"）转成数字（如0,1）
from sklearn.tree import DecisionTreeRegressor        # 决策树回归模型，用于预测连续数值（如G3分数）
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error  # 模型评估指标
#   - mean_squared_error: 均方误差(MSE)，预测值和真实值差值的平方的平均，越小越好
#   - r2_score: 决定系数(R²)，1表示完美预测，0表示和均值一样差，负数表示比均值还差
#   - mean_absolute_error: 平均绝对误差(MAE)，预测值和真实值差值绝对值的平均，直观易懂
from sklearn.tree import plot_tree           # 决策树可视化工具，直接把树结构画出来
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体，否则图表中的中文会显示为方块
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 1.读取数据
print("=" * 60)
print("决策树预测学生G3成绩")
print("=" * 60)


data = pd.read_csv("./student.csv")

print(f"\n数据集形状: {data.shape}")
print(f"即: {data.shape[0]}名学生, {data.shape[1]}个特征")
print(f"\n所有列名: {data.columns.tolist()}")

# 2.数据预处理
print("\n" + "=" * 60)
print("数据预处理")
print("=" * 60)

# 3.1分离特征(X)和目标标签(y) ---
# 要预测的是G3（期末成绩），所以G3是目标变量
# G1（一期成绩）和G2（二期成绩）是G3之前的成绩，包含了很强的信息
# 这里我把G1和G2也保留作为特征，看模型能学到什么
target = 'G3'                               # 目标列名
X = data.drop(columns=[target])             # drop() — 删除指定列，剩下的作为特征X
y = data[target]                            # 取出G3列作为目标y

print(f"\n特征数量: {X.shape[1]}")
print(f"样本数量: {X.shape[0]}")

# 3.2 类别特征编码
# 决策树只能处理数值数据，所以需要把文字类别转成数字
# 比如 "sex"列的 "F"→0, "M"→1

# select_dtypes(include=['object']) — 筛选出所有文字类型的列
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
print(f"需要编码的类别列({len(categorical_cols)}个): {categorical_cols}")

# LabelEncoder() — 创建一个编码器实例
# 它会自动找到列中所有不同的值，按字母顺序编号0,1,2...
# 例如 Mjob列有 "at_home","health","other","services","teacher" → 0,1,2,3,4
label_encoders = {}                          # 用字典保存每个列的编码器，方便后面还原
for col in categorical_cols:
    le = LabelEncoder()                      # 为当前列创建一个新的编码器
    X[col] = le.fit_transform(X[col])        # fit_transform() — 先学习(fit)有哪些类别，再转换(transform)成数字
    label_encoders[col] = le                 # 保存编码器，以便将来需要时反向转换
    # 例如: X['sex'] 从 ['F','M','F',...] 变成 [0,1,0,...]

print("\n编码后数据前5行:")
print(X.head())

# 3.3 检查缺失值
# isnull().sum() — 统计每列有多少个空值(缺失值)
missing = X.isnull().sum()
if missing.sum() > 0:
    print(f"\n缺失值统计:\n{missing[missing > 0]}")
    # fillna() — 用中位数填充缺失值，中位数比均值更不容易受极端值影响
    for col in X.columns:
        if X[col].isnull().sum() > 0:
            X[col].fillna(X[col].median(), inplace=True)  # median() — 计算中位数
            print(f"  已用中位数填充 {col} 的缺失值")
else:
    print("\n无缺失值，数据完整！")

# 4. 数据集分割（2:8 = 测试:训练）
print("\n" + "=" * 60)
print("数据集分割")
print("=" * 60)

# train_test_split() — 将数据随机拆分为训练集和测试集
# 参数说明:
#   X, y       — 特征矩阵和目标向量
#   test_size=0.2  — 测试集占20%，即训练集占80%
#   random_state=42 — 随机种子，固定后每次运行结果一致（42是编程界的传统选择）
#   返回值: X_train(训练特征), X_test(测试特征), y_train(训练目标), y_test(测试目标)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"训练集大小: {X_train.shape[0]}条 ({X_train.shape[0]/len(X)*100:.1f}%)")
print(f"测试集大小: {X_test.shape[0]}条 ({X_test.shape[0]/len(X)*100:.1f}%)")

#  5. 训练决策树模型
print("\n" + "=" * 60)
print("训练决策树模型")
print("=" * 60)

# DecisionTreeRegressor() — 创建一棵决策树回归模型
# 因为G3是0-20的连续分数，不是类别，所以用回归树而不是分类树
# 参数说明:
#   max_depth=5      — 树的最大深度(层数)，限制深度可以防止过拟合
#                       深度太大→过拟合(死记硬背)，深度太小→欠拟合(学不到东西)
#   min_samples_split=5 — 内部节点至少需要5个样本才允许继续分裂
#   min_samples_leaf=3  — 叶子节点至少包含3个样本，防止叶子太"纯"导致过拟合
#   random_state=42     — 随机种子，保证可复现
model = DecisionTreeRegressor(
    max_depth=5,
    min_samples_split=5,
    min_samples_leaf=3,
    random_state=42
)

# model.fit() — 训练模型，让决策树从训练数据中学习规律
# 内部过程: 自动选择最佳的特征和分裂点，递归构建决策树
model.fit(X_train, y_train)

print(f"决策树深度: {model.get_depth()}")      # get_depth() — 获取树的实际深度
print(f"叶子节点数: {model.get_n_leaves()}")    # get_n_leaves() — 获取叶子节点数量

# 6.模型评估
print("\n" + "=" * 60)
print("模型评估")
print("=" * 60)

# 用训练好的模型对新数据进行预测
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

# 计算各种评估指标

# R²分数 (决定系数) — 越接近1越好
# 衡量模型解释了多少数据变异，1.0=完美，0.0=和预测均值一样
train_r2 = r2_score(y_train, y_train_pred)   # 训练集R²
test_r2 = r2_score(y_test, y_test_pred)      # 测试集R²

# MAE (平均绝对误差) — 预测平均偏离多少分
# 比如 MAE=1.5 表示预测值平均和真实值差1.5分，直观好理解
train_mae = mean_absolute_error(y_train, y_train_pred)
test_mae = mean_absolute_error(y_test, y_test_pred)

# RMSE (均方根误差) — 对大误差更敏感的指标
# 比 MAE 更关注离谱的预测，值越小越好
train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))  # np.sqrt() — 求平方根
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

print(f"\n{'指标':<12} {'训练集':>10} {'测试集':>10}")
print("-" * 35)
print(f"{'R-squared':<12} {train_r2:>10.4f} {test_r2:>10.4f}")
print(f"{'MAE':<12} {train_mae:>10.4f} {test_mae:>10.4f}")
print(f"{'RMSE':<12} {train_rmse:>10.4f} {test_rmse:>10.4f}")

#  7.可视化

# 图1: 实际值 vs 预测值散点图
# 理想情况下，所有点应该落在y=x这条对角线上
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 训练集散点图
axes[0].scatter(y_train, y_train_pred, alpha=0.6, c='steelblue', edgecolors='k', linewidth=0.5)
# plot() 在图上画一条参考线 y=x，如果预测完美，所有点都会落在这条线上
axes[0].plot([y_train.min(), y_train.max()],
             [y_train.min(), y_train.max()],
             'r--', linewidth=2, label='完美预测线 (y=x)')
axes[0].set_xlabel('实际G3成绩', fontsize=13)
axes[0].set_ylabel('预测G3成绩', fontsize=13)
axes[0].set_title(f'训练集: 实际 vs 预测 (R-squared={train_r2:.4f})', fontsize=14, fontweight='bold')
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# 测试集散点图
axes[1].scatter(y_test, y_test_pred, alpha=0.6, c='coral', edgecolors='k', linewidth=0.5)
axes[1].plot([y_test.min(), y_test.max()],
             [y_test.min(), y_test.max()],
             'r--', linewidth=2, label='完美预测线 (y=x)')
axes[1].set_xlabel('实际G3成绩', fontsize=13)
axes[1].set_ylabel('预测G3成绩', fontsize=13)
axes[1].set_title(f'测试集: 实际 vs 预测 (R-squared={test_r2:.4f})', fontsize=14, fontweight='bold')
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fig1_actual_vs_predicted.png', dpi=300, bbox_inches='tight')
print(f"\n已保存图1: fig1_actual_vs_predicted.png")
plt.show()

# 图2: 特征重要性排序图
# model.feature_importances_ — 返回每个特征的重要性分数（总和为1）
# 分数越高，说明这个特征对预测结果的贡献越大
importances = model.feature_importances_                 # 获取特征重要性数组
feature_names = X.columns                                # 获取特征名称
indices = np.argsort(importances)[::-1]                  # argsort()返回排序后的索引，[::-1]翻转使其从大到小

# 只显示重要性 > 0.01 的特征，避免图表太拥挤
important_mask = importances > 0.01
n_important = important_mask.sum()

plt.figure(figsize=(10, max(6, n_important * 0.4)))

# plt.barh() — 画水平柱状图
plt.barh(
    range(n_important),                                    # y轴位置
    importances[indices][:n_important][::-1],              # x轴值（重要性分数），[::-1]让最大值在最上面
    tick_label=feature_names[indices][:n_important][::-1], # y轴标签（特征名）
    color='steelblue',
    edgecolor='black',
    linewidth=0.5
)
plt.xlabel('特征重要性', fontsize=13)
plt.title('决策树特征重要性排序（重要性 > 0.01）', fontsize=14, fontweight='bold')
plt.grid(True, axis='x', alpha=0.3)

# 在柱子末端标注数值
for i, v in enumerate(importances[indices][:n_important][::-1]):
    plt.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('fig2_feature_importance.png', dpi=300, bbox_inches='tight')
print(f"已保存图2: fig2_feature_importance.png")
plt.show()

# 图3: 决策树结构可视化
plt.figure(figsize=(20, 12))

# plot_tree() — 将决策树的结构画出来
# 参数说明:
#   model       — 训练好的决策树模型
#   feature_names — 特征名列表，显示在节点上
#   filled=True — 根据值填充颜色，不同值的节点颜色不同
#   rounded=True — 节点框为圆角
#   fontsize=8  — 字体大小
#   max_depth=3  — 只显示前3层（完整树太密看不清）
plot_tree(
    model,
    feature_names=feature_names,
    filled=True,
    rounded=True,
    fontsize=8,
    max_depth=3
)
plt.title('决策树结构（前3层）', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('fig3_decision_tree.png', dpi=300, bbox_inches='tight')
print(f"已保存图3: fig3_decision_tree.png")
plt.show()

#  图4: 预测误差分布直方图
# 误差 = 预测值 - 实际值，正值表示预测偏高，负值表示预测偏低
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 训练集误差分布
train_errors = y_train_pred - y_train.values    # .values 把 pandas Series 转为 numpy 数组
axes[0].hist(train_errors, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
# axvline() — 画一条垂直线，标注误差=0的位置
axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2, label='零误差线')
axes[0].set_xlabel('预测误差 (预测值 - 实际值)', fontsize=12)
axes[0].set_ylabel('样本数量', fontsize=12)
axes[0].set_title('训练集预测误差分布', fontsize=14, fontweight='bold')
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# 测试集误差分布
test_errors = y_test_pred - y_test.values
axes[1].hist(test_errors, bins=15, color='coral', edgecolor='black', alpha=0.7)
axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2, label='零误差线')
axes[1].set_xlabel('预测误差 (预测值 - 实际值)', fontsize=12)
axes[1].set_ylabel('样本数量', fontsize=12)
axes[1].set_title('测试集预测误差分布', fontsize=14, fontweight='bold')
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fig4_error_distribution.png', dpi=300, bbox_inches='tight')
print(f"已保存图4: fig4_error_distribution.png")
plt.show()

#  8. 结果汇总
print("\n" + "=" * 60)
print("结果汇总")
print("=" * 60)
print(f"\n模型: 决策树回归 (max_depth=5)")
print(f"数据集: student.csv ({len(data)}名学生)")
print(f"训练集: {X_train.shape[0]}条 (80%)")
print(f"测试集: {X_test.shape[0]}条 (20%)")
print(f"\n测试集性能:")
print(f"  R-squared: {test_r2:.4f}  (模型解释了{test_r2*100:.1f}%的成绩变异)")
print(f"  MAE:       {test_mae:.4f}  (预测平均偏差{test_mae:.1f}分)")
print(f"  RMSE:      {test_rmse:.4f}")

# 找出最重要的3个特征
top3_idx = indices[:3]
print(f"\n最重要的3个特征:")
for i, idx in enumerate(top3_idx):
    print(f"  {i+1}. {feature_names[idx]} (重要性: {importances[idx]:.4f})")

print(f"\n生成的图表:")
print(f"  1. fig1_actual_vs_predicted.png — 实际值 vs 预测值散点图")
print(f"  2. fig2_feature_importance.png — 特征重要性排序图")
print(f"  3. fig3_decision_tree.png — 决策树结构可视化")
print(f"  4. fig4_error_distribution.png — 预测误差分布直方图")
