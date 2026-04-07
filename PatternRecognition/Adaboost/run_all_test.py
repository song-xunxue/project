"""
AdaBoost 实验聚合测试脚本

依次执行二分类和多分类两种 AdaBoost 实验，
将所有输出同时写入控制台和 experiment_results.log 日志文件。

日志格式：
    - 时间戳标记实验开始时间
    - 每个模型逐样本预测结果（✅/❌ 标注）
    - 各模型最终准确率统计

运行方式：
    python run_all_test.py
    （需先运行 plot.py 下载数据集）

作者: 李文煜
日期: 2026-04-07

2026-04-07
变更说明：
  1. 补充模块文档字符串和详细中文注释
"""

import sys
import datetime

# 导入两个测试脚本的过程函数
from test_model_binary import data_process_binary, test_model_binary_process
from test_model_multi import data_process_multi, test_model_multi_process


class Logger(object):
    """
    双向输出 Logger

    拦截 sys.stdout 的 write 调用，使 print 语句的内容
    同时输出到控制台屏幕和日志文件，实现实验结果的自动记录。

    用法：
        sys.stdout = Logger("experiment_results.log")
        # 此后所有 print 输出都会同时写入屏幕和文件

    参数:
        filename (str): 日志文件路径，默认 "experiment_results.log"
    """

    def __init__(self, filename="experiment_results.log"):
        self.terminal = sys.stdout                    # 保留原始标准输出（屏幕）
        self.log = open(filename, "a", encoding="utf-8")  # 以追加模式打开日志文件

    def write(self, message):
        """同时向屏幕和文件写入内容"""
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # 确保实时写入磁盘，避免程序异常退出时丢失数据

    def flush(self):
        """刷新缓冲区（接口兼容）"""
        pass


if __name__ == "__main__":
    # 1. 启动日志记录拦截：此后所有 print 输出同时写入屏幕和文件
    sys.stdout = Logger("experiment_results.log")

    # 打印实验开始时间戳
    print("\n" + "=" * 60)
    print(f"=== AdaBoost 实验测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("=" * 60)

    csv_path = "./data/wine_quality_full.csv"

    # 2. 依次执行两版对比实验

    # 基础二分类：quality >= 6 → 好酒(+1)，< 6 → 差酒(-1)
    X_train_bin, X_test_bin, y_train_bin, y_test_bin = data_process_binary(csv_path)
    test_model_binary_process(X_train_bin, X_test_bin, y_train_bin, y_test_bin)

    print("\n" + "-" * 60 + "\n")

    # 进阶多分类：保留原始品质评分（3~9）
    X_train_mul, X_test_mul, y_train_mul, y_test_mul = data_process_multi(csv_path)
    test_model_multi_process(X_train_mul, X_test_mul, y_train_mul, y_test_mul)

    print("\n")
    print("=== 所有对比实验执行完毕，结果已安全保存至 experiment_results.log ===")
