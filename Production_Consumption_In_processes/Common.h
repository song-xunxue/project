#pragma once

#include <windows.h>
#include <iostream>
#include <string>
#include <vector>

#include <chrono>
#include <random>

using std::cout;
using std::cerr;
using std::endl;
using std::string;
using std::wstring;
using std::vector;

const int SENTINEL_TASK_ID = -1;
const int TARGET_FULL_CYCLES = 8;  // 目标完成8次满缓冲区循环

// 生产消费者数量
const int NUM_PRODUCERS = 4;
const int NUM_CONSUMERS = 4;

// 缓冲区大小
const int BUFFER_SIZE = 6;

// 任务类，封装了任务的数据和执行逻辑
class Task
{
public:
    int id;
    char data[128];

    Task(int taskId = -1, const string& taskData = "") : id(taskId) {
        strncpy_s(data, sizeof(data), taskData.c_str(), _TRUNCATE);
        processSleepWindows(0, 50);
    }

    void execute() const {
        // 模拟任务处理过程
        cout << "  [消费者 | PID: " << GetCurrentProcessId() << "] 正在执行任务: ID=" << this->id
            << ", Data='" << this->data << "'";
        processSleepWindows(50, 100); // 模拟耗时
    }

    void processSleepWindows(int min_ms = 0, int max_ms = 2000) const
    {
        static std::random_device rd;
        static std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(min_ms, max_ms);

        int sleep_time_ms = dis(gen);
        Sleep(sleep_time_ms);
    }
};

// 定义在共享内存中的数据结构
struct SharedData {
    Task buffer[BUFFER_SIZE];
    int read_pos;
    int write_pos;
    int count;                    // 当前缓冲区中的任务数量
    volatile long task_id_counter;      // 全局唯一的任务ID计数器
    volatile long full_cycles;          // 完成的满缓冲区循环次数
    volatile long production_finished;  // 生产阶段是否结束
};

// 负责管理进程间通信所需的所有共享资源
class IPCManager
{
public:
    IPCManager();
    ~IPCManager();

    bool createResources();
    bool openResources();

    // 资源访问接口
    SharedData* getSharedData() const { return pSharedData; }
    HANDLE getDataMutex() const { return hDataMutex; }
    HANDLE getConsoleMutex() const { return hConsoleMutex; }
    HANDLE getProduceSemaphore() const { return hProduceSemaphore; }
    HANDLE getConsumeSemaphore() const { return hConsumeSemaphore; }
    HANDLE getCycleMutex() const { return hCycleMutex; }
    //bool Empty()const { return pSharedData->count != BUFFER_SIZE; }
    //bool Full()const { return !Empty(); }

private:
    void cleanup();
    HANDLE hMapFile;
    HANDLE hDataMutex;           // 用于保护共享数据读写的互斥锁
    HANDLE hConsoleMutex;        // 用于保护控制台输出的互斥锁
    HANDLE hProduceSemaphore;    // 生产信号量
    HANDLE hConsumeSemaphore;    // 消费信号量
    HANDLE hCycleMutex;          // 用于保护循环计数的互斥锁
    SharedData* pSharedData;
};