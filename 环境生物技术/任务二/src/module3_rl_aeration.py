"""
模块三：基于DQN强化学习的曝气控制优化

技术路线：
  1. 构建简化的污水处理曝气控制环境
     - 状态: [进水COD, 进水NH4-N, 流量, 温度, 当前DO]（归一化）
     - 动作: [降低DO 0.3, 维持, 提高DO 0.3]
     - 奖励: -(出水超标惩罚 + 能耗惩罚)
  2. DQN（Deep Q-Network）智能体学习最优曝气策略
  3. 对比DQN策略 vs 固定DO(PID)策略的能耗和出水达标率

目标：在保证出水NH4-N达标(<5 mg/L)的前提下，最小化曝气能耗

李文煜 1120233042
"""

import numpy as np
import random
from collections import deque
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

from config import (DQN_EPISODES, DQN_GAMMA, DQN_EPSILON_START,
                     DQN_EPSILON_MIN, DQN_EPSILON_DECAY, DQN_BATCH_SIZE,
                     DQN_MEMORY_SIZE, DQN_SAMPLE_RATE, FIG_DIR)
from utils import log, save_fig


class SimpleWWTPEnv:
    """
    简化的污水处理曝气控制环境

    模拟活性污泥法中曝气环节的DO控制：
    - DO越高 → 硝化越充分（出水NH4-N越低）但能耗越高
    - DO越低 → 节能但出水NH4-N可能超标
    """
    def __init__(self, data):
        self.data = data.reset_index(drop=True)
        self.idx = 0
        self.done = False

    def reset(self):
        self.idx = 100
        self.done = False
        return self._get_state()

    def _get_state(self):
        row = self.data.iloc[self.idx]
        return np.array([row['cod_in'] / 700, row['nh4_in'] / 55,
                         row['flow'] / 40000, row['temp'] / 32,
                         row['do'] / 4.0])

    def step(self, action):
        """
        执行动作并返回下一状态、奖励、是否结束、附加信息

        参数:
            action: 0=降低DO 0.3, 1=维持, 2=提高DO 0.3
        """
        row = self.data.iloc[self.idx]
        do_delta = [-0.3, 0, 0.3][action]
        new_do = np.clip(row['do'] + do_delta, 0.5, 4.0)

        # 出水NH4-N: DO越高硝化越充分
        nh4_out = row['nh4_in'] * (0.08 + 0.05 * np.exp(-new_do)
                                   + 0.02 * np.exp(-(row['temp'] - 15) / 10))
        # 能耗与DO正相关
        energy = 0.25 + 0.08 * new_do + 0.0002 * row['cod_in']

        # 奖励函数：出水达标 + 低能耗
        violation = max(0, nh4_out - 5.0) * 2.0   # 超标惩罚
        energy_penalty = energy * 0.5               # 能耗惩罚
        reward = -(violation + energy_penalty)

        self.idx += 1
        if self.idx >= len(self.data) - 1:
            self.done = True

        return self._get_state(), reward, self.done, {
            'nh4_out': nh4_out, 'energy': energy, 'do': new_do}


class DQN(nn.Module):
    """DQN网络：状态→各动作的Q值"""
    def __init__(self, state_dim, action_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU(),
            nn.Linear(64, action_dim))

    def forward(self, x):
        return self.net(x)


