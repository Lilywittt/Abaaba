import sqlite3
from datetime import datetime
import dask
from sqlalchemy import create_engine
import pandas as pd
import os
import csv
import threading


# 数据库类
class DataBase:
    def __init__(self):
        self.db_path = r'./my_sqlite_database.db'

        self.default_table_name = "data_table"  # 默认表名
        # 列名
        self.Ai0 = 'Ai0'
        self.Ai1 = 'Ai1'
        self.Ai2 = 'Ai2'
        self.Ai3 = 'Ai3'
        self.power = 'power'
        self.timestamp = 'timestamp'

        self.conn = None
        self.cursor = None
        self.lock = None

        self.connect()
        self.create_table()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=wal;')   # 开启WAL模式
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    # 如果表不存在，则创建之（若数据库不存在则自动创建）
    def create_table(self, table_name = None):
        if table_name == None:
            table_name = self.default_table_name

        sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name}(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {self.Ai0} REAL DEFAULT NULL,
                    {self.Ai1} REAL DEFAULT NULL,
                    {self.Ai2} REAL DEFAULT NULL,
                    {self.Ai3} REAL DEFAULT NULL,
                    {self.power} REAL DEFAULT NULL,
                    {self.timestamp} TIMESTAMP DEFAULT NULL
                );
            '''

        self.cursor.execute(sql)
        self.conn.commit()

    # 插入数据，表名若未传入则为默认表
    def add_data(self, Ai0_data, Ai1_data, Ai2_data, Ai3_data, power_data, timestamp, table_name = None):
        if table_name == None:
            table_name = self.default_table_name

        with self.lock:
            sql = f'''
                INSERT INTO {table_name} ({self.Ai0}, {self.Ai1}, {self.Ai2}, {self.Ai3}, {self.power}, {self.timestamp})
                VALUES (?, ?, ?, ?, ?, ?);
                '''

            self.cursor.execute(sql, (Ai0_data, Ai1_data, Ai2_data, Ai3_data, power_data, timestamp))
            self.conn.commit()

    # 搜索起始时间和终止时间内的所有数据
    # 返回一个Pandas DataFrame对象
    # 表名若未传入则为默认表
    def get_all_data_by_time_interval(self, start_time, end_time, table_name = None):
        if table_name == None:
            table_name = self.default_table_name

        engine = create_engine(f'sqlite:///{self.db_path}')

        with self.lock:
            # 构建查询SQL
            sql = f'''
                SELECT * FROM {table_name}
                WHERE {self.timestamp} >= '{start_time}' AND {self.timestamp} <= '{end_time}'
                '''

            # Use Pandas to execute query and get a DataFrame
            df = pd.read_sql_query(sql, engine)

        return df

    # 搜索起始时间和终止时间内的特定列数据及其时间戳
    # 返回一个Pandas DataFrame对象
    # 表名若未传入则为默认表
    def get_specified_data_by_time_interval(self, start_time, end_time, column_name, table_name = None):
        if table_name == None:
            table_name = self.default_table_name

        engine = create_engine(f'sqlite:///{self.db_path}')

        with self.lock:
            # 构建查询SQL
            sql = f'''
                SELECT {column_name},{self.timestamp}
                FROM {table_name}
                WHERE {self.timestamp} >= '{start_time}' AND {self.timestamp} <= '{end_time}'
                '''

            # Use Pandas to execute query and get a DataFrame
            df = pd.read_sql_query(sql, engine)

        return df

    # 导出起始时间和终止时间内的所有数据到csv文件，表名若未传入则为默认表，csv文件名为表名
    def export_to_csv(self, start_time, end_time, table_name = None):
        if table_name == None:
            table_name = self.default_table_name

        with self.lock:
            sql = f'''
                SELECT * FROM {table_name}
                WHERE {self.timestamp} >= '{start_time}' AND {self.timestamp} <= '{end_time}'
                '''
            self.cursor.execute(sql)
            results = self.cursor.fetchall()

        # 创建 CSV 文件并打开以进行写入
        with open(f'{table_name}.csv', 'w', newline='') as csvfile:
            # 使用 csv.writer 创建写入器对象
            writer = csv.writer(csvfile)

            # 写入表头
            writer.writerow([i[0] for i in self.cursor.description])

            # 逐行写入查询结果
            writer.writerows(results)

        # 关闭文件和数据库连接
        csvfile.close()

    # 从csv文件导入数据起始时间到终止时间内的所有数据到表中，表名为csv文件名，不存在则创建
    # overwrite表示是否覆盖原表
    def import_from_csv(self, table_name = None, overwrite=False):
        if table_name == None:
            table_name = self.default_table_name

        file_path = f'./{table_name}.csv'
        # 检查 CSV 文件是否存在
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"CSV file '{file_path}' not found.")

        if overwrite:
            # 如果要覆盖原表，则先删除原表
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # 若表不存在则创建
        self.create_table(table_name=table_name)

        with self.lock:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)  # 使用 DictReader 创建字典形式的阅读器对象

                for row in reader:
                    sql = f'''
                            INSERT INTO {table_name} ({self.Ai0}, {self.Ai1}, {self.Ai2}, {self.Ai3}, {self.power}, {self.timestamp})
                            VALUES (?, ?, ?, ?, ?, ?);
                            '''

                    self.cursor.execute(sql, (row['Ai0'], row['Ai1'], row['Ai2'], row['Ai3'], row['power'], row['timestamp']))

            self.conn.commit()
            csvfile.close()

    # 设置默认表名
    def set_default_table_name(self, table_name):
        self.default_table_name = table_name

if __name__ == "__main__":
    db = DataBase()
    db.set_default_table_name("data_table")
    db.add_data(1, 1, 4 ,5, 1, datetime.now())
    df = db.get_all_data_by_time_interval(start_time="2023-07-05 14:18:36.683403", end_time="2024-01-01")
    print(df)
    df = db.get_specified_data_by_time_interval(start_time="2023-07-05 14:18:36.683403", end_time="2024-01-01", column_name="power")
    print(df)
    db.export_to_csv(start_time="2023-07-05 14:18:36.683403", end_time="2024-01-01")
    db.close()