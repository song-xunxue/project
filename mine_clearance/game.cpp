#include "game.h"

// 初始化棋盘函数实现
void InitBoard(char board[ROWS][COLS], int rows, int cols, char set) 
{
    for (int i = 0; i < rows; i++) 
    {
        for (int j = 0; j < cols; j++)
        {
            // 将棋盘的每个位置初始化为指定字符
            board[i][j] = set;
        }
    }
}

// 打印棋盘函数实现
void PrintBoard(char board[ROWS][COLS], int row, int col) {
    cout << "-------扫雷-------" << endl;
    // 打印列号
    for (int i = 0; i <= col; i++) {
        cout << i << " ";
    }
    cout << endl;
    for (int i = 1; i <= row; i++) {
        // 打印行号
        cout << i << " ";
        for (int j = 1; j <= col; j++) {
            // 打印棋盘每个位置的字符
            cout << board[i][j] << " ";
        }
        cout << endl;
    }
    cout << "-------扫雷-------" << endl;
}

// 设置雷的位置函数实现
void SetMine(char board[ROWS][COLS], int rows, int cols) 
{
    int count = EASY_COUNT;
    while (count) 
    {
        // 生成随机的行和列坐标
        int x = rand() % ROW + 1;
        int y = rand() % COL + 1;
        if (board[x][y] != '1')
        {
            // 在随机位置放置雷
            board[x][y] = '1';
            count--;
        }
    }
}

// 计算指定位置周围雷的数量函数
char Showmine(char board[ROWS][COLS], int x, int y)
{
    return (board[x - 1][y - 1] + board[x - 1][y] + board[x - 1][y + 1] + board[x][y - 1] + board[x][y + 1] + board[x + 1][y - 1] + board[x + 1][y] + board[x + 1][y + 1] - 8 * '0');
}

// 展开无雷区域函数实现
void Spread(char mine[ROWS][COLS], char show[ROWS][COLS], int x, int y, int* win)
{
    if (x < 1 || x > ROW || y < 1 || y > COL || show[x][y] != '*')
    {
        return;
    }
    int r = Showmine(mine, x, y);
    if (r > 0) 
    {
        show[x][y] = r + '0';
        (*win)++;
        return;
    }
    show[x][y] = '0';
    (*win)++;
    // 递归展开周围的格子
    Spread(mine, show, x - 1, y - 1, win);
    Spread(mine, show, x - 1, y, win);
    Spread(mine, show, x - 1, y + 1, win);
    Spread(mine, show, x, y - 1, win);
    Spread(mine, show, x, y + 1, win);
    Spread(mine, show, x + 1, y - 1, win);
    Spread(mine, show, x + 1, y, win);
    Spread(mine, show, x + 1, y + 1, win);
}

// 查找雷的函数实现
void FindMine(char mine[ROWS][COLS], char show[ROWS][COLS], int rows, int cols)
{
    int x, y = 0;
    int win = 0;
    while (win < ROW * COL - EASY_COUNT)
    {
        cout << "请输入需要排查的坐标:>" << endl;
        cin >> x >> y;
        if (x >= 1 && x <= ROW && y >= 1 && y <= COL) 
        {
            if (mine[x][y] == '1')
            {
                cout << "很遗憾，这是雷，你被炸死了" << endl;
                // 打印雷的分布
                PrintBoard(mine, ROW, COL);
                break;
            }
            else 
            {
                Spread(mine, show, x, y, &win);
                // 打印更新后的棋盘
                PrintBoard(show, ROW, COL);
                cout << "还有" << ROW * COL - EASY_COUNT - win << "次排查完" << endl;
            }
        }
        else
        {
            cout << "输入的坐标错误，请重新输入" << endl;
        }
    }
    if (win == ROW * COL - EASY_COUNT) 
    {
        cout << "恭喜你，排雷成功" << endl;
    }
}
