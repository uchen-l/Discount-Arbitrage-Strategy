import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from tqdm import tqdm
import seaborn as sns
import warnings
import math
import itertools

os.chdir(r"C:\\Users\\tongyu\Desktop\\贴水套利")
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置入参
und_code = '000905.SH'
days_list = [21,63,122,244]
contract_type_list = ['当月','下月','下季','隔季']
implied_q_month = ['1M','3M','6M','12M']
get_t = {
        '1M': 1/12,
        '3M': 3/12, 
        '6M': 6/12, 
        '12M': 1, 
    }

# def cal_implied_profit(S_start, S_end, basis_start, t, implied_q):
#     F_end_pred = S_start * math.exp(-(implied_q * t))
#     basis_end_implied = F_end_pred - S_end # 隐含基差
#     profit_implied = basis_end_implied - basis_start # 隐含基差收益
#     return profit_implied

# 读取数据

'''
这个函数主要是用于计算场内贴水的差额，我们需要传入的参数有：start_date,end_date,contract_type,duration
最后计算duration里的(q_end - q_start)的差值 q_diff。如果出现了换仓情况，则需要记录每一个contract_code的(q_end - q_start)，他们的总和是q_diff
我们会在start_date的时候开仓，买的是contract_type的合约（当月/下月/隔月/隔季）然后持有duration天
分为很多种情况：
首先是当月合约开始时的q值需要特别处理，如果剩余交易日小于5天，那么我们开始时候的q值就是下月合约的q值而非当月合约的q值，同时需要取的开仓时候的contract_name就变成了下月的
同时我们要记录/储存每次开仓时候的contract_name，因为我们需要在下一次检查是否需要换仓的时候用到
平仓逻辑是是我们目前持有的合约(记录的contract_code),如果这个合约目前的contract_type是‘当月’，对应的rem_trad_days等于2天并且那一天还没到end_date的情况下，那么我们需要换仓
我们要卖出这个合约，然后买入同一天对应contract_type的合约，同时记录这两个的q值(老合约q_end,新合约q_start)
'''

# def cal_q_diff(start_date,contract_type,duration):
def cal_q_diff(row,duration):    
    # 还是需要加入end_date的，判断是否会超出end_date
    q_diff = 0.0
    # initialized  这里如果是df1直接省略contract type也可以
    print(row)
    initial_date = row['date']
    contract_type = row['contract_type']
    rem_trad_day = row['rem_trad_days']

    # rem_trad_day = df.loc[(df['date'] == start_date) & (df['contract_type'] == contract_type), 'rem_trad_days'].values[0]
    
    unique_dates = df1['date']
    # unique_dates_df = pd.DataFrame(unique_dates, columns=['date'])
    # print(type(unique_dates))
    unique_dates.to_csv(f'{contract_type}_{duration}days_unique_dates.csv')
    end_index = df1[df1['date'] == initial_date].index[0] + duration
    end_date = df1.iloc[end_index]['date']
    unique_dates = unique_dates[(unique_dates >= initial_date) & (unique_dates <= end_date)]
    # print(unique_dates)
    # q_start = df1.loc[(df1['date'] == start_date) & (df1['contract_type'] == contract_type), 'q'].values
    if contract_type == '当月' and rem_trad_day < 5:
        contract_code = df.loc[(df['date'] == initial_date) & (df['contract_type'] == '下月'), 'contract_code'].values[0]
        q_start = df.loc[(df['date'] == initial_date) & (df['contract_type'] == '下月'), 'q'].values[0]
    else:
        contract_code = df.loc[(df['date'] == initial_date) & (df['contract_type'] == contract_type), 'contract_code'].values[0]
        q_start = df.loc[(df['date'] == initial_date) & (df['contract_type'] == contract_type), 'q'].values[0]
    print(f'q_start:{q_start},contract_code:{contract_code}')
    # print(f'unique_dates:{unique_dates}')
    for date in tqdm(unique_dates):
        current_date = date
        # end_date = date + pd.Timedelta(days=duration)
        # 获取当前日期的 rem_trad_days 值
        # rem_trad_day = df.loc[(df['date'] == current_date) & (df['contract_code'] == contract_code), 'rem_trad_days'].values[0]
        # print(f'current_date:{current_date}',f'contract_code:{contract_code}',f'rem_trad_day:{rem_trad_day}')
        current_contract_type = df.loc[(df['date'] == current_date) & (df['contract_code'] == contract_code), 'contract_type'].values[0]
        # 判断是否需要换仓
        if current_contract_type == '当月' and rem_trad_day < 3 and current_date < end_date:
            # 获取旧合约的 q_end 值
            q_end = df.loc[(df['date'] == current_date) & (df['contract_code'] == contract_code), 'q'].values[0]
            # 更新 q_diff
            q_diff += q_end - q_start

            # 更新合约，当月合约和其他合约的处理有所不同
            if contract_type == '当月':
                contract_code = df.loc[(df['date'] == current_date) & (df['contract_type'] == '下月'), 'contract_code'].values[0]
                q_start = df.loc[(df['date'] == current_date) & (df['contract_type'] == '下月'), 'q'].values[0]
                rem_trad_day = df.loc[(df['date'] == current_date) & (df['contract_type'] == '下月'), 'rem_trad_days'].values[0]
                print(f'当月合约换仓后q_start:{q_start},contract_code:{contract_code},date:{current_date}')
                continue
            else:
                contract_code = df.loc[(df['date'] == current_date) & (df['contract_type'] == contract_type), 'contract_code'].values[0]
                q_start = df.loc[(df['date'] == current_date) & (df['contract_type'] == contract_type), 'q'].values[0]
                rem_trad_day = df.loc[(df['date'] == current_date) & (df['contract_code'] == contract_code), 'rem_trad_days'].values[0]
                print(f'{contract_type}合约换仓后q_start:{q_start},contract_code:{contract_code}')
                continue
        else:
            rem_trad_day = df.loc[(df['date'] == current_date) & (df['contract_code'] == contract_code), 'rem_trad_days'].values[0]
        print(f'current_date:{current_date}',f'duration:{duration}',f'contract_code:{contract_code}',f'input_contract:{contract_type}',f'current_contract:{current_contract_type}',f'rem_trad_day:{rem_trad_day}')

        # 到达end_date时终止
        if current_date == end_date:
            break

    # 最后的q_end值
    q_end = df.loc[(df['date'] == end_date) & (df['contract_code'] == contract_code), 'q'].values[0]
    q_diff += q_end - q_start

    return q_diff
    
