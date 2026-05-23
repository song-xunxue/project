# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

机器学习实践课程作业项目，包含多个独立练习，每个练习放在以"作业X"命名的子目录中。

## 项目结构

- **作业一/** — Pandas 数据操作 + 梯度下降线性回归
  - `Exercise 1.py` — NBA 球员 CSV 数据的增删改查与条件过滤
  - `Exercise 2.py` — 一元线性回归（梯度下降），含数据标准化、多学习率对比、可视化
  - `nba.csv` — NBA 球员数据集（Exercise 1 使用）
- **作业二/** — 待定
  - `vaccine.csv` — 疫苗接种率时间序列数据
- **作业三/** — 决策树预测学生G3成绩
  - `decision_tree.py` — 决策树回归，LabelEncoder编码，2-8分割
  - `student.csv` — 学生成绩数据集（含G1/G2/G3）

每个作业目录独立运行，无跨目录依赖。

## 运行方式

使用 conda 环境执行 Python 脚本，推荐环境：`mypytorch`（含 numpy/pandas/matplotlib/scikit-learn）。

```bash
# 运行单个练习
C:/Users/26904/anaconda3/envs/mypytorch/python.exe "作业一/Exercise 1.py"
C:/Users/26904/anaconda3/envs/mypytorch/python.exe "作业一/Exercise 2.py"
```

注意：脚本中使用相对路径读取 CSV（如 `./nba.csv`），需在对应作业目录下运行，或修改为绝对路径。

## 代码约定

- 作者署名：`李文煜 1120233042`
- 头部 docstring 简洁：只写任务描述 + `李文煜 1120233042`，不写日期和变更日志
- 章节注释用 `# 1.读取数据` 形式，**不用** `---`/`====` 装饰分隔线
- 函数调用时行尾注释说明函数作用和关键参数
- 中文注释和输出
- matplotlib 中文字体：`Microsoft YaHei` / `SimHei`
- 图片输出：PNG，dpi 300
