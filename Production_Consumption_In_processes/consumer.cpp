#include "Common.h"

int main()
{
    IPCManager ipc;
    if (!ipc.openResources()) {
        return 1;
    }

    SharedData* sharedData = ipc.getSharedData();

    // 使用控制台锁保护初始输出
    WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
    cout << "[消费者 | PID: " << GetCurrentProcessId() << "] 启动成功，等待消费信号..." << endl;
    ReleaseMutex(ipc.getConsoleMutex());

    while (true) {
        // 等待消费信号
        WaitForSingleObject(ipc.getConsumeSemaphore(), INFINITE);
        // 检查是否生产阶段已结束
        WaitForSingleObject(ipc.getDataMutex(), INFINITE);
        bool production_finished = (sharedData->production_finished == 1);
        if (production_finished) {
            ReleaseMutex(ipc.getDataMutex());
            break;
        }
        // 消费任务
        Task currentTask = sharedData->buffer[sharedData->read_pos];
        sharedData->read_pos = (sharedData->read_pos + 1) % BUFFER_SIZE;
        sharedData->count--;

        ReleaseMutex(ipc.getDataMutex());
        // 执行任务
        WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
        currentTask.execute();
        cout << ", 缓冲区: " << (sharedData->count + 1) << "→" << sharedData->count << "/" << BUFFER_SIZE << endl;
        ReleaseMutex(ipc.getConsoleMutex());
        // 如果缓冲区为空，切换到生产阶段
        WaitForSingleObject(ipc.getDataMutex(), INFINITE);
        if (sharedData->count == 0) {
            WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
            cout<<"===== 缓冲区已空! 切换到生产阶段 =====" << endl;
            ReleaseMutex(ipc.getConsoleMutex());
            // 切换到生产阶段
            ReleaseSemaphore(ipc.getProduceSemaphore(), 1, NULL);
        }
        else {
            // 继续消费
            ReleaseSemaphore(ipc.getConsumeSemaphore(), 1, NULL);
        }
        ReleaseMutex(ipc.getDataMutex());
    }

    WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
    cout << "[消费者 | PID: " << GetCurrentProcessId() << "] 已完成工作" << endl;
    ReleaseMutex(ipc.getConsoleMutex());

    return 0;
}