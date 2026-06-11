"""
全局配置参数

李文煜 1120233042
"""

import os
import matplotlib
import matplotlib.pyplot as plt

# 项目根目录（本文件所在目录的父目录）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(PROJECT_DIR, 'figures')
RESULT_FILE = os.path.join(PROJECT_DIR, 'results.txt')

# 确保输出目录存在
os.makedirs(FIG_DIR, exist_ok=True)

# matplotlib 中文字体配置
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据参数
DATA_DAYS = 365           # 模拟天数
DATA_INTERVAL = 96        # 每天采样点数（15分钟间隔）
RANDOM_SEED = 42

# LSTM参数
LSTM_HIDDEN = 64
LSTM_LAYERS = 2
LSTM_EPOCHS = 100
LSTM_LR = 0.001
SEQ_LEN = 6               # 时序窗口长度

# 模型对比参数
N_ESTIMATORS = 200
MAX_DEPTH_TREE = 6

# DQN参数
DQN_EPISODES = 30
DQN_GAMMA = 0.95
DQN_EPSILON_START = 1.0
DQN_EPSILON_MIN = 0.05
DQN_EPSILON_DECAY = 0.995
DQN_BATCH_SIZE = 64
DQN_MEMORY_SIZE = 5000
DQN_SAMPLE_RATE = 10       # RL数据采样率（每N个取1个，加速训练）

# 故障检测参数
FAULT_CONTAMINATION = 0.05  # 异常比例估计
