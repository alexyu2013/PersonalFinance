import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 设置Streamlit应用标题
st.title('Top 100股票趋势分析(200日移动平均线)')

# 股票代码选择
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB', 'TSLA', 'BRK-B', 'NVDA', 'JPM', 'JNJ',
    'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'NFLX', 'CMCSA', 'PEP',
    'VZ', 'T', 'MRK', 'INTC', 'CSCO', 'ABT', 'NKE', 'PFE', 'XOM', 'TMO',
    'ACN', 'IBM', 'CVX', 'LLY', 'PM', 'WMT', 'MDT', 'COST', 'AMGN', 'TXN',
    'AVGO', 'ADBE', 'IBM', 'QCOM', 'BMY', 'NOW', 'LMT', 'ISRG', 'SBUX', 'CAT',
    'HON', 'NEM', 'SYY', 'AMAT', 'ATVI', 'CHTR', 'GILD', 'ADI', 'SYK', 'FISV',
    'DHR', 'MMC', 'LRCX', 'SPGI', 'C', 'BA', 'ADP', 'CME', 'BIIB', 'MS',
    'ZTS', 'GS', 'NTRS', 'LHX', 'MET', 'SRE', 'KMB', 'ADSK', 'NTES', 'CDW',
    'CB', 'PXD', 'LNT', 'DOW', 'CARR', 'MPC', 'ETR', 'HIG', 'VRTX', 'NDAQ',
    'NKE', 'FIS', 'DTE', 'TSN', 'OXY', 'MDLZ', 'PSA', 'CDK', 'MAR', 'FANG',
    'GOOGL', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NFLX', 'NVDA', 'INTC', 'CSCO']
selected_ticker = st.selectbox('选择股票代码:', tickers)

# 获取历史股票数据 - 延长数据获取时间范围
start_date = '2010-01-01'  # 改为更早的日期以确保足够数据
end_date = datetime.now().date()  # 包含今天的数据

# 下载数据
data = yf.download(selected_ticker, start=start_date, end=end_date)

# 检查数据是否足够
if len(data) < 200:
    st.error(f"错误: 数据不足(只有{len(data)}个交易日)，无法计算200日移动平均线")
    st.stop()

# 计算200日移动平均线
data['SMA_200'] = data['Close'].rolling(window=200, min_periods=1).mean()

# 确定趋势及其周期
sma_trend = []
current_trend = None
uptrend_periods = []  # 上升趋势周期
downtrend_periods = []  # 下降趋势周期

# 识别趋势及其起止日期 - 添加调试信息
for i in range(1, len(data['SMA_200'])):
    if pd.isna(data['SMA_200'].iloc[i]) or pd.isna(data['SMA_200'].iloc[i-1]):
        continue  # 跳过NaN值
    
    if data['SMA_200'].iloc[i] > data['SMA_200'].iloc[i - 1]:
        if current_trend != 'uptrend':
            if current_trend == 'downtrend' and downtrend_periods:
                downtrend_periods[-1][1] = data.index[i - 1]  # 更新最后一个下降趋势的结束日期
            uptrend_periods.append([data.index[i - 1], None])  # 开始新的上升趋势周期
            current_trend = 'uptrend'
    elif data['SMA_200'].iloc[i] < data['SMA_200'].iloc[i - 1]:
        if current_trend != 'downtrend':
            if current_trend == 'uptrend' and uptrend_periods:
                uptrend_periods[-1][1] = data.index[i - 1]  # 更新最后一个上升趋势的结束日期
            downtrend_periods.append([data.index[i - 1], None])  # 开始新的下降趋势周期
            current_trend = 'downtrend'

# 完成最后一个周期
if current_trend == 'uptrend' and uptrend_periods:
    uptrend_periods[-1][1] = data.index[-1]  # 结束最后一个上升趋势周期
elif current_trend == 'downtrend' and downtrend_periods:
    downtrend_periods[-1][1] = data.index[-1]  # 结束最后一个下降趋势周期

# 调试信息
st.write(f"原始上升趋势周期数: {len(uptrend_periods)}")
st.write(f"原始下降趋势周期数: {len(downtrend_periods)}")

