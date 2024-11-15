import os
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import seaborn as sns
import warnings
import math
warnings.filterwarnings('ignore')

# 设置路径
os.chdir(r"C:\\Users\\tongyu\Desktop\\贴水套利")

und_code_list = ['000016.SH', '000300.SH', '000905.SH', '000852.SH']
for und_code in und_code_list:
    positions = pd.DataFrame()
    # 设置buffer映射 对应不同标的
    buffer_values_open = {
        '000016.SH': 0.00,
        '000300.SH': 0.00, 
        '000905.SH': 0.00, 
        '000852.SH': 0.00, 
    }

    buffer_values_close = {
        '000016.SH': 0.006, 
        '000300.SH': 0.006, 
        '000905.SH': 0.006, 
        '000852.SH': 0.006, 
    }

    buffer_open = buffer_values_open.get(und_code)
    buffer_close = buffer_values_close.get(und_code)
    # 读取数据
    df1 = pd.read_excel(f'股指期货_{und_code}.xlsx') # df1:股指期货数据
    df2 = pd.read_excel('同余终端-场外隐含贴水率.xlsx', sheet_name=und_code) # df2:场外隐含贴水率数据
    df3 = pd.read_csv(f'同余终端-股指期货数据{und_code}.csv') # df3:股指期货合约贴水率（场内贴水）
    
    # 开仓 - 目前买进卖远
    def open_position(positions,date,remaining_days,current_spot,this_month_hyts,afn_season_hyts,six_month_pred_ts,trade_unit_1m,trade_unit_6m,pred_basis_open):
        pred_basis_close = current_spot*math.exp(-(six_month_pred_ts + buffer_close) *0.5) - current_spot
        new_position = pd.DataFrame({
        '开仓日': [date],
        '平仓日': [None],
        '剩余日期': [remaining_days],
        '现货价格':[current_spot],
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
        '总盈亏': [None],
        'pred_basis_open': [pred_basis_open],
        'pred_basis_close': [pred_basis_close]
        })
        # 此处用了concat append在pd后续中不支持
        positions = pd.concat([positions, new_position], ignore_index=True)
        return positions
    # 平仓判定条件
    def close_condition(previous_date, date, positions, remaining_days,trade_unit_1m,trade_unit_6m,afn_season_hyts,six_month_pred_ts):
        if remaining_days == 0:
            close_position_all(date, positions, trade_unit_1m,trade_unit_6m)
        else:
            for _, row in positions.iterrows():
                pred_basis_close = row['pred_basis_close']
                # 基差判定
                if diff_afn_season <= pred_basis_close:
                    close_position_single(row['开仓日'],date, positions, trade_unit_1m,trade_unit_6m)
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

    dates = df2['tradeDate'].unique()
    check_df = pd.DataFrame()
    previous_date = None

    # 创建一个空的 DataFrame（类似中间表） 用于存储所有的参数
    all_columns = ['date', 'remaining_days', 'this_month_hyts', 'afn_season_hyts', 'six_month_pred_ts', 'trade_unit_1m', 'trade_unit_6m']
    all_data = pd.DataFrame(columns=all_columns)

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
        current_spot = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '当月'), 'xh_close'].values[0]
        gzqh_close_current_month = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '当月'), 'gzqh_close'].values[0]
        gzqh_close_afn_season = df1.loc[(df1['date'] == date) & (df1['contract_type'] == '隔季'), 'gzqh_close'].values[0] 
        diff_current_month = gzqh_close_current_month - current_spot
        diff_afn_season = gzqh_close_afn_season - current_spot
        # 用 6m场外贴水预测一个F值 这个F值将用于减去现在的S，得到一个基差，用于判断是否开仓，因为是6m预测所以t默认是0.5
        pred_basis_open = current_spot*math.exp(-(six_month_pred_ts - buffer_open) *0.5) - current_spot
        
        # 创建一个 DataFrame 存储当前循环的参数
        current_data = pd.DataFrame({
            'date': [date],
            'remaining_days': [remaining_days],
            'this_month_hyts': [this_month_hyts],
            'afn_season_hyts': [afn_season_hyts],
            'six_month_pred_ts': [six_month_pred_ts],
            'trade_unit_1m': [trade_unit_1m],
            'trade_unit_6m': [trade_unit_6m],
            'gzqh_close_current_month': [gzqh_close_current_month],
            'gzqh_close_afn_season': [gzqh_close_afn_season],
            'current_spot': [current_spot],
            'diff_current_month': [diff_current_month],
            'diff_afn_season': [diff_afn_season],
            'if_open': [remaining_days >0 and diff_afn_season >= pred_basis_open and this_month_hyts > 0],
            'pred_basis_open': [pred_basis_open],
            })

        # 将当前循环的参数与之前的参数合并
        all_data = pd.concat([all_data, current_data], ignore_index=True)
        
        # 先检查持仓是否有可以平仓的
        if previous_date is not None and len(positions) > 0:
            close_condition(previous_date, date, positions, remaining_days,trade_unit_1m,trade_unit_6m,afn_season_hyts,six_month_pred_ts)
        
        # 检查能够开窗的十日内
        # if remaining_days <= 10 and remaining_days >0:
        if remaining_days > 0:
            # 基差判定:
            if diff_afn_season >= pred_basis_open:
                # 本月合约是贴水的
                if this_month_hyts > 0:
                    positions = open_position(positions,date,remaining_days,current_spot,this_month_hyts,afn_season_hyts,six_month_pred_ts,trade_unit_1m,trade_unit_6m,pred_basis_open)
        previous_date = date

    positions.to_csv(f'positions_整合{und_code}.csv', index=False)
    all_data.to_csv(f'all_data_{und_code}.csv', encoding='gbk',index=False)

    # 数据可视化：统计总共盈亏笔数，盈亏分布直方图
    lose = positions[positions['总盈亏'] < 0]
    win = positions[positions['总盈亏'] > 0]
    draw = positions[positions['总盈亏'] == 0]
    num_closed = len(win) + len(lose) + len(draw)
    num_opened = len(positions) - num_closed

    print(f"标的代码：{und_code}\n"
        f"每笔开仓平均盈亏: {positions['总盈亏'].mean():.2f}\n"
        f"已结束合约：{num_closed}\n"
        f"  总共盈利笔数: {len(win)}, 占比: {len(win)/num_closed * 100:.2f}%\n"
        f"  总共亏损笔数: {len(lose)}, 占比: {len(lose)/num_closed * 100:.2f}%\n"
        f"  总共平局笔数: {len(draw)}, 占比: {len(draw)/num_closed * 100:.2f}%\n"
        f"未结束合约：{num_opened}\n")

    # 数据可视化
    positions= positions[positions['status'] != 'open']
    plt.rcParams['font.sans-serif'] = ['STHeiti']
    plt.rcParams['axes.unicode_minus'] = False

    sns.set_theme(style="ticks")
    plt.figure(figsize=(10, 6))
    sns.histplot(positions['总盈亏'], bins=50, kde=True, color='skyblue', edgecolor='black')
    plt.xlabel('Profit')
    plt.ylabel('Frequency')
    plt.title(f'{und_code}')

    plt.savefig(f'{und_code}盈亏分布直方图.png', dpi=300)

    merged_data = pd.merge(all_data[['date', 'current_spot']], 
                        positions[['开仓日', '总盈亏']], 
                        left_on='date', 
                        right_on='开仓日', 
                        how='left')

    # 确保日期格式正确
    merged_data['date'] = pd.to_datetime(merged_data['date']).dt.date

    # 处理 None 或 NaN 值
    merged_data['总盈亏'] = merged_data['总盈亏'].fillna(0)

    # 创建图形对象
    fig, ax1 = plt.subplots(figsize=(35, 10), dpi=300)

    # 绘制折线图（主y轴）
    color = 'tab:blue'
    ax1.set_xlabel('日期', fontdict={'size': 20})
    ax1.set_ylabel('current_spot', color=color, fontdict={'size': 20})
    ax1.plot(merged_data['date'], merged_data['current_spot'], color=color, label='current_spot')
    ax1.tick_params(axis='y', labelcolor=color, labelsize=15)

    # 调整主y轴的范围，确保零点对齐
    # 这里手动设置y轴范围，例如从 0 到 max_y1 * 1.1
    max_y1 = merged_data['current_spot'].max()
    ax1.set_ylim(0, max_y1 * 1.1)

    # 选择显示在x轴上的日期间隔（例如每30天显示一个标签）
    date_labels = merged_data['date'].iloc[::30]
    ax1.set_xticks(date_labels)
    ax1.set_xticklabels(date_labels, rotation=30)

    # 创建第二个y轴，并绘制柱状图
    ax2 = ax1.twinx()  # 创建共享x轴的第二个y轴
    color = 'tab:orange'
    ax2.set_ylabel('总盈亏', color=color, fontdict={'size': 20})

    # 调整第二个y轴的范围，确保零点对齐
    # 确保右侧y轴在零点上对称，例如：从 -max_y2 到 max_y2
    max_y2 = max(abs(merged_data['总盈亏'].min()), abs(merged_data['总盈亏'].max()))
    ax2.set_ylim(-max_y2, max_y2)

    ax2.bar(merged_data['date'], merged_data['总盈亏'], color=color, label='总盈亏', width=3, alpha = 0.5)
    ax2.tick_params(axis='y', labelcolor=color, labelsize=15)

    # 添加辅助线在y=0处
    ax1.axhline(0, color='grey', linewidth=1)
    ax2.axhline(0, color='grey', linewidth=1)


    # 添加图例
    fig.tight_layout()  # 防止标签和图表内容重叠
    plt.title(f'overview_{und_code}', fontdict={'size': 20})

    # 保存图表
    plt.savefig(f'overview_{und_code}_双y轴.png', dpi=300, bbox_inches='tight')