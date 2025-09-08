#include <iostream>
#include <queue>
#include <pthread.h>
using namespace std;

template <class T>
class CP_Queue
{
    static const int defualt_cap = 15;

public:
    CP_Queue(int cap = defualt_cap) : _cap(cap)
    {
        pthread_mutex_init(&mutex, nullptr);
        pthread_cond_init(&c_cond, nullptr);
        pthread_cond_init(&p_cond, nullptr);
        low_water = cap / 3;
        hight_water = 2 * cap / 3;
    }

    T pop()
    {
        pthread_mutex_lock(&mutex);
        while (_q.size() == 0)
        {
            pthread_cond_wait(&c_cond, &mutex);
        }

        T task = _q.front();
        _q.pop();

        if(_q.size()<low_water) pthread_cond_signal(&p_cond);
        pthread_mutex_unlock(&mutex);
        return task;
    }
    void push(const T &task)
    {
        pthread_mutex_lock(&mutex);
        while (_q.size() == _cap)
        {
            pthread_cond_wait(&p_cond, &mutex);
        }
        _q.push(task);
        if(_q.size()>hight_water) pthread_cond_signal(&c_cond);
        pthread_mutex_unlock(&mutex);
    }

    ~CP_Queue()
    {
        pthread_mutex_destroy(&mutex);
        pthread_cond_destroy(&c_cond);
        pthread_cond_destroy(&p_cond);
    }

private:
    int _cap;
    int low_water;
    int hight_water;
    queue<T> _q;
    pthread_mutex_t mutex;
    pthread_cond_t c_cond; // 消费者
    pthread_cond_t p_cond; // 生产者
};