# 计算场内贴水差额，所有的

# df = pd.read_excel(f'股指期货_{und_code}.xlsx')
df = pd.read_csv(f'股指期货_{und_code}_q.csv')
implied_df = pd.read_excel('同余终端-场外隐含贴水率.xlsx', sheet_name=und_code)
df['date'] = pd.to_datetime(df['date'])#.dt.date
implied_df['tradeDate'] = pd.to_datetime(implied_df['tradeDate'])#.dt.date
start_date = implied_df['tradeDate'].min()
end_date = implied_df['tradeDate'].max()
# df['date'] = pd.to_datetime(df['date']).dt.date
# implied_df['tradeDate'] = pd.to_datetime(implied_df['tradeDate']).dt.date
df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].reset_index(drop=True)
df.to_csv(f'中间表筛选过日期_{und_code}_q.csv')
dfs = {}

# 创建一个空的DataFrame用于存储统计数据
statistics_df = pd.DataFrame()
# 生成所有的列名组合
column_combinations = [f'{month}_{contract_type}_{days}天' for month in implied_q_month for contract_type in contract_type_list for days in days_list]
# 初始化columns为统计量的名称，rows为column_combinations
statistics_df = pd.DataFrame(index=['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'], columns=column_combinations)

for contract_type in contract_type_list:
    df1 = df[df['contract_type'] == contract_type].reset_index(drop=True)
    df1.to_csv(f'{contract_type}_{und_code}_q_df1中间表.csv')
    for duration in days_list:
        if f'{und_code}_{duration}天' in dfs:
            output_df = dfs[f'{und_code}_{duration}天']
        else:
            # 动态添加列名：每个month对应一个profit_implied列
            implied_columns = [f'{month}_q_error' for month in implied_q_month]
            output_df = pd.DataFrame(columns=['日期', '标的', '合约类型', '持有天数', '贴水收益'] + implied_columns)

        for idx, (index, row) in tqdm(enumerate(df1.iterrows())):
            if idx + duration < len(df1) and row['rem_trad_days'] >= 2:
                date = row['date']
                start_date = date
                # end_date = df1.iloc[idx + duration]['date']
                q_error_dict = {}
                # S_start = row['xh_close']
                # F_start = row['gzqh_close']
                # basis_start = F_start - S_start
                for month in implied_q_month:
                    implied_q = implied_df.loc[implied_df['tradeDate'] == date, month].values[0]
                    # q_diff = cal_q_diff(start_date,end_date,contract_type,duration)
                    q_diff = cal_q_diff(row,duration)
                    # q_diff = cal_q_diff(start_date,contract_type,duration)
                    q_error = implied_q - q_diff
                    # 将q_error值添加到字典中
                    q_error_dict[f'{month}_q_error'] = q_error
                # 将q_error_dict转换为DataFrame的一行，并与其他列数据合并
                temp_df = pd.DataFrame([[date, und_code, contract_type, duration] + list(q_error_dict.values())],
                                    columns=['日期', '标的', '合约类型', '持有天数'] + implied_columns)
                output_df = pd.concat([output_df, temp_df], ignore_index=True)

            # if idx + duration < len(df1):
            #     expire_date = df1.iloc[idx + duration]['date']
            #     S_end = df1.iloc[idx + duration]['xh_close']
            #     F_end = df1.iloc[idx + duration]['gzqh_close']
            #     basis_end = F_end - S_end
            #     profit = basis_end - basis_start
            #     # 创建一个字典来存储每个month的profit_implied值
            #     profit_error_dict = {}
            #     for month in implied_q_month:
            #         t = get_t[month]
            #         implied_q = implied_df.loc[implied_df['tradeDate'] == date, month].values[0]
            #         profit_implied = cal_implied_profit(S_start, S_end, basis_start, t, implied_q)
            #         profit_error = profit_implied - profit
            #         # 将profit_implied值添加到字典中
            #         profit_error_dict[f'{month}_profit_error'] = profit_error
            #     # 将profit_implied_dict转换为DataFrame的一行，并与其他列数据合并
            #     temp_df = pd.DataFrame([[date, und_code, contract_type, S_start, F_start, days, basis_start, basis_end, profit] + list(profit_error_dict.values())],
            #                            columns=['日期', '标的', '合约类型', '指数', '合约价', '持有天数', '开始时基差', '到期日基差', '基差收益'] + implied_columns)
            #     output_df = pd.concat([output_df, temp_df], ignore_index=True)

        dfs[f'{und_code}_{duration}天'] = output_df

