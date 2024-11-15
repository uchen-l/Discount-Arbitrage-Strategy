import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 公司电脑
# os.chdir(r"C:\\Users\\tongyu\Desktop\\贴水套利")
# mbp
os.chdir(r"/Users/uchen/Downloads/贴水套利")
und_code_list = ['000016.SH', '000300.SH', '000905.SH', '000852.SH']

for und_code in und_code_list:
    positions = pd.DataFrame()
    # und_code = '000852.SH' # 指定标的代码 
    # 设置buffer映射 对应不同标的
    buffer_values = {
        '000016.SH': 0.01, # 上证50 1.5%
        '000300.SH': 0.01, # 沪深300 1.5%
        '000905.SH': 0.01, # 中证500 2%
        '000852.SH': 0.01, # 中证1000 3%
    }
    buffer = buffer_values.get(und_code)
    # 读取数据
    df1 = pd.read_excel(f'股指期货_{und_code}.xlsx') # df1:股指期货数据
    df2 = pd.read_excel('同余终端-场外隐含贴水率.xlsx', sheet_name=und_code) # df2:场外隐含贴水率数据
    df3 = pd.read_csv(f'同余终端-股指期货数据{und_code}.csv') # df3:股指期货合约贴水率（场内贴水）
    # 开仓 - 目前买进卖远
    def open_position(positions,date,remaining_days,this_month_hyts,afn_season_hyts,six_month_pred_ts,trade_unit_1m,trade_unit_6m):
        new_position = pd.DataFrame({
        '开仓日': [date],
        '平仓日': [None],
        '剩余日期': [remaining_days],
        '1M合约贴水': [this_month_hyts],
        '隔季合约贴水': [afn_season_hyts],
        '6M场外贴水': [six_month_pred_ts],
        '开仓1m': [trade_unit_1m],
        '开仓6m': [trade_unit_6m],
        '平仓1m': [None],
        '平仓6m': [None],
        'status': ['open'],
        '近月盈亏': [None],
        '远月盈亏': [None],
        '总盈亏': [None]
        })
        # 此处用了concat append在pd后续中不支持
        positions = pd.concat([positions, new_position], ignore_index=True)
        return positions
    # 平仓判定条件
    def close_condition(previous_date, date, positions, remaining_days,trade_unit_1m,trade_unit_6m,afn_season_hyts,six_month_pred_ts):
        if remaining_days == 0:
            close_position_all(date, positions, trade_unit_1m,trade_unit_6m)
        # else:
        #     for _, row in positions.iterrows():
        #         # if afn_season_hyts > row['6M场外贴水']:
        #         # 隔季合约达到预测贴水，平仓（后续再考虑buffer）%
        #         if afn_season_hyts >= six_month_pred_ts:
        #             close_position_single(row['开仓日'],date, positions, trade_unit_1m,trade_unit_6m)
        return

    # 平仓 - 单个合约（目前判定条件是 开仓时候的场外隐含贴水6M大于现在的合约贴水6M）
    def close_position_single(start_date, end_date, positions, trade_unit_1m,trade_unit_6m):
        # 通过开仓日找到对应持仓
        open_position = positions.loc[(positions['开仓日'] == start_date) & (positions['status'] == 'open')]
        # 更新这些行的值
        open_position['平仓日'] = end_date
        open_position['平仓1m'] = trade_unit_1m
        open_position['平仓6m'] = trade_unit_6m
        open_position['status'] = 'close'
        open_position['近月盈亏'] = open_position['平仓1m'] - open_position['开仓1m'] # 近月盈亏是买进，做多
        open_position['远月盈亏'] = open_position['开仓6m'] - open_position['平仓6m'] # 远月盈亏是卖出，做空
        open_position['总盈亏'] = open_position['近月盈亏'] + open_position['远月盈亏']
        # 将更新后的行合并回原 DataFrame
        positions.update(open_position)
        return positions

    # 合约到期全部平仓
    def close_position_all( date, positions, trade_unit_1m,trade_unit_6m):
        # 筛选开仓的行
        open_positions = positions[positions['status'] == 'open']
        # 更新这些行的值
        open_positions['平仓日'] = date
        open_positions['平仓1m'] = trade_unit_1m
        open_positions['平仓6m'] = trade_unit_6m
        open_positions['status'] = 'close'
        open_positions['近月盈亏'] = open_positions['平仓1m'] - open_positions['开仓1m'] # 近月盈亏是买进，做多
        open_positions['远月盈亏'] = open_positions['开仓6m'] - open_positions['平仓6m'] # 远月盈亏是卖出，做空
        open_positions['总盈亏'] = open_positions['近月盈亏'] + open_positions['远月盈亏']
        # 将更新后的行合并回原 DataFrame
        positions.update(open_positions)
        return positions

    # 返回所有在df3['currentMonth'] = NaN的日期，目前是所有当月合约到期的日子（0天），这一天没有合约年化贴水
    # no_ts_list = df3.loc[df3['currentMonth'].isna(), 'tradeDate'].unique() 
    dates = df2['tradeDate'].unique()
    start_date = '2024-03-01'
    end_date = '2024-07-31'
    filtered_dates = df2[(df2['tradeDate'] >= start_date) & (df2['tradeDate'] <= end_date)]['tradeDate'].unique()

    # print(filtered_dates)

    check_df = pd.DataFrame()
    previous_date = None



    # 创建一个空的 DataFrame（类似中间表） 用于存储所有的参数
    all_columns = ['date', 'remaining_days', 'this_month_hyts', 'afn_season_hyts', 'six_month_pred_ts', 'trade_unit_1m', 'trade_unit_6m']
    all_data = pd.DataFrame(columns=all_columns)

    # for date in tqdm(dates):
    for date in tqdm(dates):
        '''
        remaining_days: 当月合约剩余交易日
        this_month_hyts: 本月合约贴水（年化）
        afn_season_hyts: 隔季合约贴水（年化）
        six_month_pred_ts: 隔季场外预测贴水（年化）
        trade_unit_1m: 当天交易最小单位 - 近月
        trade_unit_6m: 当天交易最小单位 - 隔季
        '''
        remaining_days = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '当月'), 'rem_trad_days'].values[0]
        this_month_hyts = df3.loc[df3['tradeDate'] == date, 'currentMonth'].values[0]
        afn_season_hyts = df3.loc[df3['tradeDate'] == date, 'afterNextSeason'].values[0]
        six_month_pred_ts = df2.loc[df2['tradeDate'] == date, '6M'].values[0]
        trade_unit_1m = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '当月'), 'trad_unit'].values[0]
        trade_unit_6m = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '隔季'), 'trad_unit'].values[0]
        
        # 创建一个 DataFrame 存储当前循环的参数
        current_data = pd.DataFrame({
            'date': [date],
            'remaining_days': [remaining_days],
            'this_month_hyts': [this_month_hyts],
            'afn_season_hyts': [afn_season_hyts],
            'six_month_pred_ts': [six_month_pred_ts],
            'trade_unit_1m': [trade_unit_1m],
            'trade_unit_6m': [trade_unit_6m]
        })

        # 将当前循环的参数与之前的参数合并
        all_data = pd.concat([all_data, current_data], ignore_index=True)
        
        # 先检查持仓是否有可以平仓的
        if previous_date is not None and len(positions) > 0:
            close_condition(previous_date, date, positions, remaining_days,trade_unit_1m,trade_unit_6m,afn_season_hyts,six_month_pred_ts)
        
        # # 检查能够开窗的十日内
        # if remaining_days <= 10 and remaining_days >0:
        #     # 6M合约贴水小于预测贴水（预测贴水更大，可以做short）
        #     # 新增buffer判定条件
        #     if afn_season_hyts < six_month_pred_ts - buffer:
        #         # 本月合约是贴水的
        #         # if this_month_hyts > 0:
        #         if trade_unit_6m < trade_unit_1m and this_month_hyts > 0:
        #             positions = open_position(positions,date,remaining_days,this_month_hyts,afn_season_hyts,six_month_pred_ts,trade_unit_1m,trade_unit_6m)
        # 
        positions = open_position(positions,date,remaining_days,this_month_hyts,afn_season_hyts,six_month_pred_ts,trade_unit_1m,trade_unit_6m) 
        previous_date = date

    positions.to_csv(f'positions_整合{und_code}3-7月-benchmark.csv', index=False)

    # 数据可视化：统计总共盈亏笔数，盈亏分布直方图
    lose = positions[positions['总盈亏'] < 0]
    win = positions[positions['总盈亏'] > 0]
    draw = positions[positions['总盈亏'] == 0]

    print(f"标的代码：{und_code}\n"
        f"每笔开仓平均盈亏: {positions['总盈亏'].mean():.2f}\n"
        f"总共盈利笔数: {len(win)}, 占比: {len(win)/len(positions) * 100:.2f}%\n"
        f"总共亏损笔数: {len(lose)}, 占比: {len(lose)/len(positions) * 100:.2f}%\n"
        f"总共平局笔数: {len(draw)}, 占比: {len(draw)/len(positions) * 100:.2f}%")

    # 数据可视化
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.histplot(positions['总盈亏'], bins=50, kde=True, color='skyblue', edgecolor='black')
    plt.xlabel('Profit')
    plt.ylabel('Frequency')
    plt.title(f'{und_code}')

    plt.savefig(f'{und_code}盈亏分布直方图（benchmark）.png', dpi=300)
    # plt.show()

    # all_data.to_csv(f'all_data_{und_code}.csv', index=False)