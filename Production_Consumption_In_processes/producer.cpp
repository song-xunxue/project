#include "Common.h"

int main(int argc, char* argv[])
{
    IPCManager ipc;
    if (!ipc.openResources()) return 1;

    SharedData* sharedData = ipc.getSharedData();

    // 使用控制台锁保护初始输出
    WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
    cout << "[生产者 | PID: " << GetCurrentProcessId() << "] 启动成功，等待生产信号..." << endl;
    ReleaseMutex(ipc.getConsoleMutex());

    while (true) {
        // 等待生产信号
        WaitForSingleObject(ipc.getProduceSemaphore(), INFINITE);

        // 检查是否已经完成8次满缓冲区循环
        WaitForSingleObject(ipc.getDataMutex(), INFINITE);
        if (sharedData->full_cycles >= TARGET_FULL_CYCLES) {
            // 标记生产阶段结束
            sharedData->production_finished = 1;
            ReleaseMutex(ipc.getDataMutex());

            // 通知所有消费者退出
            for (int i = 0; i < NUM_CONSUMERS; i++) {
                ReleaseSemaphore(ipc.getConsumeSemaphore(), 1, NULL);
            }

            // 通知其他生产者退出
            for (int i = 0; i < NUM_PRODUCERS - 1; i++) {
                ReleaseSemaphore(ipc.getProduceSemaphore(), 1, NULL);
            }
            break;
        }

        // 生产任务
        long current_id = InterlockedIncrement(&sharedData->task_id_counter);
        string taskData = "产品编号 " + std::to_string(current_id);
        sharedData->buffer[sharedData->write_pos] = Task(current_id, taskData);
        sharedData->write_pos = (sharedData->write_pos + 1) % BUFFER_SIZE;
        sharedData->count++;

        WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
        cout << "[生产者 | PID: " << GetCurrentProcessId() << "] 生产任务: ID=" << current_id
            << ", 缓冲区: " << sharedData->count << "/" << BUFFER_SIZE << endl;
        ReleaseMutex(ipc.getConsoleMutex());

        // 如果缓冲区已满，切换到消费阶段
        if (sharedData->count >= BUFFER_SIZE) {
            WaitForSingleObject(ipc.getCycleMutex(), INFINITE);

            if (sharedData->full_cycles < TARGET_FULL_CYCLES) {
                InterlockedIncrement(&sharedData->full_cycles);

                WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
                cout << " =====缓冲区已满! 切换到消费阶段 ("
                    << sharedData->full_cycles << "/" << TARGET_FULL_CYCLES << ")=====" << endl;
                ReleaseMutex(ipc.getConsoleMutex());

                // 切换到消费阶段
                ReleaseSemaphore(ipc.getConsumeSemaphore(), 1, NULL);
            }
            ReleaseMutex(ipc.getCycleMutex());
        }
        else {
            // 继续生产
            ReleaseSemaphore(ipc.getProduceSemaphore(), 1, NULL);
        }

        ReleaseMutex(ipc.getDataMutex());
    }

    WaitForSingleObject(ipc.getConsoleMutex(), INFINITE);
    cout << "[生产者 | PID: " << GetCurrentProcessId() << "] 已完成工作" << endl;
    ReleaseMutex(ipc.getConsoleMutex());

    return 0;
}