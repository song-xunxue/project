#include "Common.h"

// 共享资源的全局唯一名称
const char SHARED_MEM_NAME[] = "ProducerConsumer_SharedMemory";
const char DATA_MUTEX_NAME[] = "ProducerConsumer_DataMutex";
const char CONSOLE_MUTEX_NAME[] = "ProducerConsumer_ConsoleMutex";
const char PRODUCE_SEM_NAME[] = "ProducerConsumer_ProduceSem";
const char CONSUME_SEM_NAME[] = "ProducerConsumer_ConsumeSem";
const char CYCLE_MUTEX_NAME[] = "ProducerConsumer_CycleMutex";

IPCManager::IPCManager() : hMapFile(NULL), hDataMutex(NULL), hConsoleMutex(NULL),
hProduceSemaphore(NULL), hConsumeSemaphore(NULL), hCycleMutex(NULL), pSharedData(NULL) {}

IPCManager::~IPCManager() {
    cleanup();
}

bool IPCManager::createResources() {
    // 创建互斥锁
    hDataMutex = CreateMutexA(NULL, FALSE, DATA_MUTEX_NAME);
    hConsoleMutex = CreateMutexA(NULL, FALSE, CONSOLE_MUTEX_NAME);
    hCycleMutex = CreateMutexA(NULL, FALSE, CYCLE_MUTEX_NAME);

    // 创建信号量 - 初始允许生产，不允许消费
    hProduceSemaphore = CreateSemaphoreA(NULL, 1, 1, PRODUCE_SEM_NAME);
    hConsumeSemaphore = CreateSemaphoreA(NULL, 0, 1, CONSUME_SEM_NAME);

    if (hDataMutex == NULL || hConsoleMutex == NULL || hProduceSemaphore == NULL ||
        hConsumeSemaphore == NULL || hCycleMutex == NULL) {
        cerr << "创建同步对象失败, 错误码: " << GetLastError() << endl;
        return false;
    }

    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, sizeof(SharedData), SHARED_MEM_NAME);

    if (hMapFile == NULL) {
        cerr << "创建文件映射失败, 错误码: " << GetLastError() << endl;
        return false;
    }

    pSharedData = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (pSharedData == NULL) {
        cerr << "映射共享内存失败, 错误码: " << GetLastError() << endl;
        return false;
    }
    pSharedData->read_pos = 0;
    pSharedData->write_pos = 0;
    pSharedData->count = 0;
    pSharedData->task_id_counter = 0;
    pSharedData->full_cycles = 0;
    pSharedData->production_finished = 0;

    return true;
}

bool IPCManager::openResources() {
    hDataMutex = OpenMutexA(MUTEX_ALL_ACCESS, FALSE, DATA_MUTEX_NAME);
    hConsoleMutex = OpenMutexA(MUTEX_ALL_ACCESS, FALSE, CONSOLE_MUTEX_NAME);
    hProduceSemaphore = OpenSemaphoreA(SEMAPHORE_ALL_ACCESS, FALSE, PRODUCE_SEM_NAME);
    hConsumeSemaphore = OpenSemaphoreA(SEMAPHORE_ALL_ACCESS, FALSE, CONSUME_SEM_NAME);
    hCycleMutex = OpenMutexA(MUTEX_ALL_ACCESS, FALSE, CYCLE_MUTEX_NAME);

    if (hDataMutex == NULL || hConsoleMutex == NULL || hProduceSemaphore == NULL ||
        hConsumeSemaphore == NULL || hCycleMutex == NULL) {
        cerr << "打开同步对象失败, 错误码: " << GetLastError() << endl;
        return false;
    }

    hMapFile = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, SHARED_MEM_NAME);
    if (hMapFile == NULL) {
        cerr << "打开文件映射失败, 错误码: " << GetLastError() << endl;
        return false;
    }

    pSharedData = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (pSharedData == NULL) {
        cerr << "映射共享内存失败, 错误码: " << GetLastError() << endl;
        return false;
    }

    return true;
}

void IPCManager::cleanup() {
    if (pSharedData != NULL) UnmapViewOfFile(pSharedData);
    if (hMapFile != NULL) CloseHandle(hMapFile);
    if (hDataMutex != NULL) CloseHandle(hDataMutex);
    if (hConsoleMutex != NULL) CloseHandle(hConsoleMutex);
    if (hProduceSemaphore != NULL) CloseHandle(hProduceSemaphore);
    if (hConsumeSemaphore != NULL) CloseHandle(hConsumeSemaphore);
    if (hCycleMutex != NULL) CloseHandle(hCycleMutex);
}