# Python stock data collector
<img border=0 src="https://img.shields.io/badge/python-3.8.1+-blue.svg?style=flat" alt="Python version"></a>
<a target="new" href="https://github.com/From3/Portfolio-Stock_data_collector"><img border=0 src="https://img.shields.io/github/stars/From3/Portfolio-Stock_data_collector.svg?style=social&label=Star&maxAge=60" alt="Star this repo"></a>

**Stock data collector** is a Python 3 project used for checking stock data (price, trading volume, and market cap) using [yfinance](https://github.com/ranaroussi/yfinance) package and storing collected data to PostgreSQL database using [psycopg2](https://github.com/psycopg/psycopg2) - Python-PostgreSQL Database Adapter.

It creates tables for stocks which weren't previously recorded in a database, runs it's main search every 15 seconds, and stores data (price, trading volume, market cap, and percentage of data difference) to database in case any data (price, trading volume, and market cap) have changed in that time.

## Installation

Install dependencies using `pip` from application's directory:

```
pip install -r requirements.txt
```

or in case multiple Python versions are installed:

```
pip3 install -r requirements.txt
```
