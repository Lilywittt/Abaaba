# 对数据进行初步滤波处理
import dask.dataframe as dd
import numpy
import pandas


# 修剪平均滤波
def trim_mean_filter(csv_src_path, csv_dest_path):
    # 将待降噪的csv文件读取为dask.dataframe框架，这样比pandas.dataframe快多了
    df = dd.read_csv(csv_src_path, dtype={'Ai0': 'float64', 'Ai1': 'float64', 'Ai2': 'float64', 'Ai3': 'float64'})

    x_data = df['timestamp']

    df_rolled_0 = df['Ai0'].rolling(window=30)
    y_data0_filtered = df_rolled_0.apply(lambda x: trim_mean_filter_tool(x,threshold=75), raw=True)

    df_rolled_1 = df['Ai1'].rolling(window=30)
    y_data1_filtered = df_rolled_1.apply(lambda x: trim_mean_filter_tool(x,threshold=75), raw=True)

    df_rolled_2 = df['Ai2'].rolling(window=30)
    y_data2_filtered = df_rolled_2.apply(lambda x: trim_mean_filter_tool(x,threshold=75), raw=True)

    df_rolled_3 = df['Ai3'].rolling(window=60)
    y_data3_filtered = df_rolled_3.apply(lambda x: trim_mean_filter_tool(x,threshold=300), raw=True)

    # 导出的时候用pandas就行了，dask是为了计算更快的
    df_filtered = pandas.DataFrame({
        'timestamp':x_data,
        'Ai0':y_data0_filtered,
        'Ai1':y_data1_filtered,
        'Ai2':y_data2_filtered,
        'Ai3':y_data3_filtered
    })

    df_filtered.to_csv(csv_dest_path, index=False)


# 修剪平均滤波的工具方法
# data_window 滑动窗口
# threshold 高于该阈值的数据全部忽略
def trim_mean_filter_tool(data_window, threshold):
    dt = data_window[data_window <= threshold]
    dt = numpy.sort(dt)
    if len(dt) > 2:
        dt = dt[1:-1]
    if len(dt) > 2:
        dt = dt[1:-1]
    if len(dt) > 2:
        dt = dt[1:-1]
    return dt.mean()