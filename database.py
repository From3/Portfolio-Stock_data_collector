import psycopg2 as pg2


def commit_and_close(conn, cur):
    cur.close()
    conn.commit()
    conn.close()


class DataBase:
    def __init__(self, user, password, db_name):
        self.user = user
        self.password = password
        self.db_name = db_name

    def connect(self):
        conn = pg2.connect(user=self.user, password=self.password, database=self.db_name)
        cur = conn.cursor()
        return conn, cur

    def add_log(self, ticker, price, price_percentage, volume, volume_percentage, market_cap, market_cap_percentage):
        conn, cur = self.connect()
        cur.execute(
            f"INSERT INTO {ticker}(price, price_percentage, volume, volume_percentage, market_cap, market_cap_percentage, log_time)"
            f"VALUES"
            f"({price}, {price_percentage}, {volume}, {volume_percentage}, "
            f"{market_cap}, {market_cap_percentage}, NOW())")
        commit_and_close(conn, cur)

    def create_table(self, ticker):
        conn, cur = self.connect()
        cur.execute(f"CREATE TABLE {ticker}(log_id SERIAL PRIMARY KEY, "
                    f"price NUMERIC NOT NULL,"
                    f"price_percentage NUMERIC,"
                    f"volume NUMERIC,"
                    f"volume_percentage NUMERIC,"
                    f"market_cap NUMERIC,"
                    f"market_cap_percentage NUMERIC,"
                    f"log_time TIMESTAMP UNIQUE)")
        commit_and_close(conn, cur)

    def one_line_cmd(self, cmd):
        conn, cur = self.connect()
        cur.execute(cmd)
        return conn, cur
