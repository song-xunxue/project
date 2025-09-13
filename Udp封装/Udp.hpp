#pragma once

#include <iostream>
#include <string>
#include <cstring>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <functional>
#include <unistd.h> // 添加close函数

#include "Log.hpp"

using namespace std;

#define SERVE 1
#define CLIENT 2
#define defaultUpd SERVE

const uint16_t defaultport = 8080;
const string defaultip = "0.0.0.0"; // 当服务器绑定到"0.0.0.0"时，它会监听所有网络接口 包括本地回环地址
const int size = 1024;
Log Mylog;

using func_t = function<string(const string)>;

enum
{
    SOCKET_ERR = 1,
    BIND_ERR
};

class Udp
{
public:
    Udp(const uint16_t &port = defaultport, const string &ip = defaultip, int type = defaultUpd)
        : socket_(0),
          ip_(ip),
          port_(port),
          UdpType(type),
          isrunning(false)
    {
        // // 初始化服务器地址结构
        // memset(&server_addr_, 0, sizeof(server_addr_));
        // server_addr_.sin_family = AF_INET;
        // server_addr_.sin_port = htons(port_);
        // server_addr_.sin_addr.s_addr = inet_addr(ip_.c_str());
    }

    void Init()
    {
        // 1.创建socket
        socket_ = socket(AF_INET, SOCK_DGRAM, 0);
        if (socket_ < 0)
        {
            Mylog(Error, "套接字创建失败\n");
            exit(SOCKET_ERR);
        }

        // 2.socket 结构体变量初始化
        // struct sockaddr_in local;
        bzero(&local, sizeof(local));                   // 初始化为0
        local.sin_family = AF_INET;                     // 声明为sockaddr_in
        local.sin_port = htons(port_);                  // 统一转化为网络字节序列,大端
        local.sin_addr.s_addr = inet_addr(ip_.c_str()); // ip字符串转化为 4 * 8bit位 的  uint32_t ip

        Mylog(Info, "Server success, ip: %s", ip_.c_str());
        if (UdpType & SERVE)
        {
            // 3.bind  服务器端需要绑定 客户端在发送数据时自动绑定
            if (bind(socket_, (const struct sockaddr *)&local, sizeof(local)) < 0)
            {
                Mylog(Fatal, "bind error, errno: %d, err string: %s", errno, strerror(errno));
                exit(BIND_ERR);
            }
            Mylog(Info, "bind success, errno: %d, err string: %s", errno, strerror(errno));
        }
    }

    // 客户端设置服务器地址
    // void SetServerAddress(const string &server_ip, uint16_t server_port)
    // {
    //     memset(&server_addr_, 0, sizeof(server_addr_));
    //     server_addr_.sin_family = AF_INET;
    //     server_addr_.sin_port = htons(server_port);
    //     server_addr_.sin_addr.s_addr = inet_addr(server_ip.c_str());
    // }

    void ServerRun(func_t func)
    {
        isrunning = true;
        char inbuffer[4096];
        while (isrunning)
        {
            struct sockaddr_in client;
            socklen_t len = sizeof(client);
            ssize_t n = recvfrom(socket_, inbuffer, sizeof(inbuffer) - 1, 0, (struct sockaddr *)&client, &len);
            if (n < 0)
            {
                Mylog(Error, "Serve 接受失败\n");
                continue;
            }
            inbuffer[n] = 0;

            // 获取客户端信息
            char client_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &(client.sin_addr), client_ip, INET_ADDRSTRLEN);
            uint16_t client_port = ntohs(client.sin_port);

            Mylog(Info, "Received message from %s:%d", client_ip, client_port);

            string info = inbuffer;
            string echo_string = func(info);
            cout << "Server accpet:" << echo_string << endl;
            // sendto(socket_, echo_string.c_str(), echo_string.size(), 0,
            //        (const sockaddr *)&client, len);
        }
    }

    void ClientRun()
    {
        isrunning = true;
        char outbuffer[4096];
        char inbuffer[4096];

        while (isrunning)
        {
            cout << "Please Enter@ ";
            string message;
            getline(cin, message);

            if (message == "quit" || message == "exit")
            {
                isrunning = false;
                break;
            }

            // 发送消息到服务器
            ssize_t sent_bytes = sendto(socket_, message.c_str(), message.size(), 0,
                                        (struct sockaddr *)&local, sizeof(local));

            if (sent_bytes < 0)
            {
                Mylog(Error, "发送失败");
                continue;
            }

            // 接收服务器响应
            // struct sockaddr_in from_addr;
            // socklen_t from_len = sizeof(from_addr);
            // ssize_t recv_bytes = recvfrom(socket_, inbuffer, sizeof(inbuffer) - 1, 0,
            //                               (struct sockaddr *)&from_addr, &from_len);
            // if (recv_bytes > 0)
            // {
            //     inbuffer[recv_bytes] = 0;
            //     cout << "Server response: " << inbuffer << endl;
            // }
            // else
            // {
            //     Mylog(Error, "接收失败");
            // }
        }
    }

    void Run(func_t func)
    {
        if (UdpType & SERVE)
        {
            ServerRun(func);
        }
        else if (UdpType & CLIENT)
        {
            ClientRun();
        }
    }

    ~Udp()
    {
        if (socket_ > 0)
            close(socket_);
    }

private:
    int socket_;    // 套接字文件描述符
    string ip_;     // 本地IP地址
    uint16_t port_; // 端口号
    bool isrunning; // 运行状态
    int UdpType;    // 服务器或客户端类型
    // struct sockaddr_in server_addr_; // 服务器地址信息（客户端使用）
    struct sockaddr_in local; // 本Udp使用的套接字 客户端存储服务器 服务器用于初始化
};