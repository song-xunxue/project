
#include "Udp.hpp"
int main()
{
    Udp server(8080, "127.0.0.1", SERVE);
    server.Init();

    // 定义处理函数
    auto handler = [](const string &msg) -> string
    {
        return msg;
    };

    server.Run(handler);
    return 0;
}