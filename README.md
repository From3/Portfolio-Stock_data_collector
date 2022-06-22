# Python stock data collector
<img border=0 src="https://img.shields.io/badge/python-3.8.1+-blue.svg?style=flat" alt="Python version"></a>
<a target="new" href="https://github.com/From3/Portfolio-Stock_data_collector"><img border=0 src="https://img.shields.io/github/stars/From3/Portfolio-Stock_data_collector.svg?style=social&label=Star&maxAge=60" alt="Star this repo"></a>

**Stock data collector** is a Python 3 project used for checking stock data (price, trading volume, and market cap) using [yfinance](https://github.com/ranaroussi/yfinance) package and storing collected data to PostgreSQL database using [psycopg2](https://github.com/psycopg/psycopg2) - Python-PostgreSQL Database Adapter.

It creates tables for stocks that weren't previously recorded in a database, runs its main search every 15 seconds, and stores data (price, trading volume, market cap, and percentage of data difference) in the database in case of any data (price, trading volume, and market cap) have changed over time.

## Installation

* Setup PostgreSQL if it's not yet setup

[PostgreSQL download page](https://www.postgresql.org/download/)

* Install dependencies using `pip` from application's directory:

```
pip install -r requirements.txt
```

or in case multiple Python versions are installed:

```
pip3 install -r requirements.txt
```

## Usage

To use the stock data collector, you can run it from an IDE or a shell.

Database credentials can be provided in script arguments, env variables, or inputs given when running the script.

***Arguments have a higher priority than env variables in case both are provided.***

---

To run the script use without any additional arguments:
```
python stock_data_collector.py
```

or in case multiple Python versions are installed:
```
python3 stock_data_collector.py
```
---

To run the script with all additional arguments use:
```
python3 stock_data_collector.py "{database name}" "{database username}" "{database password}" "{ticker name}"
```

or in case multiple Python versions are installed:
```
python3 stock_data_collector.py "{database name}" "{database username}" "{database password}" "{ticker name}"
```

***In case only one additional argument is provided, it will be used as a ticker name.***

---

Possible env variables:

* `COLLECTOR_DATABASE_NAME` - name of the database
* `COLLECTOR_DATABASE_USERNAME` - database username
* `COLLECTOR_DATABASE_PASSWORD` - database password
* `COLLECTOR_TICKER_NAME` - name of the stock ticker
