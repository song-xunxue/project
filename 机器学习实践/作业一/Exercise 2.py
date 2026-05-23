#李文煜 1120233042

import numpy as np
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体和高质量显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 数据集
x = np.array([55, 71, 68, 87, 101, 87, 75, 78, 93, 73])
y = np.array([91, 101, 87, 109, 129, 98, 95, 101, 104, 93])

print("=" * 50)
print("练习二：一元线性回归（梯度下降）")
print(f"数据点数量：{len(x)}")

# 数据标准化
x_mean = np.mean(x)
x_std = np.std(x)
y_mean = np.mean(y)
y_std = np.std(y)

x_normalized = (x - x_mean) / x_std
y_normalized = (y - y_mean) / y_std


# 梯度下降算法
def gradient_descent(x, y, learning_rate=0.1, iterations=1000, verbose=True):
    """
    使用梯度下降求解线性回归参数
    """
    w0 = 0
    w1 = 0
    m = len(x)
    loss_history = []

    for i in range(iterations):
        y_pred = w0 + w1 * x

        # 计算损失（均方误差）
        loss = np.mean((y_pred - y) ** 2)
        loss_history.append(loss)

        # 计算梯度
        dw0 = (2 / m) * np.sum(y_pred - y)
        dw1 = (2 / m) * np.sum((y_pred - y) * x)

        # 更新参数
        w0 = w0 - learning_rate * dw0
        w1 = w1 - learning_rate * dw1

        if verbose and (i + 1) % 200 == 0:
            print(f"迭代 {i + 1:4d}, 损失值: {loss:.6f}")

    return w0, w1, loss_history


# 训练模型
print("\n开始训练...")
learning_rate = 0.1
iterations = 1000
w0_norm, w1_norm, loss_history = gradient_descent(
    x_normalized, y_normalized, learning_rate, iterations
)

# 参数反标准化
w1_original = w1_norm * (y_std / x_std)
w0_original = y_mean - w1_original * x_mean + y_std * w0_norm

print(f"\n最终模型参数：")
print(f"w0 = {w0_original:.4f}, w1 = {w1_original:.4f}")
print(f"回归方程：y = {w0_original:.4f} + {w1_original:.4f} * x")

# 预测和评估
y_pred = w0_original + w1_original * x
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - (ss_res / ss_tot)
print(f"R²分数: {r2:.4f}")

# ==================== 图1：拟合结果图（修改R²位置） ====================
plt.figure(figsize=(10, 6))

plt.scatter(x, y, color='red', s=80, alpha=0.7, label='原始数据点', zorder=3)

x_smooth = np.linspace(x.min(), x.max(), 100)
y_smooth = w0_original + w1_original * x_smooth

plt.plot(x_smooth, y_smooth, 'b-', linewidth=2.5, label='拟合直线', zorder=2)

# 添加误差连线
for i in range(len(x)):
    plt.plot([x[i], x[i]], [y[i], w0_original + w1_original * x[i]],
             'gray', linewidth=0.8, alpha=0.5, linestyle='--')

plt.xlabel('x', fontsize=14)
plt.ylabel('y', fontsize=14)
plt.title('一元线性回归拟合结果', fontsize=16, fontweight='bold')
plt.legend(fontsize=12, loc='lower right')  # 图例放在右下角
plt.grid(True, alpha=0.3)

# 修改R²位置 - 放在左上角更安全的位置
plt.text(0.02, 0.98, f'R² = {r2:.4f}',
         transform=plt.gca().transAxes,
         fontsize=13,
         fontweight='bold',
         verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8, edgecolor='black'))

plt.tight_layout()
plt.savefig('fig1_fitting_result.png', dpi=300, bbox_inches='tight')
print("\n已保存图1: fig1_fitting_result.png")
plt.show()

