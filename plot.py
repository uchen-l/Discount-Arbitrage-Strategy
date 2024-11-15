import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

# 设置中文字体

# Change the current working directory
os.chdir(r"C:\\Users\\tongyu\\Desktop\\贴水套利")
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

und_code = '000852.SH'
# Load the Excel file
file_path = f'{und_code}_q_diff.xlsx'  # 确保文件在指定的目录中
excel_data = pd.ExcelFile(file_path)

# Initialize a dictionary to store results
mean_data = pd.DataFrame(index=['隔季', '下季', '下月', '当月'], columns=['1M_discount_error', '3M_discount_error', '6M_discount_error', '12M_discount_error'])
std_data = pd.DataFrame(index=['隔季', '下季', '下月', '当月'], columns=['1M_discount_error', '3M_discount_error', '6M_discount_error', '12M_discount_error'])

# Iterate through each sheet and populate the DataFrames with mean and std values
for sheet_name in excel_data.sheet_names:
    sheet_data = excel_data.parse(sheet_name)
    
    # Determine which q_error is present in this sheet
    for q_error in ['1M_discount_error', '3M_discount_error', '6M_discount_error', '12M_discount_error']:
        if q_error in sheet_data.columns:
            grouped = sheet_data.groupby('合约类型')[q_error].agg(['mean', 'std'])
            mean_data[q_error] = grouped['mean']
            std_data[q_error] = grouped['std']

# Plot heatmaps
plt.figure(figsize=(14, 6))

# Heatmap for means
plt.subplot(1, 2, 1)
sns.heatmap(mean_data, annot=True, cmap="coolwarm", center=0, fmt=".4f")
plt.title("平均值热力图")
plt.xlabel("implied_q_type")
plt.ylabel("合约类型")

# Heatmap for standard deviations
plt.subplot(1, 2, 2)
sns.heatmap(std_data, annot=True, cmap="coolwarm", center=0, fmt=".4f")
plt.title("标准差热力图")
plt.xlabel("implied_q_type")
plt.ylabel("合约类型")

# main title for the whole plot
plt.suptitle(f'{und_code}场内外贴水差额')
plt.tight_layout()
plt.show()


# 找到指定的 sheet 中的数据 (假设 und_code 是 '000016.SH')
# und_code = '000016.SH'
sheet_name = f"{und_code}_244天"
sheet_data = excel_data.parse(sheet_name)

# 筛选合约类型为 '隔季' 的数据
filtered_data = sheet_data[sheet_data['合约类型'] == '隔季']

# 提取日期、implied_q 和 12M_discount_error
dates = filtered_data['日期']
implied_q = filtered_data['12M_discount_error']
discount_error = filtered_data['贴水收益']

# 创建图表，设置图像的长宽比为4:1
fig, ax = plt.subplots(figsize=(16, 4))

# 画出 implied_q 的折线图
ax.plot(dates, implied_q, color='tab:blue', label='Implied Q (12M)', linewidth=1.5)

# 画出 12M_discount_error 的柱状图，柱子稍微粗一点
ax.bar(dates, discount_error, color='tab:orange', alpha=0.6, label='12M Discount Error', width=0.7)

# 设置统一的y轴刻度
ax.set_ylabel('Value', color='black')
ax.set_xlabel('日期')

# 设置图例
ax.legend()

# 设置图表标题
plt.title(f'{und_code} 隔季贴水误差 和 12M隐含贴水误差分布')

# 显示图表
plt.show()