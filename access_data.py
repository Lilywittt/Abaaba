# 数据采集卡（AquisitionCard）类的定义和相关线程
import threading
from ctypes import *
import numpy as np             #加载此模块 需要安装numpy包
import ctypes
from PyQt5.QtCore import QThread, pyqtSignal
import time
from collections import deque
from datetime import datetime

import csv


dll = windll.LoadLibrary(r'.\lib\x64\usb-1000.dll')    #加载库文件


# 采集卡相关参数的配置
Ai = np.zeros(4, dtype='float32')    # 初始化一个空矩阵 大小能发放下一次获取的数据
Dev_Index =ctypes.c_int(0)  # 索引 一张卡默认是0
Range = ctypes.c_float(10)  # 设置量程 设置为5 代表-5到5v量程范围
Mode = ctypes.c_char(3) # 接线方式 0为diff 1为NRSE 3为RSE接法
TrigOpen = ctypes.c_char(1) # 软件触发开
TrigClose = ctypes.c_char(0)    # 软件触发关
Num = ctypes.c_ulong(1)   # 执行一次getai获取的点数（每通道）
Channel = ctypes.c_ushort(0x000f)    # 通道数
samplerate = ctypes.c_uint(400) # 采样率，个数据每秒（所有通道加起来）
timeout = ctypes.c_long(400) # 超时时间 以ms为单位


# 采集卡
class AcquisitionCard:
    # 初始化
    def __init__(self, data_queue_0, data_queue_1, data_queue_2, data_queue_3, time_queue, power_queue, condition):
        # 数据缓存队列和时间戳缓存队列
        # 可变对象作为参数传递给函数或方法时，函数内部所获得的是指向原始对象的引用，而不是对象的副本
        # 换句话说，当你改变self.data_queue和self.time_queue时，外部传入的参数也会跟着改变
        self.data_queue_0 = data_queue_0
        self.data_queue_1 = data_queue_1
        self.data_queue_2 = data_queue_2
        self.data_queue_3 = data_queue_3
        self.time_queue = time_queue
        self.power_queue = power_queue
        # 使用条件的线程同步
        self.condition = condition
        self.read_data_thread = ReadDataThread(data_queue_0=self.data_queue_0, data_queue_1=self.data_queue_1, data_queue_2=self.data_queue_2, data_queue_3=self.data_queue_3, time_queue=self.time_queue, power_queue=self.power_queue, condition=self.condition)    # 该类所调用的数据整合线程实例

    # 开始采集，一切正常则返回0，未成功连接至采集卡则返回1，其他错误信息待添加
    def start(self):
        temp = dll.OpenDevice(Dev_Index)   # 打开采集卡
        if temp != 0:
            return 1

        dll.ResetDevice(Dev_Index)  # 初始化采集卡
        dll.SetChanMode(Dev_Index, Mode)  # 设置通道接线方式
        dll.SetUSB1AiRange(Dev_Index, Range)  # 设置量程 USB-1252A有两个量程 正负5和0到10v 设置5为正负5 设置10为0到10
        dll.SetSampleRate(Dev_Index, samplerate)  # 设置采样率 单位为Hz 这里设置的是总采样率 多通道采集最大可设置为200k
        dll.SetChanSel(Dev_Index, Channel)  # 开启通道数 选择需要采集的通道  以二进制表示 这里选择开启0通道  AI功能 一共16通道低位到高位依次是 Ai0到Ai15
        dll.StartRead(Dev_Index)  # 开启读数线程
        dll.SetSoftTrig(Dev_Index, TrigOpen)  # 开启采集卡软件触发 触发采集

        self.read_data_thread.start()   # 开启数据整合线程
        return 0

    # 结束采集
    def stop(self):
        # 先结束数据采集线程
        self.read_data_thread.stop()

        dll.StopRead(Dev_Index)
        dll.SetSoftTrig(Dev_Index, TrigClose)
        # 清空模拟输入缓存，包括软件 FIFO 和硬件 FIFO
        # 注意！！这个b接口贼他喵的耗时，在线程运行中调用的话每次稳定卡10s，非必要别用这玩意
        dll.ClearBufs(Dev_Index)


# 数据采集线程
class ReadDataThread(threading.Thread):
    # 初始化
    def __init__(self, data_queue_0, data_queue_1, data_queue_2, data_queue_3, time_queue, power_queue, condition):
        super().__init__()
        # 数据缓存队列和时间戳缓存队列（的引用）
        self.data_queue_0 = data_queue_0
        self.data_queue_1 = data_queue_1
        self.data_queue_2 = data_queue_2
        self.data_queue_3 = data_queue_3
        self.time_queue = time_queue
        self.power_queue = power_queue
        # 使用条件的线程同步，也是引用
        self.condition = condition
        self.running = True # 运行与否的开关

    def run(self):
        count = 0

        with open('data.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp","Ai0","Ai1","Ai2","Ai3"])

        while self.running:
            time.sleep(0.002)  # 每0.1秒获取一次数据点，这个要独立在condition之外
            print("Start access data at", datetime.now())   # 此类打印均为调试用，正式发布时注释掉或删去

            with self.condition:
                # 读取软件 FIFO 中存储的模拟输入通道采样数据
                temp = dll.GetAiChans(Dev_Index, Num, Channel, Ai.ctypes.data_as(POINTER(c_float)), timeout)
                print("FIFO剩余空间:", temp)
                if temp < 1000:
                    continue

                # #数据存放规则为前100个数据是Ai0通道；接下来100个数据是Ai1通道；接下来100个数据是Ai2通道；
                # 此处会添加进行计算的部分
                datapoint0 = Ai[0] * 25
                datapoint1 = Ai[1] * 25
                datapoint2 = Ai[2] * 25
                datapoint3 = Ai[3] * 90
                power_data = 2250 * Ai[3] * (Ai[0] + Ai[1] + Ai[2])
                t = datetime.now()
                print("Start put one data into the queue.")

                row = [t, datapoint0, datapoint1, datapoint2, datapoint3]
                with open('data.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(row)

                # 若队列满，会自动顶掉开头的
                self.data_queue_0.append(datapoint0)   # 依次获取个数据点
                self.data_queue_1.append(datapoint1)
                self.data_queue_2.append(datapoint2)
                self.data_queue_3.append(datapoint3)
                self.time_queue.append(t)
                self.power_queue.append(power_data)
                print("t = ", t, "datapoint0 = ", datapoint0, "datapoint1 = ", datapoint1, "datapoint2 = ", datapoint2, "datapoint3 = ", datapoint3, "power = ", power_data, "size=", len(self.power_queue))
                print("Successfully put one data into the queue.")

                print("Successfully access data at", datetime.now())
                count += 1
                if count >= 2:
                    self.condition.notify()
                    count = 0

    # 暂停数据采集
    def stop(self):
        self.running = False