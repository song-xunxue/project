"""
进阶版：从乐学课程原始数据中分析学生行为，提取特征，使用SVM预测成绩等级

fig4-6

李文煜 1120233042
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.metrics import ConfusionMatrixDisplay
import warnings

warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 1.读取原始数据
print("=" * 60)
print("进阶版：从原始数据提取特征 + SVM预测")
print("=" * 60)

DATA_DIR = "./乐学课程数据2023"

# read_csv() / read_excel() — 读取不同格式的数据文件
result = pd.read_csv(f"{DATA_DIR}/mdl_programming_result.csv", encoding='gbk')
grade = pd.read_excel(f"{DATA_DIR}/student_grade.xlsx")
programming = pd.read_csv(f"{DATA_DIR}/mdl_programming.CSV", encoding='gbk')

print(f"\n数据文件:")
print(f"  提交结果表: {result.shape}  (学生×题目的提交统计)")
print(f"  成绩表: {grade.shape}  (学生最终成绩)")
print(f"  题目表: {programming.shape}  (编程题目信息)")

# submits 文件很大(123MB)，分批读取关键列以节省内存
print(f"\n正在读取提交记录（较大，需等待）...")
submits = pd.read_excel(f"{DATA_DIR}/mdl_programming_submits.xlsx",
                        usecols=['id', 'programmingid', 'userid', 'timemodified',
                                 'codelines', 'codesize', 'timeused', 'judgeresult', 'passed'])
print(f"  提交记录: {submits.shape}")

# 2.特征提取
print("\n" + "=" * 60)
print("特征提取")
print("=" * 60)

# --- 特征1: 从 result 表提取每个学生的做题统计 ---
# groupby('userid') — 按学生分组
# agg() — 对每组计算聚合统计量

result_features = result.groupby('userid').agg(
    total_problems=('programmingid', 'nunique'),       # nunique() — 不重复的题目数 = 完成了几道不同的题
    total_submits=('submitcount', 'sum'),               # sum() — 总提交次数
    avg_submits=('submitcount', 'mean'),                # mean() — 平均每题提交次数
    max_submits=('submitcount', 'max'),                 # max() — 单题最多提交次数
    min_submits=('submitcount', 'min'),                 # min() — 单题最少提交次数
).reset_index()  # reset_index() — 把分组键从索引变回普通列

print(f"\n特征1(做题统计): {result_features.shape}")
print(result_features.head(3).to_string())

# --- 特征2: 从 submits 表提取提交行为特征 ---
# judgeresult 含义: AC=通过, WA=答案错误, CE=编译错误, RE=运行错误, TLE=超时

# 先统计每个学生的AC(通过)次数
ac_count = submits[submits['judgeresult'] == 'AC'].groupby('userid').size().reset_index(name='ac_count')
# groupby().size() — 统计每组的行数

# 每个学生的总提交次数
submit_total = submits.groupby('userid').size().reset_index(name='submit_total')

# 平均代码行数和代码大小
code_stats = submits.groupby('userid').agg(
    avg_codelines=('codelines', 'mean'),                # 平均代码行数
    avg_codesize=('codesize', 'mean'),                  # 平均代码大小(字节)
    avg_timeused=('timeused', 'mean'),                  # 平均运行耗时
).reset_index()

# 首次提交通过率: passed=1 表示通过
first_pass = submits.groupby('userid')['passed'].mean().reset_index(name='first_pass_rate')

# 秒交行为: timeused < 0.01秒 认为是秒交（没有认真思考就提交）
quick_submits = submits[submits['timeused'] < 0.01].groupby('userid').size().reset_index(name='quick_submit_count')

# 合并所有提交特征
submit_features = submit_total.merge(ac_count, on='userid', how='left')
submit_features = submit_features.merge(code_stats, on='userid', how='left')
submit_features = submit_features.merge(first_pass, on='userid', how='left')
submit_features = submit_features.merge(quick_submits, on='userid', how='left')
# merge(on='userid', how='left') — 以userid为键左连接，保留所有学生

# 填充NaN（某些学生可能没有AC记录或秒交记录）
submit_features.fillna(0, inplace=True)

# 计算衍生特征
submit_features['ac_rate'] = submit_features['ac_count'] / submit_features['submit_total']  # AC率
submit_features['quick_rate'] = submit_features['quick_submit_count'] / submit_features['submit_total']  # 秒交率

print(f"\n特征2(提交行为): {submit_features.shape}")
print(submit_features.head(3).to_string())

# --- 特征3: 从 log 表提取学习活跃度 ---
print(f"\n正在读取活动日志（较大，需等待）...")
logs = pd.read_excel(f"{DATA_DIR}/mdl_log.xlsx",
                     usecols=['userid', 'action', 'module', 'time'])
print(f"  日志记录: {logs.shape}")

# 统计每个学生的活跃次数
log_count = logs.groupby('userid').size().reset_index(name='log_count')

# 统计不同操作类型次数
# pivoted: 行=userid, 列=action类型, 值=次数
log_action = logs.groupby(['userid', 'action']).size().unstack(fill_value=0).reset_index()
# unstack(fill_value=0) — 将多层索引转为宽表，空值填0

# 只保留关键操作列
key_actions = ['view', 'view all', 'edit', 'update']  # 查看、浏览全部、编辑、更新
existing_actions = [c for c in key_actions if c in log_action.columns]
log_action = log_action[['userid'] + existing_actions]

# 学习时间跨度（最后一次操作 - 第一次操作的时间差）
log_time = logs.groupby('userid')['time'].agg(['min', 'max']).reset_index()
log_time['active_days'] = (log_time['max'] - log_time['min']) / 86400  # 86400秒=1天
# 学习活跃天数

log_features = log_count.merge(log_action, on='userid', how='left')
log_features = log_features.merge(log_time[['userid', 'active_days']], on='userid', how='left')
log_features.fillna(0, inplace=True)

print(f"\n特征3(学习活跃度): {log_features.shape}")
print(log_features.head(3).to_string())

# 3.合并所有特征 + 成绩标签
print("\n" + "=" * 60)
print("合并特征与标签")
print("=" * 60)

# 只取"正常考试"的学生成绩
grade_valid = grade[grade['考试性质'] == '正常考试'][['userid', '折算成绩']].dropna()
# dropna() — 删除含缺失值的行

# 依次合并三组特征
features = grade_valid.merge(result_features, on='userid', how='inner')
# how='inner' — 只保留两边都有的userid
features = features.merge(submit_features, on='userid', how='inner')
features = features.merge(log_features, on='userid', how='inner')

print(f"\n合并后数据集: {features.shape}")
print(f"特征列: {features.drop(columns=['userid', '折算成绩']).columns.tolist()}")
print(f"学生数: {len(features)}")

# 4.构造标签
print("\n" + "=" * 60)
print("构造成绩等级标签")
print("=" * 60)

y_raw = features['折算成绩']
X = features.drop(columns=['userid', '折算成绩'])

def grade_to_label(score):
    """将百分制成绩转为等级标签"""
    if score < 60:
        return 0  # 不及格
    elif score < 75:
        return 1  # 及格
    elif score < 90:
        return 2  # 良好
    else:
        return 3  # 优秀

y = y_raw.apply(grade_to_label)

label_names = ['不及格(<60)', '及格(60-75)', '良好(75-90)', '优秀(>=90)']
print(f"\n各等级分布:")
for i, name in enumerate(label_names):
    count = (y == i).sum()
    print(f"  {name}: {count}人 ({count/len(y)*100:.1f}%)")

# 5.标准化 + 分割 + 训练
print("\n" + "=" * 60)
print("模型训练与调参")
print("=" * 60)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

print(f"训练集: {len(X_train)}条, 测试集: {len(X_test)}条")
print(f"特征数量: {X.shape[1]}")

param_grid = {
    'C': [0.1, 1, 10, 100],
    'kernel': ['linear', 'rbf'],
    'gamma': ['scale', 'auto']
}

grid_search = GridSearchCV(
    estimator=SVC(random_state=42),
    param_grid=param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)

print("\n正在进行网格搜索...")
grid_search.fit(X_train, y_train)

print(f"\n最优参数: {grid_search.best_params_}")
print(f"最优CV准确率: {grid_search.best_score_:.4f}")

best_model = grid_search.best_estimator_
y_pred = best_model.predict(X_test)

# 6.评估
print("\n" + "=" * 60)
print("模型评估")
print("=" * 60)

acc = accuracy_score(y_test, y_pred)
print(f"\n测试集准确率: {acc:.4f}")
print(f"\n分类报告:")
print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))

cm = confusion_matrix(y_test, y_pred)

# 7.可视化
print("\n" + "=" * 60)
print("生成可视化图表")
print("=" * 60)

# 图1: 混淆矩阵
fig, ax = plt.subplots(figsize=(8, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label_names)
disp.plot(ax=ax, cmap='Blues', values_format='d')
plt.title('进阶版 SVM混淆矩阵', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('fig4_advanced_confusion_matrix.png', dpi=300, bbox_inches='tight')
print("已保存图1: fig4_advanced_confusion_matrix.png")
plt.show()

# 图2: 特征重要性（通过线性核SVM的系数近似）
# 用线性核单独训练一次，获取特征权重
linear_svc = SVC(kernel='linear', C=1, random_state=42)
linear_svc.fit(X_train, y_train)
# coef_ — 线性SVM的权重矩阵，形状为(n_classes, n_features)
# 取所有类别权重的绝对值平均作为特征重要性
importance = np.mean(np.abs(linear_svc.coef_), axis=0)  # axis=0 按列求平均

feature_names = X.columns.tolist()
# 排序取top15
sorted_idx = np.argsort(importance)[::-1][:15]

plt.figure(figsize=(10, 7))
plt.barh(range(len(sorted_idx)), importance[sorted_idx][::-1],
         tick_label=[feature_names[i] for i in sorted_idx][::-1],
         color='steelblue', edgecolor='black', linewidth=0.5)
plt.xlabel('特征重要性（线性SVM权重绝对值均值）', fontsize=12)
plt.title('进阶版 特征重要性 Top15', fontsize=14, fontweight='bold')
plt.grid(True, axis='x', alpha=0.3)
for i, v in enumerate(importance[sorted_idx][::-1]):
    plt.text(v + 0.001, i, f'{v:.3f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('fig5_feature_importance.png', dpi=300, bbox_inches='tight')
print("已保存图2: fig5_feature_importance.png")
plt.show()

# 图3: 各等级预测准确率
class_acc = []
for i in range(4):
    mask = y_test == i
    if mask.sum() > 0:
        class_acc.append((y_pred[mask] == i).mean())
    else:
        class_acc.append(0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 左图: 各等级人数
train_c = [(y_train == i).sum() for i in range(4)]
test_c = [(y_test == i).sum() for i in range(4)]
x_pos = np.arange(4)
ax1.bar(x_pos - 0.2, train_c, 0.4, label='训练集', color='steelblue', edgecolor='black')
ax1.bar(x_pos + 0.2, test_c, 0.4, label='测试集', color='coral', edgecolor='black')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(label_names, fontsize=10)
ax1.set_ylabel('人数', fontsize=12)
ax1.set_title('各等级人数分布', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, axis='y', alpha=0.3)

# 右图: 各等级准确率
bars = ax2.bar(label_names, class_acc, color=['#e74c3c', '#f39c12', '#2ecc71', '#3498db'],
               edgecolor='black')
ax2.set_ylabel('准确率', fontsize=12)
ax2.set_title('各等级预测准确率', fontsize=14, fontweight='bold')
ax2.set_ylim(0, 1.1)
ax2.grid(True, axis='y', alpha=0.3)
for bar, v in zip(bars, class_acc):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f'{v:.2f}', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('fig6_advanced_accuracy.png', dpi=300, bbox_inches='tight')
print("已保存图3: fig6_advanced_accuracy.png")
plt.show()

# 8.结果汇总
print("\n" + "=" * 60)
print("结果汇总")
print("=" * 60)
print(f"数据来源: 乐学课程数据2023（原始数据自行提取特征）")
print(f"提取的特征数量: {X.shape[1]}")
print(f"特征列表: {X.columns.tolist()}")
print(f"学生数: {len(features)}")
print(f"\n模型: SVM ({grid_search.best_params_['kernel']}核)")
print(f"最优参数: C={grid_search.best_params_['C']}, gamma={grid_search.best_params_['gamma']}")
print(f"\n测试集准确率: {acc:.4f}")
print(f"标签设置: 不及格(<60)=0, 及格(60-75)=1, 良好(75-90)=2, 优秀(>=90)=3")
