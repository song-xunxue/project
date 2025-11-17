#include <windows.h>
#include <iostream>
#include <string>
#include <vector>
#include "Common.h"


int main()
{
    cout << "主程序 (PID: " << GetCurrentProcessId() << ") 启动。" << endl;

    IPCManager ipcManager;
    if (!ipcManager.createResources()) {
        return 1;
    }
    cout << "主程序：共享资源创建成功。" << endl;

    // 创建一个 vector 来存储所有子进程的句柄信息
    vector<PROCESS_INFORMATION> piList;
    piList.reserve(NUM_PRODUCERS + NUM_CONSUMERS); // 预分配内存提高效率

    string producerCmd = "producer.exe " + std::to_string(NUM_PRODUCERS) + " " + std::to_string(NUM_CONSUMERS);
    string consumerCmd = "consumer.exe"; // 消费者不需要参数
    vector<char> producerCmdVec(producerCmd.begin(), producerCmd.end());
    producerCmdVec.push_back('\0');
    vector<char> consumerCmdVec(consumerCmd.begin(), consumerCmd.end());
    consumerCmdVec.push_back('\0');

    // 使用循环来启动多个生产者
    cout << "主程序：准备启动 " << NUM_PRODUCERS << " 个生产者进程..." << endl;
    for (int i = 0; i < NUM_PRODUCERS; ++i) {
        STARTUPINFO si = { sizeof(si) };
        PROCESS_INFORMATION pi;
        if (CreateProcessA(NULL, producerCmdVec.data(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
            piList.push_back(pi); // 成功后，将句柄信息存起来
        }
        else {
            cerr << "创建生产者进程 " << i << " 失败, 错误码: " << GetLastError() << endl;
        }
    }

    // 使用循环来启动多个消费者
    cout << "主程序：准备启动 " << NUM_CONSUMERS << " 个消费者进程..." << endl;
    for (int i = 0; i < NUM_CONSUMERS; ++i) {
        STARTUPINFO si = { sizeof(si) };
        PROCESS_INFORMATION pi;
        if (CreateProcessA(NULL, consumerCmdVec.data(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
            piList.push_back(pi); // 存起来
        }
        else {
            cerr << "创建消费者进程 " << i << " 失败, 错误码: " << GetLastError() << endl;
        }
    }

    cout << "主程序：所有 " << piList.size() << " 个子进程已启动，等待它们全部结束..." << endl;

    // 等待所有子进程结束
    if (!piList.empty()) {
        vector<HANDLE> processHandles;
        for (const auto& pi : piList) {
            processHandles.push_back(pi.hProcess);
        }
        WaitForMultipleObjects(processHandles.size(), processHandles.data(), TRUE, INFINITE);
    }

    cout << "主程序：所有子进程已结束，即将退出。" << endl;

    // 清理所有子进程的句柄
    for (const auto& pi : piList) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    return 0;
}