# ==================== 图2：Loss下降曲线（修正bug版） ====================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左图：完整的Loss下降曲线
axes[0].plot(range(1, len(loss_history) + 1), loss_history, 'b-', linewidth=2)
axes[0].set_xlabel('迭代次数', fontsize=14)
axes[0].set_ylabel('损失值 (MSE)', fontsize=14)
axes[0].set_title('Loss下降曲线 - 完整过程', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3)
axes[0].set_yscale('log')
axes[0].set_xlim(0, iterations)
axes[0].axhline(y=loss_history[-1], color='r', linestyle='--', linewidth=1, alpha=0.7)
axes[0].text(iterations * 0.7, loss_history[-1] * 1.1, f'最终损失: {loss_history[-1]:.6f}',
             fontsize=10, color='red')

# 右图：前200次迭代的Loss下降细节（修正bug）
n_iterations = min(200, len(loss_history))  # 取200和实际长度的最小值
axes[1].plot(range(1, n_iterations + 1), loss_history[:n_iterations], 'purple', linewidth=2)
axes[1].set_xlabel('迭代次数', fontsize=14)
axes[1].set_ylabel('损失值 (MSE)', fontsize=14)
axes[1].set_title(f'Loss下降曲线 - 初期细节 (前{n_iterations}次迭代)', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3)
axes[1].set_yscale('log')

plt.tight_layout()
plt.savefig('fig2_loss_curve.png', dpi=300, bbox_inches='tight')
print("已保存图2: fig2_loss_curve.png")
plt.show()

# ==================== 图3：不同学习率对比图 ====================
print("\n" + "=" * 50)
print("测试不同学习率的效果...")

learning_rates = [0.005, 0.01, 0.05, 0.1, 0.3, 0.5]
colors = ['blue', 'green', 'orange', 'red', 'purple', 'brown']
line_styles = ['-', '--', '-.', ':', '-', '--']

plt.figure(figsize=(12, 8))

final_losses = {}

for idx, lr in enumerate(learning_rates):
    print(f"\n测试学习率 = {lr}")
    _, _, loss_hist = gradient_descent(
        x_normalized, y_normalized,
        learning_rate=lr, iterations=500, verbose=False
    )
    final_loss = loss_hist[-1]
    final_losses[lr] = final_loss
    print(f"  迭代500次后损失值: {final_loss:.8f}")

    plt.plot(range(1, len(loss_hist) + 1), loss_hist,
             color=colors[idx], linewidth=2,
             linestyle=line_styles[idx],
             label=f'学习率 = {lr} (最终损失: {final_loss:.6f})')

plt.xlabel('迭代次数', fontsize=14)
plt.ylabel('损失值 (MSE)', fontsize=14)
plt.title('不同学习率下的损失下降曲线对比', fontsize=16, fontweight='bold')
plt.legend(fontsize=11, loc='upper right')
plt.grid(True, alpha=0.3)
plt.yscale('log')

# 设置合理的y轴范围
y_min = min(final_losses.values()) * 0.5
y_max = max(loss_hist[0] for loss_hist in
            [gradient_descent(x_normalized, y_normalized, lr, 1, False)[2] for lr in learning_rates]) * 2
plt.ylim(max(y_min, 1e-10), y_max)

# 添加最优学习率标注
best_lr = min(final_losses, key=final_losses.get)
plt.text(0.02, 0.02, f'最优学习率: {best_lr}\n最终损失: {final_losses[best_lr]:.8f}',
         transform=plt.gca().transAxes, fontsize=12,
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

plt.tight_layout()
plt.savefig('fig3_learning_rate_comparison.png', dpi=300, bbox_inches='tight')
print("\n已保存图3: fig3_learning_rate_comparison.png")
plt.show()

# 打印总结信息
print("\n" + "=" * 50)
print("训练完成！生成的文件如下：")
print("1. fig1_fitting_result.png - 一元线性回归拟合结果图")
print("2. fig2_loss_curve.png - Loss下降曲线图（包含整体和细节）")
print("3. fig3_learning_rate_comparison.png - 不同学习率对比图")
print(f"\n最佳学习率: {best_lr}")
print(f"对应最终损失: {final_losses[best_lr]:.8f}")
print(f"模型R²分数: {r2:.4f}")