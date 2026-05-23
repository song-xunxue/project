#李文煜 1120233042

import pandas as pd

# 读取数据
data = pd.read_csv("./nba.csv")

# 1. 基本操作
print("="*50)
print("数据前5行：")
print(data.head())
print("\n数据后5行：")
print(data.tail())
print("\n数据信息：")
print(data.info())
print("\n数据描述统计：")
print(data.describe())

# 2. 增加单行（使用整数索引）
next_index = len(data)
data.loc[next_index] = ["limei", "Utah Jazz", 24.0, 'PG', 26.0, '6-2', 180.0, "Kansas", 15000000.0]
data.loc[next_index + 1] = ["lihua", "Utah Jazz", 25.0, 'PG', 27.0, '6-3', 190.0, "Kansas", 12000000.0]
data.loc[next_index + 2] = ["libai", "Utah Jazz", 26.0, 'PG', 28.0, '6-4', 200.0, "Kansas", 11000000.0]

print("\n增加行后的数据后5行：")
print(data.tail())

# 3. 删除操作
# 删除错误的身高列
print("\n删除前的列名：", data.columns.tolist())
print(f"数据形状（删除前）：{data.shape}")

# 删除Height列
data = data.drop('Height', axis=1)
# 或者使用：data.drop('Height', axis=1, inplace=True)

print(f"\n删除Height列后的列名：{data.columns.tolist()}")
print(f"数据形状（删除后）：{data.shape}")



# 删除之前添加的一行
data = data.drop(index=next_index + 1)
print(f"\n删除'lihua'行后，剩余 {len(data)} 行数据")

# 4. 修改操作
# 修改某行数据
# 例如：修改libai的薪水
data.loc[next_index + 2, 'Salary'] = 13000000.0
print(f"\n修改libai的薪水后：{data.loc[next_index + 2, 'Name']} 的薪水为 {data.loc[next_index + 2, 'Salary']}")

# 5. 条件过滤：选出salary大于1000万且position为PG的球员
filtered_data = data[(data['Salary'] > 10000000) & (data['Position'] == 'PG')]
print("\n薪水大于1000万且位置为PG的球员：")
print(filtered_data[['Name', 'Team', 'Position', 'Salary']])

# 显示符合条件的球员数量
print(f"\n共找到 {len(filtered_data)} 名符合条件的球员")

# 额外：按薪水排序显示
if len(filtered_data) > 0:
    print("\n按薪水降序排列：")
    print(filtered_data[['Name', 'Team', 'Position', 'Salary']].sort_values('Salary', ascending=False))