#!/usr/bin/env python3
# -*- coding: utf-8 -*- #

import psycopg2 as pg2


def commit_and_close(conn, cur, commit=False):
    cur.close()
    if commit:
        conn.commit()
    conn.close()


class DataBase:
    def __init__(self, database_name, username, password, ticker):
        self.database_name = database_name
        self.username = username
        self.password = password
        self.ticker = ticker

    def connect(self):
        conn = pg2.connect(database=self.database_name, user=self.username, password=self.password)
        cur = conn.cursor()
        return conn, cur

    def add_log(self, price, price_percentage, volume, volume_percentage, market_cap, market_cap_percentage):
        conn, cur = self.connect()
        cur.execute(
            f"INSERT INTO {self.ticker}(price, "
            f"price_percentage, "
            f"volume, "
            f"volume_percentage, "
            f"market_cap, "
            f"market_cap_percentage, "
            f"log_time)"
            f"VALUES"
            f"({price}, {price_percentage}, {volume}, {volume_percentage}, "
            f"{market_cap}, {market_cap_percentage}, NOW())")
        commit_and_close(conn, cur, commit=True)

    def create_table(self):
        conn, cur = self.connect()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {self.ticker}(log_id SERIAL PRIMARY KEY, "
                    f"price NUMERIC NOT NULL,"
                    f"price_percentage NUMERIC,"
                    f"volume NUMERIC,"
                    f"volume_percentage NUMERIC,"
                    f"market_cap NUMERIC,"
                    f"market_cap_percentage NUMERIC,"
                    f"log_time TIMESTAMP UNIQUE)")
        commit_and_close(conn, cur, commit=True)

    def execute_cmd(self, cmd: str) -> tuple:
        """
        Execute a SQL command that fetches data, but does not do any changes in a database.
        :param cmd: SQL command that needs to be executed.
        :return: Result of the specified command.
        """
        conn, cur = self.connect()
        cur.execute(cmd)
        result = cur.fetchone()
        commit_and_close(conn, cur)
        return result

    def row_count(self) -> int:
        result = self.execute_cmd(f"SELECT COUNT(*) AS count FROM {self.ticker}")
        return result[0]
