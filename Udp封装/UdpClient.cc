#include "Udp.hpp"

int main()
{
    Udp client(8080, "127.0.0.1", CLIENT); // 设置服务器地址
    client.Init();

    // 运行客户端
    client.Run([](const string &) -> string
               {
                   return ""; // 客户端模式下处理函数不会被使用
               });
    return 0;
}