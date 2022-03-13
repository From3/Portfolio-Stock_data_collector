# This code gets data from Yahoo Finance web page and stores it in PostgreSQL database
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
sql_subject_change = ['-', '=']
for symbol in sql_subject_change:
    if symbol in sql_subject:
        subject_split = [_ for _ in sql_subject]
        subject_split[subject_split.index(symbol)] = '_'
        sql_subject = ''.join(subject_split)


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


def int_data(str_num):
    str_num = str(str_num)
    str_num_list = list(str_num)
    commas = str_num_list.count(',')
    for comma in range(commas):
        str_num_list.remove(',')
    try:
        return int(''.join(str_num_list))
    except ValueError:
        return float(''.join(str_num_list))


def int_mcap(str_mc):
    conv_num = 0
    conv_dict = {'M': 6, 'B': 9, 'T': 12}
    conv = str(str_mc)[-1]
    if conv == '0':
        return 0
    if conv in conv_dict:
        conv_num = 10**conv_dict.get(conv)
    list_mcap = [_ for _ in str_mc]
    list_mcap.remove(conv)
    return int(float(''.join(list_mcap)) * conv_num)


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
                       f"({int_data(in_price)}, {in_price_perc}, {in_volume}, {in_volume_perc}, "
                       f"{in_mcap}, {in_mcap_perc}, NOW())")
    pg2_cc(insert_conn, insert_cur)


def pg2_oneliner(_):
    one_conn, one_cur = pg2_connect()
    one_cur.execute(_)
    return one_conn, one_cur


def ws_deco(ws_str, ws_str2):
    # improves result readability in console screen
    num = 18
    num2 = 6
    ws_minus = ''
    ws_list, ws_list2 = [_ for _ in ws_str], [_ for _ in ws_str2]
    if ws_list2[0] == '-':
        num -= 1
        ws_minus = ' '
    res = ''
    ws_list.append(' ' * (num - int(len(ws_list))))
    ws_list += ws_list2
    ws_list.append((' ' * (num2 - int(len(ws_list2)))) + ws_minus)
    for _ in ws_list:
        res += _
    return res


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
    except (AttributeError, requests.exceptions.ChunkedEncodingError) as e:
        time.sleep(15)
        continue
    except requests.exceptions.ConnectionError:
        time.sleep(30)
        continue
    if price_difference != price or volume_difference != volume:
        price_difference = price
        if price != 'Full screen':
            price = int_data(price)
        else:
            continue
        price_perc = 0.0

        volume_difference = volume
        volume = int_data(volume)
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

        print(f'{ws_deco(str(date.today()), str(time.strftime("%H:%M:%S")))}\n'
              f'{ws_deco(str(price), str(price_perc))} %\n'
              f'{ws_deco(str(volume_difference), str(volume_perc))} %\n'
              f'{ws_deco(str(mcap), str(mcap_perc)) + "%" if mcap > 0 else ""}\n')

    time.sleep(15)