def run(df):
    """
    运行DQN强化学习曝气控制优化

    参数:
        df: 污水处理厂数据DataFrame
    返回:
        dict: 能耗节省百分比、超标率等
    """
    log("\n" + "=" * 70)
    log("模块三：DQN强化学习曝气控制优化")
    log("=" * 70)

    # 数据降采样加速训练
    df_rl = df.iloc[::DQN_SAMPLE_RATE].reset_index(drop=True)
    env = SimpleWWTPEnv(df_rl)
    state_dim = 5
    action_dim = 3

    policy_net = DQN(state_dim, action_dim)
    target_net = DQN(state_dim, action_dim)
    target_net.load_state_dict(policy_net.state_dict())
    optimizer = torch.optim.Adam(policy_net.parameters(), lr=0.001)

    memory = deque(maxlen=DQN_MEMORY_SIZE)
    epsilon = DQN_EPSILON_START
    episode_rewards = []

    # 训练
    for ep in range(DQN_EPISODES):
        state = env.reset()
        total_reward = 0

        while not env.done:
            if random.random() < epsilon:
                action = random.randint(0, 2)
            else:
                with torch.no_grad():
                    q_vals = policy_net(torch.FloatTensor(state).unsqueeze(0))
                    action = q_vals.argmax().item()

            next_state, reward, done, info = env.step(action)
            memory.append((state, action, reward, next_state, done))
            total_reward += reward
            state = next_state

            # 经验回放
            if len(memory) >= DQN_BATCH_SIZE:
                batch = random.sample(memory, DQN_BATCH_SIZE)
                s, a, r, s2, d = zip(*batch)
                s = torch.FloatTensor(np.array(s))
                a = torch.LongTensor(a)
                r = torch.FloatTensor(r)
                s2 = torch.FloatTensor(np.array(s2))
                d = torch.FloatTensor(d)

                q = policy_net(s).gather(1, a.unsqueeze(1)).squeeze()
                with torch.no_grad():
                    q_next = target_net(s2).max(1)[0]
                    q_target = r + DQN_GAMMA * q_next * (1 - d)

                loss = nn.MSELoss()(q, q_target)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        epsilon = max(DQN_EPSILON_MIN, epsilon * DQN_EPSILON_DECAY)
        episode_rewards.append(total_reward)

        if (ep + 1) % 10 == 0:
            target_net.load_state_dict(policy_net.state_dict())
            log(f"  Episode {ep+1}/{DQN_EPISODES}, Reward: {total_reward:.2f}, "
                f"Epsilon: {epsilon:.3f}")

    # 测试对比
    log("\n测试阶段对比:")
    test_data = df_rl.iloc[int(len(df_rl) * 0.8):].reset_index(drop=True)

    # DQN策略
    test_env = SimpleWWTPEnv(test_data)
    state = test_env.reset()
    dqn_do, dqn_nh4, dqn_energy = [], [], []
    while not test_env.done:
        with torch.no_grad():
            action = policy_net(torch.FloatTensor(state).unsqueeze(0)).argmax().item()
        state, _, done, info = test_env.step(action)
        dqn_do.append(info['do'])
        dqn_nh4.append(info['nh4_out'])
        dqn_energy.append(info['energy'])

    # PID基准（固定DO=2.0）
    test_env2 = SimpleWWTPEnv(test_data)
    state = test_env2.reset()
    pid_do, pid_nh4, pid_energy = [], [], []
    while not test_env2.done:
        current_do = test_env2.data.iloc[test_env2.idx]['do']
        if current_do < 1.8:
            action = 2
        elif current_do > 2.2:
            action = 0
        else:
            action = 1
        state, _, done, info = test_env2.step(action)
        pid_do.append(info['do'])
        pid_nh4.append(info['nh4_out'])
        pid_energy.append(info['energy'])

    dqn_avg_energy = np.mean(dqn_energy)
    pid_avg_energy = np.mean(pid_energy)
    dqn_violation = np.mean(np.array(dqn_nh4) > 5.0) * 100
    pid_violation = np.mean(np.array(pid_nh4) > 5.0) * 100
    energy_saving = (pid_avg_energy - dqn_avg_energy) / pid_avg_energy * 100

    log(f"{'指标':<20} {'固定DO(PID)':>15} {'DQN策略':>15} {'改善':>10}")
    log("-" * 60)
    log(f"{'平均能耗(kWh/m3)':<20} {pid_avg_energy:>15.4f} {dqn_avg_energy:>15.4f} {energy_saving:>9.1f}%")
    log(f"{'出水超标率(%)':<20} {pid_violation:>15.1f} {dqn_violation:>15.1f} {pid_violation-dqn_violation:>9.1f}%")
    log(f"{'平均NH4-N(mg/L)':<20} {np.mean(pid_nh4):>15.4f} {np.mean(dqn_nh4):>15.4f}")
    log(f"{'平均DO(mg/L)':<20} {np.mean(pid_do):>15.4f} {np.mean(dqn_do):>15.4f}")

    # 可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    show = min(500, len(dqn_do))

    # 训练奖励曲线
    axes[0, 0].plot(episode_rewards, alpha=0.5, color='steelblue')
    window = 5
    smoothed = np.convolve(episode_rewards, np.ones(window) / window, mode='valid')
    axes[0, 0].plot(range(window - 1, len(episode_rewards)), smoothed, 'r-', linewidth=2)
    axes[0, 0].set_title('DQN训练奖励曲线', fontsize=14)
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('累计奖励')
    axes[0, 0].grid(True, alpha=0.3)

    # DO控制对比
    axes[0, 1].plot(np.arange(show), pid_do[:show], 'b-', alpha=0.6, label='固定DO(PID)')
    axes[0, 1].plot(np.arange(show), dqn_do[:show], 'r-', alpha=0.6, label='DQN策略')
    axes[0, 1].axhline(y=2.0, color='k', linestyle='--', alpha=0.3, label='DO目标')
    axes[0, 1].set_title('DO控制策略对比', fontsize=14)
    axes[0, 1].set_xlabel('时间步')
    axes[0, 1].set_ylabel('DO (mg/L)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 能耗对比
    axes[1, 0].plot(np.arange(show), pid_energy[:show], 'b-', alpha=0.6, label='固定DO(PID)')
    axes[1, 0].plot(np.arange(show), dqn_energy[:show], 'r-', alpha=0.6, label='DQN策略')
    axes[1, 0].set_title(f'能耗对比 (DQN节省{energy_saving:.1f}%)', fontsize=14)
    axes[1, 0].set_xlabel('时间步')
    axes[1, 0].set_ylabel('能耗 (kWh/m3)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # 出水NH4-N对比
    axes[1, 1].plot(np.arange(show), pid_nh4[:show], 'b-', alpha=0.6, label='固定DO(PID)')
    axes[1, 1].plot(np.arange(show), dqn_nh4[:show], 'r-', alpha=0.6, label='DQN策略')
    axes[1, 1].axhline(y=5.0, color='k', linestyle='--', alpha=0.3, label='排放标准')
    axes[1, 1].set_title('出水NH4-N对比', fontsize=14)
    axes[1, 1].set_xlabel('时间步')
    axes[1, 1].set_ylabel('NH4-N (mg/L)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    save_fig(fig, 'module3_rl_aeration', FIG_DIR)

    return {'energy_saving_pct': energy_saving, 'dqn_violation': dqn_violation}
