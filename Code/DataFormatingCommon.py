import pandas as pd
import numpy as np

from pathlib import Path
from pandas.core.reshape.merge import merge

from Definitions import DATA_FOLDER, stocklist_enum


def merge_sector_and_industry_columns(stock_df: pd.DataFrame) -> pd.DataFrame:
    # This is where it goes wrong
    stock_df["Sector"] = stock_df["Sector_x"].combine_first(stock_df["Sector_y"])
    stock_df = stock_df.drop(["Sector_x", "Sector_y"], axis=1)
    stock_df["Industry"] = stock_df["Industry_x"].combine_first(stock_df["Industry_y"])
    stock_df = stock_df.drop(["Industry_x", "Industry_y"], axis=1)
    stock_df.drop(['Market Cap'], axis=1, inplace=True)
    return stock_df


def merge_stocklists(stocklists: dict) -> pd.DataFrame:
    top_stocks = pd.DataFrame()
    for stocklist in stocklist_enum:
        stocks = pd.read_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(stocklist.name)))
        if not top_stocks.empty:
            top_stocks = top_stocks.merge(stocks, on="Symbol", how="outer")
        else:
            top_stocks = stocks

    return merge_sector_and_industry_columns(top_stocks)


def read_data_from_files_to_single_dataframe() -> pd.DataFrame:
    """ To us this function the user should 'lock' the files before calling """
    stocks = {}
    for stocklist in stocklist_enum:
        stocks[stocklist] = pd.read_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(stocklist.name)))

    return merge_stocklists(stocks)


def read_data_from_files_to_dict() -> dict:
    """ To us this function the user should 'lock' the files before calling """
    stocks = {}
    for stocklist in stocklist_enum:
        stocks[stocklist] = pd.read_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(stocklist.name)))

    return stocks


def set_common_dataframe_columns(stocklists: dict) -> dict:
    columns = []
    for stocklist in stocklist_enum:
        columns = list(set(columns + list(stocklists[stocklist].columns)))

    for stocklist in stocklist_enum:
        for column in columns:
            if column not in stocklists[stocklist].columns:
                stocklists[stocklist][column] = np.nan