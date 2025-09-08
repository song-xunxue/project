#include "cp.cpp"
#include <unistd.h>
#include <ctime>

void *Product(void* args)
{
    CP_Queue<int> *bq = static_cast<CP_Queue<int> *>(args);
    int i = 1;
    while (true)
    {
        bq->push(i);
        cout << " 生产一个任务：" << i++ << endl;
    }
}

void *Constume(void *args)
{
    CP_Queue<int> *bq = static_cast<CP_Queue<int> *>(args);
    while(true)
    {
        sleep(1);
        int cnt=bq->pop();
        cout << " 消费一个任务：" << cnt << endl;
    }
}

int main()
{
    CP_Queue<int> bq;
    pthread_t p, c;
    pthread_create(&p, nullptr, Product, &bq);
    pthread_create(&c, nullptr, Constume, &bq);

    pthread_join(p, nullptr);
    pthread_join(c, nullptr);
    return 0;
}