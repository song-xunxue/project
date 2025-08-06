
#include "game.h"

// 菜单函数
void Menu() {
    std::cout << "**********************" << std::endl;
    std::cout << "*******扫雷游戏*******" << std::endl;
    std::cout << "***** 1.开始游戏 *****" << std::endl;
    std::cout << "***** 0.结束游戏 *****" << std::endl;
    std::cout << "**********************" << std::endl;
}

// 游戏函数
void Game() {
    // 创建棋盘
    char mine[ROWS][COLS] = { 0 };
    char show[ROWS][COLS] = { 0 };
    // 初始化棋盘
    InitBoard(mine, ROWS, COLS, '0');
    InitBoard(show, ROWS, COLS, '*');
    // 设置雷的位置
    SetMine(mine, ROWS, COLS);
    // 打印初始棋盘
    PrintBoard(show, ROW, COL);
    // 开始排查雷
    FindMine(mine, show, ROWS, COLS);
}

int main() {
    // 初始化随机数种子
    srand((unsigned int)time(NULL));
    int input = 0;
    do {
        // 显示菜单
        Menu();
        std::cout << "请输入你的选项:>" << std::endl;
        std::cin >> input;
        switch (input) {
        case 1:
            // 开始游戏
            Game();
            break;
        case 0:
            std::cout << "游戏结束" << std::endl;
            break;
        default:
            std::cout << "输入错误，请重新输入" << std::endl;
            break;
        }
    } while (input);
    return 0;
}