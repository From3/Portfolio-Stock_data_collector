#!/usr/bin/env python3
# -*- coding: utf-8 -*- #

import requests
import yfinance as yf
import psycopg2 as pg2
from datetime import date
import time

# 'subject' variable requires for a stock ticker (case sensitive)
subject = 'TSLA'

# 'db_name' variable requires for your PostgreSQL database name (case sensitive)
db_name = 'financedata'
db_user = str(input('Enter your PostgreSQL database\n\nusername: '))
db_password = str(input('password: '))

# converts ticker's name into PostgreSQL naming format
sql_subject = subject.lower()
for symbol in ["-", "="]:
    sql_subject = sql_subject.replace(symbol, "_")


def data_tracker():
    ticker_data = yf.Ticker(subject).info
    ticker_price = ticker_data['regularMarketPrice']
    ticker_volume = ticker_data['regularMarketVolume']
    ticker_market_cap = ticker_data['marketCap']
    return ticker_volume, ticker_price, ticker_market_cap


def check_none(none_data):
    if none_data is None:
        return 1
    else:
        return none_data


def perc_func(present, early):
    try:
        return round(float(present) / early * 100 - 100, 3)
    except ZeroDivisionError:
        return 0.0


def pg2_connect():
    func_conn = pg2.connect(user=db_user, password=db_password, database=db_name)
    func_cur = func_conn.cursor()
    return func_conn, func_cur


def pg2_cc(cc_conn, cc_cur):
    cc_cur.close()
    cc_conn.commit()
    cc_conn.close()


def pg2_insert(in_price, in_price_perc, in_volume, in_volume_perc, in_mcap, in_mcap_perc):
    insert_conn, insert_cur = pg2_connect()
    insert_cur.execute(f"INSERT INTO {sql_subject}(price, price_perc, volume, volume_perc, mcap, mcap_perc, log_time)"
                       f"VALUES"
                       f"({in_price}, {in_price_perc}, {in_volume}, {in_volume_perc}, "
                       f"{in_mcap}, {in_mcap_perc}, NOW())")
    pg2_cc(insert_conn, insert_cur)


def pg2_oneliner(_):
    one_conn, one_cur = pg2_connect()
    one_cur.execute(_)
    return one_conn, one_cur


def format_output(first_str, second_str):
    first_str, second_str = str(first_str), str(second_str)
    first_whitespaces = 27
    second_whitespaces = 6
    if second_str[0] == "-":
        first_whitespaces -= 1
        second_str += " "
    first_str += " " * (first_whitespaces - len(first_str))
    second_str += " " * (second_whitespaces - len(second_str))
    return first_str + second_str


conn, cur = pg2_connect()
cur.execute("SELECT version();")
record = cur.fetchone()
print("You are connected to - ", record, "\n")
need_new = False
try:
    cur.execute(f"SELECT * FROM {sql_subject};")
    record = cur.fetchone()
except (Exception, pg2.Error) as err:
    if str(type(err)) == "<class 'psycopg2.errors.UndefinedTable'>":
        need_new = True
        cur.close()
        conn.close()

if need_new:
    conn, cur = pg2_connect()
    cur.execute(f"CREATE TABLE {sql_subject}(log_id SERIAL PRIMARY KEY, "
                f"price NUMERIC NOT NULL,"
                f"price_perc NUMERIC,"
                f"volume NUMERIC,"
                f"volume_perc NUMERIC,"
                f"mcap NUMERIC,"
                f"mcap_perc NUMERIC,"
                f"log_time TIMESTAMP UNIQUE)")
    pg2_cc(conn, cur)
    print('Created new')
    need_new = False
else:
    cur.close()
    conn.close()

log_id = 0

price_difference = ''
volume_difference = ''

conn, cur = pg2_oneliner(f"SELECT * FROM {sql_subject} ORDER BY log_id DESC")
print(f'\n{cur.fetchone()}\n')
pg2_cc(conn, cur)

while True:
    # main loop
    try:
        volume, price, mcap = data_tracker()
        if not mcap:
            mcap = 0
    except requests.exceptions.ConnectionError:
        conn_error_counter += 1
        conn_error_time = str(time.strftime('%H:%M:%S'))
        print(f"\n{format_output(date.today(), conn_error_time)}\n"
              f"Connection error ({conn_error_counter} time{'s' if conn_error_counter > 1 else ''} this session)")
        time.sleep(30)
        continue
    if price_difference != price or volume_difference != volume:
        price_difference = price
        price_perc = 0.0

        volume_difference = volume
        volume_perc = 0.0
        mcap_perc = 0.0

        conn, cur = pg2_oneliner(f"SELECT COUNT(log_id) FROM {sql_subject}")
        for _ in cur:
            log_id = _[0]
        pg2_cc(conn, cur)

        if log_id > 0:
            conn, cur = pg2_oneliner(f"SELECT * FROM {sql_subject} ORDER BY log_id DESC")
            early_row = cur.fetchone()
            early_price, early_volume, early_mcap = \
                float(early_row[1]), float(check_none(early_row[3])), float(check_none(early_row[5]))
            pg2_cc(conn, cur)

            if early_price != float(price) or early_volume != float(volume):
                price_perc = perc_func(price, early_price)
                volume_perc = perc_func(volume, early_volume)
                mcap_perc = perc_func(mcap, early_mcap)
                pg2_insert(price, price_perc, volume, volume_perc, mcap, mcap_perc)
        else:
            pg2_insert(price, 0.0, volume, 0.0, mcap, 0.0)

        print(f'{format_output(date.today(), time.strftime("%H:%M:%S"))}\n'
              f'{format_output(price, price_perc)} %\n'
              f'{format_output(volume_difference, volume_perc)} %\n'
              f'{format_output(mcap, mcap_perc) + "%" if mcap > 0 else ""}\n')

    time.sleep(15)
