"""
基于乐学学生在C语言编程课程上的行为，使用SVM预测学生的成绩等级

基本版：使用mooc_set0作业版.xlsx，提取特征，SVM调参预测成绩等级
进阶版见 exercise2.py

李文煜 1120233042
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV  # GridSearchCV — 网格搜索自动调参
from sklearn.preprocessing import StandardScaler                    # 标准化器，将特征缩放到均值0方差1
from sklearn.svm import SVC                                        # SVM分类器（Support Vector Classification）
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score  # 分类评估指标
from sklearn.metrics import ConfusionMatrixDisplay                 # 混淆矩阵可视化
import warnings

warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 1.读取数据
print("=" * 60)
print("SVM预测学生成绩等级")
print("=" * 60)

data = pd.read_excel("./mooc_set0作业版.xlsx")  # read_excel() — 读取Excel文件
print(f"\n数据集形状: {data.shape}")
print(f"列名: {data.columns.tolist()}")
print(f"\n前5行:")
print(data.head())

# 2.数据预处理
print("\n" + "=" * 60)
print("数据预处理")
print("=" * 60)

# 处理缺失值: 平均提交时间有1个NaN，用中位数填充
print(f"\n缺失值统计:")
print(data.isnull().sum()[data.isnull().sum() > 0])
data['平均提交时间'].fillna(data['平均提交时间'].median(), inplace=True)  # fillna() — 填充缺失值

# 分离特征和目标
X = data.drop(columns=['userid', '考试成绩'])  # 去掉userid(无意义)和考试成绩(目标)
y_raw = data['考试成绩']

print(f"\n特征列: {X.columns.tolist()}")
print(f"成绩范围: {y_raw.min():.1f} - {y_raw.max():.1f}")
print(f"成绩分布:")
print(y_raw.describe())

# 3.构造标签（label自定义）
# 将连续成绩分为4个等级：不及格(<60)、及格(60-75)、良好(75-90)、优秀(>=90)
print("\n" + "=" * 60)
print("构造成绩等级标签")
print("=" * 60)

def grade_to_label(score):
    """将百分制成绩转为等级标签"""
    if score < 60:
        return 0  # 不及格
    elif score < 75:
        return 1  # 及格
    elif score < 90:
        return 2  # 良好
    else:
        return 3  # 优秀

y = y_raw.apply(grade_to_label)  # apply() — 对每个元素应用函数

# 统计各等级人数
label_names = ['不及格(<60)', '及格(60-75)', '良好(75-90)', '优秀(>=90)']
print(f"\n各等级分布:")
for i, name in enumerate(label_names):
    count = (y == i).sum()
    print(f"  {name}: {count}人 ({count/len(y)*100:.1f}%)")

# 4.特征标准化 + 数据分割
print("\n" + "=" * 60)
print("特征标准化与数据分割")
print("=" * 60)

# StandardScaler() — 将每个特征缩放为均值0、标准差1
# SVM对特征尺度敏感，不标准化会导致数值大的特征主导模型
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # fit_transform() — 计算均值方差并转换

# train_test_split() — 2:8分割
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)
# stratify=y — 保证训练集和测试集中各等级的比例一致

print(f"训练集: {len(X_train)}条 (80%)")
print(f"测试集: {len(X_test)}条 (20%)")

# 5.SVM模型训练 + 网格搜索调参
print("\n" + "=" * 60)
print("SVM模型训练与调参")
print("=" * 60)

# GridSearchCV() — 网格搜索交叉验证，自动尝试所有参数组合，选出最优
# 参数说明:
#   estimator — 基础模型
#   param_grid — 要搜索的参数字典，key是参数名，value是候选值列表
#   cv=5 — 5折交叉验证，数据分5份，轮流用4份训练1份验证
#   scoring='accuracy' — 用准确率作为评估标准
#   n_jobs=-1 — 使用所有CPU核心并行加速

# SVC() — 支持向量机分类器
# 参数说明:
#   C — 正则化参数，越大模型越不允许分错（可能过拟合），越小越宽容
#   kernel — 核函数类型:
#     'linear' — 线性核，只能分线性可分的数据
#     'rbf' — 径向基核(高斯核)，可以处理非线性边界，最常用
#   gamma — 核函数系数，控制单个样本的影响范围，越大越容易过拟合

param_grid = {
    'C': [0.1, 1, 10, 100],           # 正则化参数候选值
    'kernel': ['linear', 'rbf'],       # 核函数候选
    'gamma': ['scale', 'auto']         # gamma候选，'scale'=1/(n_features*var)
}

grid_search = GridSearchCV(
    estimator=SVC(random_state=42),
    param_grid=param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)  # fit() — 执行网格搜索，自动训练所有参数组合

print(f"\n最优参数: {grid_search.best_params_}")          # best_params_ — 最优参数组合
print(f"最优交叉验证准确率: {grid_search.best_score_:.4f}")  # best_score_ — 最优CV分数

# 用最优模型预测
best_model = grid_search.best_estimator_  # best_estimator_ — 最优参数训练好的模型
y_pred = best_model.predict(X_test)       # predict() — 预测测试集

# 6.模型评估
print("\n" + "=" * 60)
print("模型评估")
print("=" * 60)

# accuracy_score() — 准确率 = 预测正确的数量 / 总数量
acc = accuracy_score(y_test, y_pred)
print(f"\n测试集准确率: {acc:.4f}")

# classification_report() — 输出每个类别的精确率、召回率、F1分数
# precision(精确率) — 预测为该类中有多少是对的
# recall(召回率) — 实际为该类中有多少被找到了
# f1-score — 精确率和召回率的调和平均
print(f"\n分类报告:")
print(classification_report(y_test, y_pred, target_names=label_names))

# confusion_matrix() — 混淆矩阵，行=真实标签，列=预测标签
cm = confusion_matrix(y_test, y_pred)
print(f"混淆矩阵:\n{cm}")

# 7.可视化
print("\n" + "=" * 60)
print("生成可视化图表")
print("=" * 60)

# 图1: 混淆矩阵热力图
fig, ax = plt.subplots(figsize=(8, 6))
# ConfusionMatrixDisplay — sklearn自带的混淆矩阵可视化工具
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label_names)
disp.plot(ax=ax, cmap='Blues', values_format='d')  # cmap='Blues' 蓝色渐变
plt.title('SVM混淆矩阵', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('fig1_confusion_matrix.png', dpi=300, bbox_inches='tight')
print("已保存图1: fig1_confusion_matrix.png")
plt.show()

# 图2: 各类别分布 + 预测准确率对比
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 左图: 各等级人数分布
train_counts = [(y_train == i).sum() for i in range(4)]
test_counts = [(y_test == i).sum() for i in range(4)]
x_pos = np.arange(4)

ax1.bar(x_pos - 0.2, train_counts, 0.4, label='训练集', color='steelblue', edgecolor='black')
ax1.bar(x_pos + 0.2, test_counts, 0.4, label='测试集', color='coral', edgecolor='black')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(label_names, fontsize=10)
ax1.set_ylabel('人数', fontsize=12)
ax1.set_title('各等级人数分布', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, axis='y', alpha=0.3)

# 右图: 各等级预测准确率
class_acc = []
for i in range(4):
    mask = y_test == i
    if mask.sum() > 0:
        class_acc.append((y_pred[mask] == i).mean())
    else:
        class_acc.append(0)

bars = ax2.bar(label_names, class_acc, color=['#e74c3c', '#f39c12', '#2ecc71', '#3498db'],
               edgecolor='black')
ax2.set_ylabel('准确率', fontsize=12)
ax2.set_title('各等级预测准确率', fontsize=14, fontweight='bold')
ax2.set_ylim(0, 1.1)
ax2.grid(True, axis='y', alpha=0.3)
for bar, acc_val in zip(bars, class_acc):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f'{acc_val:.2f}', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('fig2_distribution_and_accuracy.png', dpi=300, bbox_inches='tight')
print("已保存图2: fig2_distribution_and_accuracy.png")
plt.show()

# 图3: SVM参数搜索热力图
cv_results = pd.DataFrame(grid_search.cv_results_)  # cv_results_ — 所有参数组合的CV结果

# 只取rbf核的结果画热力图
rbf_results = cv_results[cv_results['param_kernel'] == 'rbf']
# pivot_table() — 透视表，行=gamma, 列=C, 值=平均测试分数
pivot = rbf_results.pivot_table(
    index='param_gamma', columns='param_C', values='mean_test_score'
)

fig, ax = plt.subplots(figsize=(8, 5))
# imshow() — 将矩阵显示为热力图
im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
ax.set_xlabel('C (正则化参数)', fontsize=12)
ax.set_ylabel('gamma', fontsize=12)
ax.set_title('SVM参数搜索热力图 (RBF核, 5折CV准确率)', fontsize=13, fontweight='bold')

for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f'{pivot.values[i, j]:.4f}', ha='center', va='center', fontsize=11)

plt.colorbar(im, ax=ax, label='准确率')
plt.tight_layout()
plt.savefig('fig3_param_heatmap.png', dpi=300, bbox_inches='tight')
print("已保存图3: fig3_param_heatmap.png")
plt.show()

# 8.结果汇总
print("\n" + "=" * 60)
print("结果汇总")
print("=" * 60)
print(f"模型: SVM ({grid_search.best_params_['kernel']}核)")
print(f"最优参数: C={grid_search.best_params_['C']}, gamma={grid_search.best_params_['gamma']}")
print(f"训练集: {len(X_train)}条 (80%)")
print(f"测试集: {len(X_test)}条 (20%)")
print(f"\n测试集准确率: {acc:.4f}")
print(f"标签设置: 不及格(<60)=0, 及格(60-75)=1, 良好(75-90)=2, 优秀(>=90)=3")
