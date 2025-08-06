#include "time.h"

int main()
{
    int cnt=10;
    while(cnt>=0)
    {
        printf("%2d\r",cnt);
        fflush(stdout);
        sleep(1);
        cnt--;
    }
    printf("\n");
    return 0;
}
