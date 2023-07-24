# 本文件负责数据可视化功能，即实时显示当前数据和静态显示所搜索时间段内的数据，主要利用matplotlib库

import matplotlib.pyplot as plt #导入matplotlib相关库
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from collections import deque   # 双端队列
import time
import time
from datetime import datetime
import threading

import os
import plotly.graph_objects as go
import sys

import dask.dataframe as dd
import numpy as np
import pandas as pd


# 实时绘图线程
class PlotThread(threading.Thread):
    # 初始化
    def __init__(self, data_queue_0, data_queue_1, data_queue_2, data_queue_3, time_queue, power_queue, condition):
        super().__init__()

        # 初始化坐标轴等参数
        self.fig, self.ax = plt.subplots()
        # 格式化横坐标为时间
        date_format = mdates.DateFormatter('%H:%M:%S')
        self.ax.xaxis.set_major_formatter(date_format)

        self.line = Line2D([], [])
        self.ax.add_line(self.line)

        # 数据缓存队列和时间戳缓存队列
        self.data_queue_0 = data_queue_0
        self.data_queue_1 = data_queue_1
        self.data_queue_2 = data_queue_2
        self.data_queue_3 = data_queue_3
        self.time_queue = time_queue
        self.power_queue = power_queue

        # 使用条件的线程同步
        self.condition = condition

        self.running = True
        print("Successfully initalized PlotThread.")

    def run(self):
        print("Enter PlotThread.run.")
        while self.running:
            with self.condition:
                self.condition.wait()

                # 队列空
                if len(self.time_queue) == 0:
                    print("Queue is empty.")

                # 更新图形并在完成后通知给条件
                self.update_plot()

    def stop(self):
        self.running = False

    # 更新图像，这里直接调用数据缓存队列和时间戳缓存队列
    def update_plot(self):
        print("Start update plot at", datetime.now(), "size=", len(self.time_queue))
        self.line.set_data(self.time_queue, self.data_queue_3)  # 更新数据线条
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.set_xlim(left=self.time_queue[0], right=self.time_queue[-1])    # 更新x轴范围
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        print("Successfully updated plot at", datetime.now())


# 静态绘图
def StaticPlot(csv_file_path):
    df = dd.read_csv(csv_file_path, dtype={'Ai0': 'float64', 'Ai1': 'float64', 'Ai2': 'float64', 'Ai3': 'float64'})

    x_data = df['timestamp']
    y_data0 = df['Ai0']
    y_data1 = df['Ai1']
    y_data2 = df['Ai2']
    y_data3 = df['Ai3']

    x_data = x_data.compute()
    y_data0 = y_data0.compute()
    y_data1 = y_data1.compute()
    y_data2 = y_data2.compute()
    y_data3 = y_data3.compute()

    power_data = y_data3 * (y_data0 + y_data1 + y_data2)

    fig0 = go.Figure(data=go.Scatter(x=x_data, y=y_data0, mode='lines'), layout_title_text='Ai0')
    fig1 = go.Figure(data=go.Scatter(x=x_data, y=y_data1, mode='lines'), layout_title_text='Ai1')
    fig2 = go.Figure(data=go.Scatter(x=x_data, y=y_data2, mode='lines'), layout_title_text='Ai2')
    fig3 = go.Figure(data=go.Scatter(x=x_data, y=y_data3, mode='lines'), layout_title_text='Ai3')

    fig_power = go.Figure(data=go.Scatter(x=x_data, y=power_data, mode='lines'), layout_title_text='Power')

    # html文件输出目标文件夹
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fig0_file = os.path.join(output_folder, 'fig0.html')
    fig1_file = os.path.join(output_folder, 'fig1.html')
    fig2_file = os.path.join(output_folder, 'fig2.html')
    fig3_file = os.path.join(output_folder, 'fig3.html')
    fig_power_file = os.path.join(output_folder, 'fig_power.html')

    fig0.write_html(fig0_file)
    fig1.write_html(fig1_file)
    fig2.write_html(fig2_file)
    fig3.write_html(fig3_file)
    fig_power.write_html(fig_power_file)

    # 返回已保存的html文件
    return fig0_file, fig1_file, fig2_file, fig3_file, fig_power_file