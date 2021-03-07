from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import multiprocessing as mp

from pathlib import Path
from pandas.core.reshape.merge import merge
import requests

from Definitions import *


class DataCommon():
    def __init__(self, lock: mp.Lock, queue: mp.Queue) -> None:
        self.lock = lock
        self.queue = queue


    def read_data(self) -> pd.DataFrame:
        """ To use this function the user must first acquire the file lock """
        stock_df = pd.DataFrame()
        try:
            print("{} Reading data...".format(DATA_COMMON_MESSAGE_HEADER))
            stock_df = pd.read_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(STOCKLIST_PICKLE_FILE)))
            print("{} Finished reading data...".format(DATA_COMMON_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to read data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))

        return stock_df


    def write_data(self, stock_df: pd.DataFrame) -> None:
        try:
            print("{} Writing data...".format(DATA_COMMON_MESSAGE_HEADER))
            stock_df.to_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(STOCKLIST_PICKLE_FILE)))
            print("{} Finished writing data...".format(DATA_COMMON_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to write data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))


    def update_data(self, updated_stock_df: pd.DataFrame) -> None:
        try:
            stock_df = self.read_data()

            for i, stock in updated_stock_df.iterrows():
                cols_with_values = stock.dropna()
                row_index = stock_df.index[stock_df["Symbol"] == stock["Symbol"]]
                for col, val in cols_with_values.iteritems():
                    if col != "Symbol":
                        stock_df.loc[row_index, col] = val

            self.write_data(stock_df)
        except Exception as e:
            print("{} Failed to update data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))


    def get_stock_name(self, stock_symbol: str) -> str:
        """ Get the name of a stock using its ticker from Yahoo finance

        Description
        -----------
        Parses finance.yahoo using BeautifulSoup to find the name of a stock based on its ticker symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol for the stock of interest

        Returns
        -------
        str
            Name of the stock, if parsing wasn't successful it is set to an empty string

        """
        try:
            yahoo_link = self.get_yahoo_finance_webpage(stock_symbol)
            market_watch_link = self.get_marketwatch_webpage(stock_symbol)

            data = requests.get(yahoo_link)
            soup = BeautifulSoup(data.text, "html.parser")
            stock_name = soup.find("h1", {"class": "D(ib) Fz(18px)"}).text.split("(")[0].rstrip()

            if stock_name and not stock_name.isnumeric():
                return stock_name

            data = requests.get(market_watch_link)
            soup = BeautifulSoup(data.text, "html.parser")
            stock_name = soup.find("h1", {"class": "company__name"}).text

            if stock_name:
                return stock_name

        except:
            print("{} Something went wrong when parsing name for ticker {}.".format(DATA_COMMON_MESSAGE_HEADER, stock_symbol))

        return ""


    def get_yahoo_finance_webpage(self, stock_symbol: str) -> str:
        """ Get the html-link to a stock on Yahoo finance

        Description
        -----------
        Returns the link to the stock on Yahoo finance if it can be found, if not an empty string is returned

        Parameters
        ----------
        stock_symbol : str
            Ticker symbol for the stock

        Returns
        -------
        str
            The link to the webpage
        """
        return "https://finance.yahoo.com/quote/{}".format(stock_symbol)


    def get_marketwatch_webpage(self, stock_symbol: str) -> str:
        """ Get the html-link to a stock on Marketwatch

        Description
        -----------
        Returns the link to the stock on Marketwatch if it can be found, if not an empty string is returned

        Parameters
        ----------
        stock_symbol : str
            Ticker symbol for the stock

        Returns
        -------
        str
            The link to the webpage
        """
        return "https://www.marketwatch.com/investing/stock/{}".format(stock_symbol)


    def get_tradefollowers_webpage(self, stock_symbol: str) -> str:
        """ Get the html-link to a stock on Tradefollower

        Description
        -----------
        Returns the link to the stock on Tradefollower if it can be found, if not an empty string is returned

        Parameters
        ----------
        stock_symbol : str
            Ticker symbol for the stock

        Returns
        -------
        str
            The link to the webpage
        """
        return "https://www.tradefollowers.com/stock/stock_detail.jsp?s=${}".format(stock_symbol)


    def get_sentdex_webpage(self, stock_symbol: str) -> str:
        """ Get the html-link to a stock on Sentdex

        Description
        -----------
        Returns the link to the stock on Sentdex if it can be found, if not an empty string is returned

        Parameters
        ----------
        stock_symbol : str
            Ticker symbol for the stock

        Returns
        -------
        str
            The link to the webpage
        """
        return "http://www.sentdex.com/financial-analysis/?i={}&tf=all".format(stock_symbol)


def cell_contains(series: pd.Series, search_string, *args) -> pd.Series:
    search_string = search_string.lower()
    contains = series.str.contains(search_string, case=False)
    return contains


def cell_does_not_contain(series: pd.Series, search_string, *arg) -> pd.Series:
    search_string = search_string.lower()
    contains = ~series.str.contains(search_string, case=False)
    return contains


def cell_is_nan(series: pd.Series, *args) -> pd.Series:
    is_nan = series.isna()
    return is_nan


def cell_is_not_nan(series: pd.Series, *args) -> pd.Series:
    is_not_nan = ~series.isna()
    return is_not_nan


def cell_string_equals(series: pd.Series, search_string, *args) -> pd.Series:
    search_string = search_string.lower()
    return series.str.lower() == search_string


def cell_string_not_equals(series: pd.Series, search_string, *args) -> pd.Series:
    search_string = search_string.lower()
    return series.str.lower() != search_string


def cell_num_not_equals(series: pd.Series, compare_value, *args) -> pd.Series:
    return series != compare_value


def cell_num_equals(series: pd.Series, compare_value, *args) -> pd.Series:
    return series == compare_value


def cell_greater_than(series: pd.Series, compare_value, *args) -> pd.Series:
    return series > compare_value


def cell_greater_than_or_equal(series: pd.Series, compare_value, *args) -> pd.Series:
    return series >= compare_value


def cell_less_than(series: pd.Series, compare_value, *args) -> pd.Series:
    return series < compare_value


def cell_less_than_or_equal(series: pd.Series, compare_value, *args) -> pd.Series:
    return series <= compare_value
