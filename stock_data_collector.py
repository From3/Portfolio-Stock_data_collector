#!/usr/bin/env python3
# -*- coding: utf-8 -*- #

import requests
import yfinance as yf
from sys import argv
from os import environ
from getpass import getpass
from typing import Union
from database import DataBase
import time
import logging

# connection to the database with script call arguments, env variables or input
argv_length = len(argv)
if argv_length > 4:
    DATABASE_NAME = argv[1]
    DATABASE_USERNAME = argv[2]
    DATABASE_PASSWORD = argv[3]
    TICKER_NAME = argv[4]
else:
    DATABASE_NAME = environ.get("COLLECTOR_DATABASE_NAME", input("Enter the database name: "))
    DATABASE_USERNAME = environ.get("COLLECTOR_DATABASE_USERNAME", input("Enter the database username: "))
    DATABASE_PASSWORD = environ.get("COLLECTOR_DATABASE_PASSWORD", getpass("Enter the database password: "))
    if argv_length == 2:
        TICKER_NAME = argv[1]
    else:
        TICKER_NAME = environ.get("COLLECTOR_TICKER_NAME", input("Enter the ticker: "))

SQL_TABLE_NAME = TICKER_NAME.lower()
# check and correct compatibility of SQL_TABLE_NAME
for symbol in ["-", "="]:
    SQL_TABLE_NAME = SQL_TABLE_NAME.replace(symbol, "_")
SQL_TABLE_NAME = SQL_TABLE_NAME.replace("^", "")

logging.basicConfig(level=logging.INFO, format=f"[%(levelname)s] %(asctime)s: %(message)s")


def collect_data() -> tuple:
    """
    :return: A tuple that includes TICKER_NAME stock price, trading volume,
    and market cap which was collected with yfinance.
    """
    ticker_data = yf.Ticker(TICKER_NAME).info
    ticker_price = ticker_data["regularMarketPrice"]
    if not ticker_price:
        logging.error("Ticker \"{}\" not found\nPress \"Enter\" to exit".format(TICKER_NAME))
        input()
        exit()
    ticker_volume = ticker_data["regularMarketVolume"]
    ticker_market_cap = ticker_data["marketCap"]
    if not ticker_market_cap:
        ticker_market_cap = 0
    return ticker_volume, ticker_price, ticker_market_cap


def get_percentage(current: Union[int, float], previous: float) -> float:
    try:
        return round(current / previous * 100 - 100, 3)
    except ZeroDivisionError:
        return 0.0


def format_output(first_str: Union[str, int, float], second_str: Union[str, float]) -> str:
    """
    :return: A prettified version of first_str and second_str sum
    """
    first_str, second_str = str(first_str), str(second_str)
    first_whitespaces = 21
    second_whitespaces = 6
    if second_str[0] == "-":
        first_whitespaces -= 1
        second_str += " "
    first_str += " " * (first_whitespaces - len(first_str))
    second_str += " " * (second_whitespaces - len(second_str))
    return first_str + second_str


DB = DataBase(DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, SQL_TABLE_NAME)

db_version = DB.execute_cmd("SELECT version();")
logging.info("Connected to {}\n".format(*db_version))

# create a new table for the provided ticker if it does not exist in the database
DB.create_table()

if __name__ == "__main__":
    # main loop
    while True:
        if DB.row_count():
            """
            Get last row from database to evaluate difference between last row and new data
            if data collection was done previously with the same ticker.
            """
            previous_row = DB.execute_cmd(f"SELECT * FROM {SQL_TABLE_NAME} "
                                          f"ORDER BY log_id DESC "
                                          f"LIMIT 1")
            previous_price = float(previous_row[1])
            previous_volume = float(previous_row[3])
            previous_market_cap = float(previous_row[5])
        else:
            previous_price = previous_volume = previous_market_cap = 0.0

        try:
            volume, price, market_cap = collect_data()
        except requests.exceptions.ConnectionError:
            logging.error("Connection error\n"
                          "Check internet connection\n")
            time.sleep(30)
            continue
        except KeyError:
            # yfinance data collection unsuccessful
            logging.warning("\"{}\" data collection failed\n"
                            "Retrying\n".format(TICKER_NAME))
            time.sleep(15)
            continue

        if previous_price != price or previous_volume != volume:
            # add data to the database and output it if there were changes found in price or trading volume
            price_percentage = get_percentage(price, previous_price)
            volume_percentage = get_percentage(volume, previous_volume)
            market_cap_percentage = get_percentage(market_cap, previous_market_cap)

            DB.add_log(price, price_percentage, volume, volume_percentage, market_cap, market_cap_percentage)

            logging.info("\"{TICKER_NAME}\" data collected\n"
                         "{price_output} %\n"
                         "{volume_output} %\n"
                         "{market_cap_output}\n"
                         .format(TICKER_NAME=TICKER_NAME,
                                 price_output="Price       $" + format_output(price, price_percentage),
                                 volume_output="Volume      $" + format_output(volume, volume_percentage),
                                 market_cap_output="Market Cap  $" + format_output(market_cap, market_cap_percentage) +
                                                   " %" if market_cap > 0 else '')
                         )
        # uncomment the next two rows to see logs in case of no changes found in price or trading volume
        # else:
        #     logging.info("No changes found in \"{}\"\n".format(TICKER_NAME))

        time.sleep(15)
