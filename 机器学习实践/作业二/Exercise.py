"""
对vaccine数据集进行多项式回归预测，对比线性回归和2-5次多项式拟合效果

李文煜 1120233042
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression               # 线性回归模型
from sklearn.preprocessing import PolynomialFeatures            # 多项式特征转换器，把x扩展为[x, x^2, x^3, ...]
from sklearn.pipeline import make_pipeline                      # 管道工具，把多个步骤封装成一个整体
from sklearn.metrics import mean_absolute_error, mean_squared_error  # MAE和MSE评估指标
import warnings

warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']  # 中文字体设置
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 1.读取数据
print("=" * 60)
print("多项式回归预测疫苗数据")
print("=" * 60)

data = pd.read_csv("./vaccine.csv")  # 读取CSV文件，返回DataFrame
print(f"\n数据集形状: {data.shape}")
print(f"前5行:")
print(data.head())

X = data['Year'].values    # .values 将DataFrame列转为numpy数组
y = data['Values'].values

print(f"\n年份范围: {X.min()} - {X.max()}")
print(f"接种率范围: {y.min():.2f} - {y.max():.2f}")

# 2.数据集分割（2:8 = 测试:训练）
print("\n" + "=" * 60)
print("数据集分割")
print("=" * 60)

split_idx = int(len(X) * 0.8)  # int() — 取整，80%的位置作为分界点
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"训练集: {len(X_train)}条 (80%), 年份: {X_train[0]}-{X_train[-1]}")
print(f"测试集: {len(X_test)}条 (20%), 年份: {X_test[0]}-{X_test[-1]}")

# reshape(len, 1) — 将一维数组转为二维列向量，sklearn要求输入特征是二维的
X_train = X_train.reshape(len(X_train), 1)  # (27, 1)
X_test = X_test.reshape(len(X_test), 1)     # (7, 1)

# 3.线性回归（1次，基线模型）
print("\n" + "=" * 60)
print("线性回归预测")
print("=" * 60)

# LinearRegression() — 创建线性回归模型，拟合 y = w*x + b
model = LinearRegression()
# fit() — 训练模型，学习系数w和截距b
model.fit(X_train, y_train.reshape(len(y_train), 1))
# predict() — 用训练好的模型预测测试集
results = model.predict(X_test.reshape(len(X_test), 1))  # 返回预测值二维数组

print(f"\n线性回归预测结果:")
for i, (year, pred, real) in enumerate(zip(X_test.flatten(), results.flatten(), y_test)):
    print(f"  {int(year)}年: 预测={pred:.2f}, 实际={real:.2f}, 误差={pred-real:.2f}")

# flatten() — 将多维数组展平为一维，因为results是(n,1)的二维数组
mae_linear = mean_absolute_error(y_test, results.flatten())  # MAE — 平均绝对误差
mse_linear = mean_squared_error(y_test, results.flatten())   # MSE — 均方误差
print(f"\n线性回归平均绝对误差: {mae_linear}")
print(f"线性回归均方误差: {mse_linear}")

# 4.二次多项式回归
print("\n" + "=" * 60)
print("二次多项式回归")
print("=" * 60)

# PolynomialFeatures(degree=2) — 将特征x扩展为 [x, x^2]
# include_bias=False 不添加常数列1（由LinearRegression的截距处理）
poly_features_2 = PolynomialFeatures(degree=2, include_bias=False)

# fit_transform() — 先fit学习特征范围，再transform转换数据
# 把 [x] 变成 [x, x^2]，例如 [1990] → [1990, 3960100]
poly_X_train_2 = poly_features_2.fit_transform(X_train)
poly_X_test_2 = poly_features_2.fit_transform(X_test)

print(f"转换后训练集特征形状: {poly_X_train_2.shape}")  # (27, 2)，即[x, x^2]两列

model_2 = LinearRegression()
model_2.fit(poly_X_train_2, y_train.reshape(len(y_train), 1))  # 用多项式特征训练

# 通过方程对测试集进行预测
results_2 = model_2.predict(poly_X_test_2)
print(f"\n二次多项式回归预测结果:")
for i, (year, pred, real) in enumerate(zip(X_test.flatten(), results_2.flatten(), y_test)):
    print(f"  {int(year)}年: 预测={pred:.2f}, 实际={real:.2f}, 误差={pred-real:.2f}")

mae_2 = mean_absolute_error(y_test, results_2.flatten())
mse_2 = mean_squared_error(y_test, results_2.flatten())
print(f"\n二次多项式回归平均绝对误差: {mae_2}")
print(f"二次多项式回归均方误差: {mse_2}")

# 5.三、四、五次多项式回归（使用make_pipeline）
print("\n" + "=" * 60)
print("三、四、五次多项式回归")
print("=" * 60)

# make_pipeline() — 将多个处理步骤封装成一个管道对象
# 等价于手动调用 PolynomialFeatures → LinearRegression
# 好处: 只需调用一次 fit() 和 predict()，内部自动按顺序执行每一步
for m in [3, 4, 5]:
    model = make_pipeline(
        PolynomialFeatures(m, include_bias=False),  # 第一步: 特征扩展为 [x, x^2, ..., x^m]
        LinearRegression()                          # 第二步: 线性回归拟合
    )
    model.fit(X_train, y_train)           # fit() — 管道自动完成特征转换+模型训练
    y_pred = model.predict(X_test)        # predict() — 管道自动完成特征转换+预测
    mae = mean_absolute_error(y_test, y_pred.flatten())
    mse = mean_squared_error(y_test, y_pred.flatten())
    print(f"{m}次多项式回归平均绝对误差: {mae}")
    print(f"{m}次多项式回归均方误差: {mse}")

# 6.绘制MSE随多项式次数的变化曲线
print("\n" + "=" * 60)
print("MSE随多项式次数变化曲线")
print("=" * 60)

mse_list = []  # 存储各次数对应的MSE
m = 1          # 起始次数
m_max = 10     # 最大次数

while m <= m_max:
    model = make_pipeline(
        PolynomialFeatures(m, include_bias=False),
        LinearRegression()
    )
    model.fit(X_train, y_train)
    pre_y = model.predict(X_test)
    # 计算m次多项式的均方误差
    mse_list.append(mean_squared_error(y_test, pre_y.flatten()))
    m = m + 1

# 绘制折线图+散点图
plt.figure(figsize=(10, 6))
plt.plot([i for i in range(1, m_max + 1)], mse_list, 'r')   # 红色折线
plt.scatter([i for i in range(1, m_max + 1)], mse_list)      # 散点叠加
plt.title('MSE of m degree of polynomial regression')
plt.xlabel('m')       # x标签表示多项式次数
plt.ylabel('MSE')     # y标签表示对应的均方误差
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('fig1_mse_vs_degree.png', dpi=300, bbox_inches='tight')
print("已保存图1: fig1_mse_vs_degree.png")
plt.show()

# 找出最优次数
best_m = mse_list.index(min(mse_list)) + 1  # index() — 找到最小值的索引，+1因为从1开始
print(f"\n最优多项式次数: {best_m}次 (MSE最小={min(mse_list):.4f})")

# 7.可视化: 各模型拟合曲线对比
print("\n" + "=" * 60)
print("生成拟合曲线对比图")
print("=" * 60)

x_smooth = np.linspace(X.flatten().min(), X.flatten().max(), 300).reshape(-1, 1)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
degrees = [1, 2, 3, 4, 5]
colors = ['gray', 'steelblue', 'coral', 'green', 'purple']

for idx, (degree, color) in enumerate(zip(degrees, colors)):
    ax = axes[idx // 3][idx % 3]

    # 根据次数构建模型
    if degree == 1:
        mdl = LinearRegression()
        mdl.fit(X_train, y_train)
    else:
        mdl = make_pipeline(
            PolynomialFeatures(degree, include_bias=False),
            LinearRegression()
        )
        mdl.fit(X_train, y_train)

    y_smooth = mdl.predict(x_smooth)
    y_test_pred = mdl.predict(X_test)
    mae = mean_absolute_error(y_test, y_test_pred.flatten())

    ax.scatter(X_train, y_train, c='lightgray', alpha=0.5, s=30, label='训练数据')
    ax.scatter(X_test, y_test, c='red', alpha=0.8, s=40, label='测试数据')
    ax.plot(x_smooth.flatten(), y_smooth, color=color, linewidth=2.5,
            label=f'{degree}次多项式 (MAE={mae:.2f})')

    ax.set_xlabel('年份', fontsize=11)
    ax.set_ylabel('接种率(%)', fontsize=11)
    ax.set_title(f'{degree}次多项式回归', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

# 第6个子图: 所有曲线叠加对比
ax_all = axes[1][2]
ax_all.scatter(X.flatten(), y, c='black', s=30, zorder=5, label='原始数据')
for degree, color in zip(degrees, colors):
    if degree == 1:
        mdl = LinearRegression()
    else:
        mdl = make_pipeline(
            PolynomialFeatures(degree, include_bias=False),
            LinearRegression()
        )
    mdl.fit(X_train, y_train)
    ax_all.plot(x_smooth.flatten(), mdl.predict(x_smooth), color=color, linewidth=1.5,
                label=f'{degree}次')
ax_all.set_xlabel('年份', fontsize=11)
ax_all.set_ylabel('接种率(%)', fontsize=11)
ax_all.set_title('所有模型叠加对比', fontsize=13, fontweight='bold')
ax_all.legend(fontsize=8)
ax_all.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fig2_fitting_comparison.png', dpi=300, bbox_inches='tight')
print("已保存图2: fig2_fitting_comparison.png")
plt.show()

# 8.结果汇总
print("\n" + "=" * 60)
print("结果汇总")
print("=" * 60)
print(f"数据集: vaccine.csv ({len(data)}条数据)")
print(f"训练集: {len(X_train)}条 (80%), 测试集: {len(X_test)}条 (20%)")
print(f"\n各模型测试集误差:")
print(f"  线性回归(1次): MAE={mae_linear:.4f}, MSE={mse_linear:.4f}")
print(f"  2次多项式:     MAE={mae_2:.4f}, MSE={mse_2:.4f}")

# 重新计算3-5次用于汇总
for m in [3, 4, 5]:
    mdl = make_pipeline(PolynomialFeatures(m, include_bias=False), LinearRegression())
    mdl.fit(X_train, y_train)
    yp = mdl.predict(X_test).flatten()
    print(f"  {m}次多项式:     MAE={mean_absolute_error(y_test, yp):.4f}, MSE={mean_squared_error(y_test, yp):.4f}")

print(f"\n最优多项式次数: {best_m}次 (MSE最小={min(mse_list):.4f})")
