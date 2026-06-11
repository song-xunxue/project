"""
基于机器学习的污水处理智能优化 — 主入口

运行方式：
    方式一（推荐）: 在任务二根目录执行  python -m src.main
    方式二: 直接运行本文件（已自动处理路径）

李文煜 1120233042
"""

from config import FIG_DIR, RESULT_FILE
from utils import log, save_results
from data_generator import generate_wwtp_data
import module1_water_quality, module2_energy, module3_rl_aeration, module4_fault_detection


def main():
    log("=" * 70)
    log(" 基于机器学习的污水处理智能优化 - 算法实验")
    log(" 李文煜 1120233042")
    log("=" * 70)

    # 数据准备
    log("\n[数据准备] 生成BSM1风格模拟数据...")
    df = generate_wwtp_data()
    log(f"数据规模: {df.shape[0]} 条记录 ({df.shape[0] // 96} 天)")
    log(f"特征统计:\n{df.describe().round(2)}")

    # 运行四大模块
    m1 = module1_water_quality.run(df)
    m2 = module2_energy.run(df)
    m3 = module3_rl_aeration.run(df)
    module4_fault_detection.run(df)

    # 保存
    log("\n" + "=" * 70)
    log("实验完成！所有结果图保存至 figures/ 目录")
    log("=" * 70)
    save_results(RESULT_FILE)


if __name__ == '__main__':
    main()