# 调整筛选条件 - 降低持续时间要求
min_duration_days = 20  # 从50天改为20天

filtered_uptrend_periods = []
for start, end in uptrend_periods:
    if end is not None and start is not None:
        duration = (end - start).days
        if duration > min_duration_days:  # 使用调整后的条件
            filtered_uptrend_periods.append([start, end])

filtered_downtrend_periods = []
for start, end in downtrend_periods:
    if end is not None and start is not None:
        duration = (end - start).days
        if duration > min_duration_days:  # 使用调整后的条件
            filtered_downtrend_periods.append([start, end])

# 合并相同趋势的连续周期(间隔小于50天)
merged_uptrend_periods = []
if filtered_uptrend_periods:
    start, end = filtered_uptrend_periods[0]
    for i in range(1, len(filtered_uptrend_periods)):
        next_start, _ = filtered_uptrend_periods[i]
        if next_start <= end + pd.Timedelta(days=50):  # 检查下一个开始是否在当前结束的50天内
            end = filtered_uptrend_periods[i][1]  # 延长结束日期
        else:
            merged_uptrend_periods.append([start, end])  # 存储合并后的周期
            start, end = filtered_uptrend_periods[i]  # 开始新周期
    merged_uptrend_periods.append([start, end])  # 添加最后一个周期

# 对下降趋势周期重复合并操作
merged_downtrend_periods = []
if filtered_downtrend_periods:
    start, end = filtered_downtrend_periods[0]
    for i in range(1, len(filtered_downtrend_periods)):
        next_start, _ = filtered_downtrend_periods[i]
        if next_start <= end + pd.Timedelta(days=50):  # 检查下一个开始是否在当前结束的50天内
            end = filtered_downtrend_periods[i][1]  # 延长结束日期
        else:
            merged_downtrend_periods.append([start, end])  # 存储合并后的周期
            start, end = filtered_downtrend_periods[i]  # 开始新周期
    merged_downtrend_periods.append([start, end])  # 添加最后一个周期

# 在Streamlit中显示结果
st.write(f"上升趋势周期数量: {len(merged_uptrend_periods)}")
for start, end in merged_uptrend_periods:
    duration = (end - start).days
    st.write(f"**上升趋势周期:** 开始: {start.strftime('%Y-%m-%d')}, 结束: {end.strftime('%Y-%m-%d')}, 持续时间: {duration} 天")

st.write(f"\n下降趋势周期数量: {len(merged_downtrend_periods)}")
for start, end in merged_downtrend_periods:
    duration = (end - start).days
    st.write(f"**下降趋势周期:** 开始: {start.strftime('%Y-%m-%d')}, 结束: {end.strftime('%Y-%m-%d')}, 持续时间: {duration} 天")

# 创建Plotly图表
fig = go.Figure()

# 添加收盘价轨迹
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'],
    mode='lines',
    name=f'{selected_ticker} 收盘价',
    line=dict(color='blue')
))

# 根据趋势周期为SMA线段着色
for start, end in merged_uptrend_periods:
    mask = (data.index >= start) & (data.index <= end)
    fig.add_trace(go.Scatter(
        x=data.index[mask],
        y=data['SMA_200'][mask],
        mode='lines',
        name='200日移动平均线(上升趋势)',
        line=dict(color='green', width=2)
    ))

for start, end in merged_downtrend_periods:
    mask = (data.index >= start) & (data.index <= end)
    fig.add_trace(go.Scatter(
        x=data.index[mask],
        y=data['SMA_200'][mask],
        mode='lines',
        name='200日移动平均线(下降趋势)',
        line=dict(color='red', width=2)
    ))

# 更新图表布局
fig.update_layout(
    title=f'{selected_ticker} 收盘价与200日移动平均线',
    xaxis_title='日期',
    yaxis_title='价格(美元)',
    legend=dict(x=-0.1, y=1, traceorder='normal', orientation='v'),
    template='plotly',
    hovermode='x unified'
)

# 显示图表
st.plotly_chart(fig)

# 显示原始数据用于调试
with st.expander("显示原始数据(调试用)"):
    st.write(data.tail())
