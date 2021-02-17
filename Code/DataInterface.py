import pandas as pd

from pathlib import Path
from Definitions import DATA_FOLDER

class DataInterface():
    def __init__(self):
        self.stocklist = pd.DataFrame()
        self.working_stocklist = pd.DataFrame()


    def update_stocklist(self) -> None:
        self.stocklist = self.read_data()
        self.working_stocklist = self.stocklist.head()


    def get_stocklist(self) -> pd.DataFrame:
        return self.stocklist


    def get_working_stocklist(self) -> pd.DataFrame:
        return self.working_stocklist


    def set_working_stocklist(self, num_stocks: str) -> None:
        if num_stocks.lower() == "all":
            self.working_stocklist = self.stocklist
        else:
            try:
                num_stocks = int(num_stocks)
                self.working_stocklist = self.stocklist.head(num_stocks)
            except Exception as e:
                print("Could not convert {} to an integer. Got {} instead. Will not update stocklist.".format(num_stocks, e))


    def sort_working_stocklist(self, sort_variable: str, sort_direction: bool) -> bool:
        list_was_sorted = False
        if sort_variable in self.working_stocklist.columns:
            print("Sorting stocklist based on '{}'.".format(sort_variable))
            self.working_stocklist = self.working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            list_was_sorted = True

        return list_was_sorted


    def merge_sector_and_industry_columns(self, stock_df: pd.DataFrame) -> pd.DataFrame:
        stock_df["Sector"] = stock_df["Sector_x"].combine_first(stock_df["Sector_y"])
        stock_df = stock_df.drop(["Sector_x", "Sector_y"], axis=1)
        stock_df["Industry"] = stock_df["Industry_x"].combine_first(stock_df["Industry_y"])
        stock_df = stock_df.drop(["Industry_x", "Industry_y"], axis=1)
        return stock_df


    def read_data(self) -> pd.DataFrame:
        top_stocks = pd.DataFrame()
        try:
            print("Reading data...")
            movers = pd.read_pickle(Path.joinpath(DATA_FOLDER, "movers.pkl"))
            company_info = pd.read_pickle(Path.joinpath(DATA_FOLDER, "company_info.pkl"))
            twitter_data_bull_bear = pd.read_pickle(Path.joinpath(DATA_FOLDER, "twitter.pkl"))
            twitter_momentum = pd.read_pickle(Path.joinpath(DATA_FOLDER, "momentum.pkl"))

            # Merge with "how='outer'" to not remove any symbols
            top_stocks = movers.merge(company_info, on='Symbol', how='outer')
            top_stocks = top_stocks.merge(twitter_data_bull_bear, on='Symbol', how='outer')
            top_stocks = top_stocks.merge(twitter_momentum, on='Symbol', how='outer')
            top_stocks.drop(['Market Cap'], axis=1, inplace=True)
            top_stocks = self.merge_sector_and_industry_columns(top_stocks)
            print("Finished reading data...")
        except Exception as e:
            print("Failed to read data, got {}".format(e))

        return top_stocks