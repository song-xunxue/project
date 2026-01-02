import time
import torch
import model10 as model

# 全局路径配置
train_dir = 'cowface-verification-U/train/train'
test_dir = 'cowface-verification-U/test-new/test-new'
test_csv = 'cowface-verification-U/test-1118.csv'  # 测试集定义文件

if __name__ == '__main__':
    start_time = time.time()  # 记录开始时间

    print("========== 阶段 1: 模型训练 ==========")
    # -------------------------------------------------------------
    # 1. 启动训练
    # -------------------------------------------------------------
    # main_train 会返回两个值：训练好的模型对象(未使用) 和 最佳阈值(best_threshold)
    # 这里的 train_epochs=30 是推荐值，显存充足且时间够可以设为 50
    _, best_threshold = model.main_train(
        train_epochs=30,
        train_dir=train_dir
    )

    print(f"\n========== 阶段 2: 自动推理 (阈值: {best_threshold:.4f}) ==========")
    # -------------------------------------------------------------
    # 2. 启动预测 (使用训练得到的最佳阈值)
    # -------------------------------------------------------------
    # model_path=None 表示让程序自动去 'model_train' 文件夹下找刚刚保存的最新的模型文件
    # threshold=best_threshold 表示使用刚才训练出的最佳参数，不再瞎猜 0.8
    # 释放训练占用的显存
    torch.cuda.empty_cache()
    import gc

    gc.collect()
    model.main_predict(
        model_path=None,
        test_csv_path=test_csv,
        test_dir_path=test_dir,
        output_name='submission',
        threshold=best_threshold
    )

    # -------------------------------------------------------------
    # 备选：如果你只想单独跑预测 (不需要训练)，请注释掉上面的1和2，取消下面的注释
    # -------------------------------------------------------------
    # model.main_predict(
    #     model_path='model_train/best_model_01.pth',  # 手动指定要跑哪个模型文件
    #     test_csv_path=test_csv,
    #     test_dir_path=test_dir,
    #     output_name='submission_manual',
    #     threshold=0.3000  # 这里必须手动填入你之前记录下的最佳阈值
    # )

    # 计算并显示耗时
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    hours = int(elapsed_seconds // 3600)
    minutes = int((elapsed_seconds % 3600) // 60)
    print("="*30)
    print(f"\n全流程总耗时: {hours:02d}小时 {minutes:02d}分钟")