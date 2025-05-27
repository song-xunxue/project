#pragma once
#include <iostream>
#include <cstdlib>
#include <ctime>
using namespace std;
// 使用宏定义棋盘的行数和列数
//由于编译器的原因实现不了选择棋盘大小
#define ROW 9
#define COL 9
// 定义雷的数量
#define EASY_COUNT 10
// 实际棋盘大小，为了避免越界，在9x9的基础上增加2行2列
#define ROWS (ROW + 2)
#define COLS (COL + 2)

// 初始化棋盘函数声明
void InitBoard(char board[ROWS][COLS], int rows, int cols, char set);
// 打印棋盘函数声明
void PrintBoard(char board[ROWS][COLS], int row, int col);
// 设置雷的位置函数声明
void SetMine(char board[ROWS][COLS], int rows, int cols);
// 查找雷的函数声明
void FindMine(char mine[ROWS][COLS], char show[ROWS][COLS], int rows, int cols);
// 展开无雷区域函数声明
void Spread(char mine[ROWS][COLS], char show[ROWS][COLS], int x, int y, int* win);