with pd.ExcelWriter(f'{und_code}_q_diff.xlsx') as writer:
    for sheet_name, data in dfs.items():
        data.to_excel(writer, sheet_name=sheet_name, index=False)


# # 遍历 dfs 中的每个 days 对应的 output_df
# for days in days_list:
#     if f'{und_code}_{days}天' in dfs:
#         output_df = dfs[f'{und_code}_{days}天']
#         # 提取周三 周五日期进行计算
#         # output_df['日期'] = pd.to_datetime(output_df['日期'])
#         # output_df = output_df[output_df['日期'].dt.dayofweek.isin([2, 4])]

#         # 获取所有独特的 '合约类型'
#         unique_contract_types = output_df['合约类型'].unique()
#         for contract_type in unique_contract_types:
#             # 筛选出特定合约类型的数据
#             df_contract_type = output_df[output_df['合约类型'] == contract_type]
#             for month in implied_q_month:
#                 # 构建 column name
#                 column_name = f'{month}_{contract_type}_{days}天'
#                 # 检查 month 对应的 profit_error 列是否存在
#                 profit_error_column = f'{month}_profit_error'
#                 if profit_error_column in df_contract_type.columns:
#                     # 提取 profit_error 数据
#                     column_data = df_contract_type[profit_error_column]
#                     # 计算统计数据并存储在 statistics_df 中
#                     statistics_df.loc['count', column_name] = column_data.count()
#                     statistics_df.loc['mean', column_name] = column_data.mean()
#                     statistics_df.loc['std', column_name] = column_data.std()
#                     statistics_df.loc['min', column_name] = column_data.min()
#                     statistics_df.loc['25%', column_name] = column_data.quantile(0.25)
#                     statistics_df.loc['50%', column_name] = column_data.median()
#                     statistics_df.loc['75%', column_name] = column_data.quantile(0.75)
#                     statistics_df.loc['max', column_name] = column_data.max()

# # 显示最终的 statistics_df
# print(statistics_df)
# statistics_df.to_excel(f'{und_code}_stats.xlsx')

# # 生成热力图
# for days in days_list:
# # 过滤出列名中包含 'xx天' 的所有列，并提取 'mean'  / 'std'行的数据
#     plot_values = statistics_df.loc['mean'].filter(like=f'{days}天')

#     # 创建用于热力图的数据框架，行对应 1M, 3M, 6M, 12M，列对应 当月, 下月, 下季, 隔季
#     heatmap_data = pd.DataFrame(index=['1M', '3M', '6M', '12M'], columns=['当月', '下月', '下季', '隔季'])

#     # 填充热力图数据
#     for col in plot_values.index:
#         for period in ['1M', '3M', '6M', '12M']:
#             for timing in ['当月', '下月', '下季', '隔季']:
#                 if f'{period}_{timing}' in col:
#                     heatmap_data.loc[period, timing] = plot_values[col]

#     # 将数据转换为数值类型，以便绘制
#     heatmap_data = heatmap_data.apply(pd.to_numeric)
#     # 调整 heatmap_data 的行和列的顺序
#     heatmap_data = heatmap_data.loc[['1M', '3M', '6M', '12M'], ['隔季', '下季', '下月', '当月']]

#     # 生成热力图
#     plt.figure(figsize=(10, 6))

#     # 使用 'coolwarm' 配色，设置中心点为0，并且数值格式为保留两位小数
#     sns.heatmap(heatmap_data.T, annot=True, cmap="coolwarm", center=0, linewidths=.5, fmt='.2f')
#     plt.title(f'沪深300 预测与真实基差误差均值-{days}天（全日期）')
#     # plt.show()
#     plt.savefig(f'沪深300 预测与真实基差误差均值_{days}天.png')