import time
import model10 as model  # 引用你的稳定版 ArcFace 代码

# 全局路径配置
train_dir = 'cowface-verification-U/train/train'
test_dir = 'cowface-verification-U/test-new/test-new'
test_csv = 'cowface-verification-U/test-1118.csv'  # 测试集定义文件

if __name__ == '__main__':
    start_time = time.time()

    print("========== 阶段 1: 终极微调 (Last Mile) ==========")

    # 指向你刚刚跑出 0.9859 的那个模型
    # 注意：model10 的 train 函数会保存最好的模型覆盖 best_model_01.pth
    # 所以直接加载它就是加载最新的
    previous_model = 'model_train/best_model_01.pth'

    print(f"加载 0.98+ 模型: {previous_model} ...")

    # 再跑 50 轮！
    # 这次目的是让 Loss 降到 2.0 以下，Train Acc 冲向 80%
    model.main_train(
        model_path=previous_model,
        train_epochs=50,
        train_dir=train_dir
    )

    print("\n========== 阶段 2: 极限推理 ==========")

    # 0.98+ 的模型非常自信，阈值可以进一步提高
    # 尝试 0.40, 0.45, 0.50
    thresholds = [0.40, 0.45, 0.50]

    for th in thresholds:
        print(f"正在生成预测结果 (Threshold={th})...")
        model.main_predict(
            model_path=None,  # 自动找最新的 best_model
            test_csv_path=test_csv,
            test_dir_path=test_dir,
            output_name=f'submission_final_{int(th * 100)}',
            threshold=th
        )

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    hours = int(elapsed_seconds // 3600)
    minutes = int((elapsed_seconds % 3600) // 60)
    print("=" * 30)
    print(f"\n终极训练耗时: {hours:02d}小时 {minutes:02d}分钟")