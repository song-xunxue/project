"""
模块四：基于孤立森林和LOF的故障检测

检测三类故障：
  1. 进水冲击负荷（COD和流量同时异常高）
  2. DO传感器漂移（DO异常低）
  3. 出水超标事件（NH4-N和COD同时超标）

对比三种无监督异常检测方法：
  - IsolationForest: 基于随机分割的孤立检测
  - LOF: 基于局部密度的离群因子
  - OneClassSVM: 单类支持向量机

李文煜 1120233042
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.metrics import classification_report

from config import FAULT_CONTAMINATION, FIG_DIR
from utils import log, save_fig


def run(df):
    """
    运行多方法故障检测

    参数:
        df: 污水处理厂数据DataFrame
    """
    log("\n" + "=" * 70)
    log("模块四：基于孤立森林和LOF的故障检测")
    log("=" * 70)

    feature_cols = ['cod_in', 'nh4_in', 'flow', 'do', 'cod_out', 'nh4_out']
    X = df[feature_cols].values

    # 故障标注
    y_true = np.zeros(len(df), dtype=int)

    # 故障类型1：进水冲击（COD>600 且 流量>30000）
    shock_mask = (df['cod_in'] > 600) & (df['flow'] > 30000)
    y_true[shock_mask] = 1

    # 故障类型2：DO传感器漂移（DO<0.8）
    drift_mask = df['do'] < 0.8
    y_true[drift_mask] = 1

    # 故障类型3：出水超标（NH4-N>5 且 COD>60）
    exceed_mask = (df['nh4_out'] > 5) & (df['cod_out'] > 60)
    y_true[exceed_mask] = 1

    fault_rate = y_true.sum() / len(y_true) * 100
    log(f"数据中故障比例: {fault_rate:.2f}% ({y_true.sum()}/{len(y_true)})")

    # 标准化
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # 模型
    models = {
        'IsolationForest': IsolationForest(contamination=FAULT_CONTAMINATION, random_state=42),
        'LOF': LocalOutlierFactor(contamination=FAULT_CONTAMINATION, novelty=True),
        'OneClassSVM': OneClassSVM(gamma='scale', nu=FAULT_CONTAMINATION),
    }

    log(f"\n{'方法':<20} {'精确率':>8} {'召回率':>8} {'F1分数':>8} {'检测率':>8}")
    log("-" * 55)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for i, (name, model) in enumerate(models.items()):
        model.fit(X_scaled)
        pred = model.predict(X_scaled)
        pred_binary = (pred == -1).astype(int)

        report = classification_report(y_true, pred_binary, output_dict=True, zero_division=0)
        precision = report['1']['precision'] if '1' in report else 0
        recall = report['1']['recall'] if '1' in report else 0
        f1 = report['1']['f1-score'] if '1' in report else 0

        log(f"{name:<20} {precision:>8.4f} {recall:>8.4f} {f1:>8.4f} {recall*100:>7.1f}%")

        # 可视化
        ax = axes[i]
        normal_mask = pred_binary == 0
        fault_mask = pred_binary == 1
        true_fault = y_true == 1

        ax.scatter(X_scaled[normal_mask, 3], X_scaled[normal_mask, 0],
                   c='steelblue', alpha=0.2, s=3, label='正常')
        ax.scatter(X_scaled[fault_mask, 3], X_scaled[fault_mask, 0],
                   c='red', alpha=0.5, s=5, label='检测异常')
        ax.scatter(X_scaled[true_fault, 3], X_scaled[true_fault, 0],
                   facecolors='none', edgecolors='green', s=10, linewidths=0.5, label='真实故障')
        ax.set_title(f'{name}\n(F1={f1:.3f})', fontsize=12)
        ax.set_xlabel('DO (标准化)')
        ax.set_ylabel('COD_in (标准化)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    save_fig(fig, 'module4_fault_detection', FIG_DIR)
