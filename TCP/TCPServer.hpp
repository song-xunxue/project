#pragma once
#include <iostream>
#include <iostream>
#include <string>
#include <cstring>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <functional>
#include <unistd.h>
#include <pthread.h>
#include "Log.hpp"
// using namespace std;

const uint16_t defualtport = 8080;
const std::string defualtip = "127.0.0.1";
Log Mylog;

enum
{
    SOCKET_ERROR = 1,
    BIND_ERROR
};

class TCPServer
{

public:
    TCPServer(const uint16_t port = defualtport, const std::string ip = defualtip)
        : _ip(ip),
          _port(port)
    {
    }
    TCPServer() {}
    void Init()
    {
        _listensocket = socket(AF_INET, SOCK_STREAM, 0);
        if (_listensocket < 0)
        {
            Mylog(Fatal, "_listensocket error");
            exit(SOCKET_ERROR);
        }
        Mylog(Info, "_listensocket succes");
        sockaddr_in local;
        memset(&local, 0, sizeof(local));
        local.sin_family = AF_INET;
        local.sin_port = htons(_port);
        // local.sin_addr.s_addr=inet_addr(_ip.c_str())
        inet_aton(_ip.c_str(), &(local.sin_addr)); // inet_aton IPV4专属 inet_pton 通用IPV4、6
        // 內核綁定
        if (bind(_listensocket, (const sockaddr *)(&local), sizeof(local)) < 1)
        {
            Mylog(Fatal, "Bind listensocket error");
            exit(BIND_ERROR);
        }
        Mylog(Info, "Bind succes");
    }

    void Serve(int sockfd, std::string ip, uint16_t port)
    {
        //
        ;
    }

    void Start()
    {
        Mylog(Info, "Server start succes");
        while (true)
        {

            struct sockaddr_in client;
            socklen_t len = sizeof(client);
            int sockfd = accept(_listensocket, (struct sockaddr *)&client, &len);
            if (sockfd < 0)
            {
                Mylog(Fatal, "accept error:%s", errno);
                continue;
            }
            // 获取客户端的ip和端口进行服务
            char clientip[32];
            // std::string clientip=inet_ntoa(client.sin_addr);
            inet_ntop(AF_INET, &client.sin_addr, clientip, sizeof(clientip));

            uint16_t clientport = ntohs(client.sin_port);//转为主机字节序
            Serve(sockfd, clientip, clientport);
            // 1.单进程

            // pid_t fd=fork();
            // if(fd==0)
            // {
            //     //子进程

            // }
        }
    }

    ~TCPServer()
    {
    }

private:
    int _listensocket;
    std::string _ip;
    uint16_t _port;
    bool isruuning;
};
