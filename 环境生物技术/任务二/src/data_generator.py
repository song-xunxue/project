"""
BSM1风格污水处理厂模拟数据生成器

基于IWA活性污泥模型（ASM1）的基准模拟模型（BSM1）特征，
生成包含进水水质、运行参数、出水水质和能耗的时序数据。

数据包含：
  输入特征: cod_in, bod_in, nh4_in, tn_in, tp_in, flow, temp, mlss, do, srt, hrt
  输出目标: cod_out, nh4_out, energy

数据特征:
  - 日变化：模拟昼夜用水量变化
  - 周变化：工作日与周末差异
  - 季节变化：温度和用水量的年周期
  - 冲击负荷：随机注入3%异常高负荷事件
  - 非线性关系：出水水质与DO、温度、SRT等参数的非线性耦合

李文煜 1120233042
"""

import numpy as np
import pandas as pd
from config import DATA_DAYS, DATA_INTERVAL, RANDOM_SEED
from utils import log


def generate_wwtp_data(n_days=DATA_DAYS, seed=RANDOM_SEED):
    """
    生成BSM1风格的污水处理厂模拟数据

    参数:
        n_days: 模拟天数
        seed: 随机种子

    返回:
        DataFrame，每行一个采样点（15分钟间隔）
    """
    np.random.seed(seed)
    n = n_days * DATA_INTERVAL

    t = np.arange(n)
    # 将采样索引转换为一天中的时刻（0-24h）
    hour = (t % DATA_INTERVAL) / DATA_INTERVAL * 24

    # 1. 进水水质
    # COD: 日变化 + 周变化 + 季节变化 + 随机噪声
    cod_in = (350 + 80 * np.sin(2 * np.pi * hour / 24)
              + 50 * np.sin(2 * np.pi * t / (DATA_INTERVAL * 7))
              + 100 * np.sin(2 * np.pi * t / (DATA_INTERVAL * 365))
              + np.random.normal(0, 30, n))
    cod_in = np.clip(cod_in, 150, 700)

    # BOD约为COD的0.45-0.55倍
    bod_in = cod_in * (0.5 + np.random.normal(0, 0.03, n))
    bod_in = np.clip(bod_in, 80, 350)

    # NH4-N: 氨氮浓度
    nh4_in = (25 + 8 * np.sin(2 * np.pi * hour / 24 + 0.5)
              + np.random.normal(0, 3, n))
    nh4_in = np.clip(nh4_in, 10, 55)

    # TN: 总氮约为NH4-N的2倍
    tn_in = nh4_in * (2.0 + np.random.normal(0, 0.1, n))
    tn_in = np.clip(tn_in, 20, 80)

    # TP: 总磷
    tp_in = (5 + 1.5 * np.sin(2 * np.pi * hour / 24 + 1)
             + np.random.normal(0, 0.5, n))
    tp_in = np.clip(tp_in, 2, 10)

    # 2. 水量：白天高夜间低
    flow = (22000 + 6000 * np.sin(2 * np.pi * (hour - 6) / 24)
            + 2000 * np.sin(2 * np.pi * t / (DATA_INTERVAL * 7))
            + np.random.normal(0, 1000, n))
    flow = np.clip(flow, 12000, 40000)

    # 3. 温度：季节变化
    temp = (18 + 8 * np.sin(2 * np.pi * t / (DATA_INTERVAL * 365) - np.pi / 2)
            + np.random.normal(0, 1, n))
    temp = np.clip(temp, 5, 32)

    # 4. 运行参数
    mlss = 3000 + 500 * np.sin(2 * np.pi * t / (DATA_INTERVAL * 30)) + np.random.normal(0, 200, n)
    mlss = np.clip(mlss, 1500, 5000)

    do_setpoint = 2.0 + 0.3 * np.sin(2 * np.pi * hour / 24)
    do_actual = do_setpoint + np.random.normal(0, 0.2, n)
    do_actual = np.clip(do_actual, 0.5, 4.0)

    srt = 12 + 2 * np.random.normal(0, 1, n)
    srt = np.clip(srt, 5, 25)

    hrt = 8 + flow / 10000 + np.random.normal(0, 0.5, n)
    hrt = np.clip(hrt, 4, 15)

    # 5. 输出变量（非线性耦合关系）
    # 出水COD: 去除率受DO、COD负荷、温度影响
    cod_removal = (0.88 + 0.04 * (do_actual / 3.0)
                   - 0.02 * (cod_in / 500)
                   + 0.01 * (temp / 20))
    cod_removal = np.clip(cod_removal, 0.75, 0.97) + np.random.normal(0, 0.01, n)
    cod_out = cod_in * (1 - cod_removal)
    cod_out = np.clip(cod_out, 15, 100)

    # 出水NH4-N: 受DO、温度影响大（硝化反应对DO敏感）
    nh4_out = (nh4_in * (0.08 + 0.05 * np.exp(-do_actual)
               + 0.02 * np.exp(-(temp - 15) / 10)
               + np.random.normal(0, 0.01, n)))
    nh4_out = np.clip(nh4_out, 0.5, 15)

    # 能耗: 曝气(与DO正相关) + 有机负荷 + 水量 + 温度 + MLSS
    energy = (0.35 + 0.12 * do_actual
              + 0.0005 * cod_in
              + 0.003 * (flow / 10000)
              - 0.008 * (temp - 15)
              + 0.002 * (mlss - 3000) / 1000
              + np.random.normal(0, 0.03, n))
    energy = np.clip(energy, 0.20, 0.80)

    # 6. 注入冲击负荷事件（约3%的采样点）
    shock_idx = np.random.choice(n, size=int(n * 0.03), replace=False)
    cod_in[shock_idx] *= np.random.uniform(1.5, 2.5, len(shock_idx))
    nh4_in[shock_idx] *= np.random.uniform(1.3, 2.0, len(shock_idx))
    flow[shock_idx] *= np.random.uniform(1.2, 1.8, len(shock_idx))

    df = pd.DataFrame({
        'cod_in': cod_in, 'bod_in': bod_in, 'nh4_in': nh4_in,
        'tn_in': tn_in, 'tp_in': tp_in, 'flow': flow, 'temp': temp,
        'mlss': mlss, 'do': do_actual, 'srt': srt, 'hrt': hrt,
        'cod_out': cod_out, 'nh4_out': nh4_out, 'energy': energy,
    })
    return df
