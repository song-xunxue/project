"""
模块二：多模型能耗预测对比（重点LightGBM）

对比5种机器学习模型的能耗预测效果：
  - LightGBM: 微软提出的快速梯度提升树
  - XGBoost: 经典梯度提升树
  - RandomForest: 随机森林
  - SVR: 支持向量回归
  - GBDT: 梯度提升决策树

预测目标：污水处理厂单位能耗 (kWh/m3)

李文煜 1120233042
"""

import numpy as np
import time
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
import lightgbm as lgb
from xgboost import XGBRegressor

from config import N_ESTIMATORS, MAX_DEPTH_TREE, FIG_DIR
from utils import log, save_fig


def run(df):
    """
    运行多模型能耗预测对比

    参数:
        df: 污水处理厂数据DataFrame
    返回:
        all_metrics: 各模型评估指标字典
    """
    log("\n" + "=" * 70)
    log("模块二：多模型能耗预测对比（重点LightGBM）")
    log("=" * 70)

    feature_cols = ['cod_in', 'bod_in', 'nh4_in', 'tn_in', 'tp_in',
                    'flow', 'temp', 'mlss', 'do', 'srt', 'hrt']
    X = df[feature_cols].values
    y = df['energy'].values

    # 时间序列划分（不shuffle，保持时序性）
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False)

    # SVR需要标准化，树模型不需要
    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # 候选模型
    models = {
        'LightGBM': lgb.LGBMRegressor(n_estimators=N_ESTIMATORS, max_depth=MAX_DEPTH_TREE,
                                       learning_rate=0.05, random_state=42, verbose=-1),
        'XGBoost': XGBRegressor(n_estimators=N_ESTIMATORS, max_depth=MAX_DEPTH_TREE,
                                learning_rate=0.05, random_state=42, verbosity=0),
        'RandomForest': RandomForestRegressor(n_estimators=N_ESTIMATORS, max_depth=10,
                                               random_state=42),
        'SVR': SVR(kernel='rbf', C=10, gamma='scale'),
        'GBDT': GradientBoostingRegressor(n_estimators=N_ESTIMATORS, max_depth=5,
                                           learning_rate=0.05, random_state=42),
    }

    log(f"\n{'模型':<15} {'R-squared':>10} {'RMSE':>10} {'MAE':>10} {'训练时间(ms)':>12}")
    log("-" * 60)

    all_metrics = {}
    all_preds = {}

    for name, model in models.items():
        start = time.time()
        if name == 'SVR':
            model.fit(X_train_s, y_train)
            pred = model.predict(X_test_s)
        else:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
        train_time = (time.time() - start) * 1000

        r2 = r2_score(y_test, pred)
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        mae = mean_absolute_error(y_test, pred)

        all_metrics[name] = {'R-squared': r2, 'RMSE': rmse, 'MAE': mae, 'Time_ms': train_time}
        all_preds[name] = pred
        log(f"{name:<15} {r2:>10.4f} {rmse:>10.4f} {mae:>10.4f} {train_time:>12.1f}")

    best_name = max(all_metrics, key=lambda k: all_metrics[k]['R-squared'])
    log(f"\n最优模型: {best_name} (R-squared={all_metrics[best_name]['R-squared']:.4f})")

    # 可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    show = 300
    x_axis = np.arange(show)

    # 预测曲线对比
    axes[0, 0].plot(x_axis, y_test[:show], 'k-', alpha=0.5, linewidth=0.8, label='真实值')
    for name in ['LightGBM', 'XGBoost', 'SVR']:
        axes[0, 0].plot(x_axis, all_preds[name][:show], alpha=0.7, linewidth=0.8, label=name)
    axes[0, 0].set_title('能耗预测对比（部分测试集）', fontsize=14)
    axes[0, 0].set_xlabel('时间步')
    axes[0, 0].set_ylabel('能耗 (kWh/m3)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # R-squared柱状图
    names = list(all_metrics.keys())
    r2_vals = [all_metrics[n]['R-squared'] for n in names]
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0', '#F44336']
    bars = axes[0, 1].bar(names, r2_vals, color=colors, alpha=0.8, edgecolor='white')
    axes[0, 1].set_title('各模型 R-squared 对比', fontsize=14)
    axes[0, 1].set_ylabel('R-squared')
    axes[0, 1].set_ylim(min(r2_vals) - 0.05, 1.0)
    for bar, val in zip(bars, r2_vals):
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                        f'{val:.4f}', ha='center', fontsize=10)
    axes[0, 1].grid(True, alpha=0.3, axis='y')

    # LightGBM散点图
    axes[1, 0].scatter(y_test, all_preds['LightGBM'], alpha=0.3, s=5, c='#2196F3')
    lim = [y_test.min(), y_test.max()]
    axes[1, 0].plot(lim, lim, 'r--', linewidth=1)
    axes[1, 0].set_title(
        f'LightGBM散点 (R-squared={all_metrics["LightGBM"]["R-squared"]:.4f})', fontsize=12)
    axes[1, 0].set_xlabel('真实值 (kWh/m3)')
    axes[1, 0].set_ylabel('预测值 (kWh/m3)')
    axes[1, 0].grid(True, alpha=0.3)

    # 特征重要性
    importances = models['LightGBM'].feature_importances_
    sorted_idx = np.argsort(importances)
    axes[1, 1].barh([feature_cols[i] for i in sorted_idx], importances[sorted_idx],
                     color='#2196F3', alpha=0.8)
    axes[1, 1].set_title('LightGBM特征重要性', fontsize=14)
    axes[1, 1].set_xlabel('重要性得分')
    axes[1, 1].grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    save_fig(fig, 'module2_energy_prediction', FIG_DIR)
    return all_metrics
