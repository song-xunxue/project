"""
模块一：基于LSTM+XGBoost混合模型的出水水质预测

技术路线：
  1. LSTM提取进水时序数据的隐藏特征（捕捉长期依赖关系）
  2. 将LSTM隐藏层输出与原始特征拼接，作为XGBoost的输入
  3. XGBoost完成非线性回归（处理非时序维度的高维映射）
  4. 对比纯LSTM与混合模型的预测效果

预测目标：出水COD (mg/L)、出水NH4-N (mg/L)

李文煜 1120233042
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import torch
import torch.nn as nn
from xgboost import XGBRegressor

from config import (SEQ_LEN, LSTM_HIDDEN, LSTM_LAYERS, LSTM_EPOCHS, LSTM_LR, FIG_DIR)
from utils import log, save_fig


class LSTMModel(nn.Module):
    """LSTM时序预测网络"""
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super().__init__()
        # LSTM层：batch_first=True表示输入shape为(batch, seq, feature)
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.2)
        # 全连接层：将最后时间步的隐藏状态映射到输出
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out


def create_sequences(features, targets, seq_len):
    """将数据转化为时序窗口格式"""
    X, y = [], []
    for i in range(seq_len, len(features)):
        X.append(features[i - seq_len:i])
        y.append(targets[i])
    return np.array(X), np.array(y)


def run(df):
    """
    运行LSTM+XGBoost混合模型水质预测

    参数:
        df: 污水处理厂数据DataFrame
    返回:
        metrics: 包含各模型各指标评估结果的字典
    """
    log("=" * 70)
    log("模块一：LSTM+XGBoost混合模型出水水质预测")
    log("=" * 70)

    feature_cols = ['cod_in', 'bod_in', 'nh4_in', 'tn_in', 'tp_in',
                    'flow', 'temp', 'mlss', 'do', 'srt', 'hrt']
    target_cols = ['cod_out', 'nh4_out']

    # 创建时序窗口
    X_all, y_all = create_sequences(
        df[feature_cols].values, df[target_cols].values, SEQ_LEN)

    # 时间序列划分（前80%训练，后20%测试）
    split = int(len(X_all) * 0.8)
    X_train, X_test = X_all[:split], X_all[split:]
    y_train, y_test = y_all[:split], y_all[split:]

    # 标准化
    n_samples, n_timesteps, n_features = X_train.shape
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()

    X_train_scaled = scaler_X.fit_transform(
        X_train.reshape(-1, n_features)).reshape(n_samples, n_timesteps, n_features)
    X_test_scaled = scaler_X.transform(
        X_test.reshape(-1, n_features)).reshape(-1, n_timesteps, n_features)
    y_train_scaled = scaler_y.fit_transform(y_train)
    y_test_scaled = scaler_y.transform(y_test)

    # 构建LSTM
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    log(f"设备: {device}")

    model = LSTMModel(n_features, LSTM_HIDDEN, LSTM_LAYERS, len(target_cols)).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LSTM_LR)

    X_train_t = torch.FloatTensor(X_train_scaled).to(device)
    y_train_t = torch.FloatTensor(y_train_scaled).to(device)
    X_test_t = torch.FloatTensor(X_test_scaled).to(device)

    # 训练LSTM
    model.train()
    for epoch in range(LSTM_EPOCHS):
        optimizer.zero_grad()
        output = model(X_train_t)
        loss = criterion(output, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 20 == 0:
            log(f"  LSTM Epoch {epoch+1}/{LSTM_EPOCHS}, Loss: {loss.item():.6f}")

    # LSTM预测
    model.eval()
    with torch.no_grad():
        lstm_pred_scaled = model(X_test_t).cpu().numpy()
    lstm_pred = scaler_y.inverse_transform(lstm_pred_scaled)

    # 混合模型：LSTM隐特征 + 原始特征 → XGBoost
    with torch.no_grad():
        hidden_train = model.lstm(X_train_t)[0][:, -1, :].cpu().numpy()
        hidden_test = model.lstm(X_test_t)[0][:, -1, :].cpu().numpy()

    X_hybrid_train = np.concatenate([X_train[:, -1, :], hidden_train], axis=1)
    X_hybrid_test = np.concatenate([X_test[:, -1, :], hidden_test], axis=1)

    hybrid_preds = np.zeros_like(y_test)
    for j, tname in enumerate(target_cols):
        xgb = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1,
                           random_state=42, verbosity=0)
        xgb.fit(X_hybrid_train, y_train[:, j])
        hybrid_preds[:, j] = xgb.predict(X_hybrid_test)

    # 评估
    log(f"\n{'指标':<12} {'LSTM-COD':>10} {'LSTM-NH4':>10} {'混合-COD':>10} {'混合-NH4':>10}")
    log("-" * 55)

    metrics = {}
    for metric_name, metric_fn in [('R-squared', r2_score),
                                    ('RMSE', lambda y, p: np.sqrt(mean_squared_error(y, p))),
                                    ('MAE', mean_absolute_error)]:
        vals = []
        for j in range(2):
            vals.append(metric_fn(y_test[:, j], lstm_pred[:, j]))
            vals.append(metric_fn(y_test[:, j], hybrid_preds[:, j]))
        log(f"{metric_name:<12} {vals[0]:>10.4f} {vals[1]:>10.4f} {vals[2]:>10.4f} {vals[3]:>10.4f}")
        for j, tname in enumerate(target_cols):
            metrics[f'{metric_name}_lstm_{tname}'] = vals[j * 2]
            metrics[f'{metric_name}_hybrid_{tname}'] = vals[j * 2 + 1]

    # 可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    show = 500
    x_axis = np.arange(show)

    # COD和NH4-N预测对比
    for j, (tname, unit) in enumerate([('COD', 'mg/L'), ('NH4-N', 'mg/L')]):
        axes[0, j].plot(x_axis, y_test[:show, j], 'k-', alpha=0.5, linewidth=0.8, label='真实值')
        axes[0, j].plot(x_axis, lstm_pred[:show, j], 'b-', alpha=0.7, linewidth=0.8, label='LSTM')
        axes[0, j].plot(x_axis, hybrid_preds[:show, j], 'r-', alpha=0.7, linewidth=0.8, label='LSTM+XGBoost')
        axes[0, j].set_title(f'{tname}预测对比', fontsize=14)
        axes[0, j].set_xlabel('时间步')
        axes[0, j].set_ylabel(f'{tname} ({unit})')
        axes[0, j].legend()
        axes[0, j].grid(True, alpha=0.3)

    # 散点图
    for j, (tname, color) in enumerate([('cod_out', 'steelblue'), ('nh4_out', 'coral')]):
        axes[1, j].scatter(y_test[:, j], hybrid_preds[:, j], alpha=0.3, s=5, c=color)
        lim = [min(y_test[:, j].min(), hybrid_preds[:, j].min()),
               max(y_test[:, j].max(), hybrid_preds[:, j].max())]
        axes[1, j].plot(lim, lim, 'r--', linewidth=1)
        r2_key = f'R-squared_hybrid_{tname}'
        axes[1, j].set_title(f'混合模型 {tname}散点 (R-squared={metrics[r2_key]:.4f})', fontsize=12)
        axes[1, j].set_xlabel('真实值 (mg/L)')
        axes[1, j].set_ylabel('预测值 (mg/L)')
        axes[1, j].grid(True, alpha=0.3)

    plt.tight_layout()
    save_fig(fig, 'module1_water_quality', FIG_DIR)
    return metrics
