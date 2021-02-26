# Import relevant packages
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader as web
import requests
import yahoo_fin.stock_info as ya
import multiprocessing as mp
import math
import time

from alpha_vantage.sectorperformance import SectorPerformances
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
from bs4 import BeautifulSoup
from typing import List, Tuple
from pathlib import Path
from datetime import date
from queue import Empty

from DataCommon import DataCommon
from Definitions import *


class DataGatherer(DataCommon):
    def __init__(self, lock: mp.Lock, queue: mp.Queue):
        super().__init__(lock, queue)
        self.updated_stocks = 0
        self.updated_stocks_df = pd.DataFrame()


    def gather_data(self) -> None:
        try:
            if not DATA_FOLDER.exists():
                with self.lock:
                    Path.mkdir(DATA_FOLDER)

            if not any(Path(DATA_FOLDER).iterdir()):
                with self.lock:
                    stock_dict = {}
                    for stocklist in stocklist_enum:
                        stock_dict[stocklist] = self.get_stocklist(stocklist)

                    stock_df = self.merge_stocklists(stock_dict)
                    self.write_data(stock_df)

        except Exception as e:
            print("{} Failed to gather data, got {}".format(DATA_GATHERER_MESSAGE_HEADER, e))


    def merge_stocklists(self, stocklists: dict) -> pd.DataFrame:
        stock_df = pd.DataFrame()
        for stocklist in stocklist_enum:
            if not stock_df.empty:
                stock_df = stock_df.merge(stocklists[stocklist], on="Symbol", how="outer")
            else:
                stock_df = stocklists[stocklist]

        # Make the stocklist a bit more nicer
        stock_df["Sector"] = stock_df["Sector_x"].combine_first(stock_df["Sector_y"])
        stock_df = stock_df.drop(["Sector_x", "Sector_y"], axis=1)
        stock_df["Industry"] = stock_df["Industry_x"].combine_first(stock_df["Industry_y"])
        stock_df = stock_df.drop(["Industry_x", "Industry_y"], axis=1)
        stock_df.drop(['Market Cap'], axis=1, inplace=True)
        stock_df["Volume"] = stock_df["Volume"].apply(lambda x: int(x) if not math.isnan(x) else np.nan)
        stock_df["Avg Vol (3 month)"] = stock_df["Avg Vol (3 month)"].apply(lambda x: int(x) if not math.isnan(x) else np.nan)
        # This column is added to indicate if a stock has attempted to be updated at some point
        stock_df["Updated"] = False

        return stock_df


    def update_stocks_with_missing_data(self) -> None:
        try:
            message = self.queue[DATA_GATHERER_MESSAGE_HEADER].get_nowait().split(">")
            command = message[0].split()
            columns_with_missing_data = message[-1].split(";")

            if "UPDATE" in command[0]:
                self.updated_stocks += 1
                stock_symbol = command[STOCK_SYMBOL_POSITION]
                stock_name = self.get_stock_info(stock_symbol)
                stock_data = pd.DataFrame(columns=columns_with_missing_data)
                stock_data.loc[0, "Symbol"] = stock_symbol
                stock_data["Updated"] = True
                stock_data["Name"] = stock_name

                if set(["Twit_1d_Mom", "Twit_7d_Mom"]).intersection(set(columns_with_missing_data)) and stock_name:
                        success, twitter_momentum = self.get_twitter_data(stock_symbol, stock_name)
                        if success:
                            print("{} Found twitter data for {}!".format(DATA_GATHERER_MESSAGE_HEADER, stock_name))
                            stock_data["Twit_1d_Mom"] = twitter_momentum["Twit_1d_Mom"]
                            stock_data["Twit_7d_Mom"] = twitter_momentum["Twit_7d_Mom"]

                print("{} Finished with {} ({})".format(DATA_GATHERER_MESSAGE_HEADER,
                                                        stock_name,
                                                        stock_symbol))

                if not self.updated_stocks_df.empty:
                    # Make sure they have the same columns before concatenating
                    stock_data = stock_data.merge(self.updated_stocks_df, how="left")
                    self.updated_stocks_df = pd.concat([self.updated_stocks_df, stock_data])
                else:
                    self.updated_stocks_df = stock_data

                if self.updated_stocks % ENOUGH_STOCKS_UPDATED_TO_SIGNAL == 0 or "FINAL" in command[0]:
                    with self.lock:
                        self.update_data(self.updated_stocks_df)
                        self.queue[DATA_INTERFACE_MESSAGE_HEADER].put("NEW_DATA")
                        self.updated_stocks_df = pd.DataFrame()

        except Empty:
            # print("{} No message available in queue.".format(DATA_GATHERER_MESSAGE_HEADER))
            pass


    def get_most_active_with_positive_change(self) -> list:
        # Get the 100 most traded stocks for the trading day
        movers = ya.get_day_most_active()
        movers = movers[movers['% Change'] >= 0]

        return movers


    def get_monthly_sentiment_data_from_sentdex(self) -> pd.DataFrame:
        res = requests.get('http://www.sentdex.com/financial-analysis/?tf=30d')
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find_all('tr')
        # Initialize empty lists to store stock symbol, sentiment and mentions
        ticker_name = []
        mentions = []
        sentiment = []
        sentiment_trend = []

        # Use try and except blocks to mitigate missing data
        for ticker in table:
            ticker_info = ticker.find_all('td')

            if ticker_info:
                try:
                    ticker_name.append(ticker_info[0].get_text())
                    mentions.append(ticker_info[2].get_text())
                    sentiment.append(ticker_info[3].get_text())

                    if (ticker_info[4].find('span', {"class":"glyphicon  glyphicon-chevron-up"})):
                        sentiment_trend.append('up')
                    else:
                        sentiment_trend.append('down')
                except:
                    print("{} No data found, continue with next ticker.".format(DATA_GATHERER_MESSAGE_HEADER))

        company_info = pd.DataFrame(data={'Symbol': ticker_name,
                                          'Sentiment': sentiment,
                                          'Direction': sentiment_trend,
                                          'Mentions':mentions})

        company_info["Mentions"] = company_info["Mentions"].replace(",", "", regex=True)
        company_info["Mentions"] = pd.to_numeric(company_info["Mentions"])

        return company_info


    def parse_twitter_data(self, page: str) -> Tuple[list, list, list, list]:
        res = requests.get(page)
        soup = BeautifulSoup(res.text, "html.parser")
        twitter_stocks = soup.find_all('tr')

        twit_stock = []
        sector = []
        industry = []
        twit_score = []

        for stock in twitter_stocks:
            try:
                score = stock.find_all("td", {"class": "datalistcolumn"})
                twit_stock.append(score[0].get_text().replace('$','').strip())
                sector.append(score[2].get_text().replace('\n','').strip())
                industry.append(score[3].get_text().replace('\n','').strip())
                twit_score.append(score[4].get_text().replace('\n','').strip())
            except:
                twit_stock.append(np.nan)
                sector.append(np.nan)
                industry.append(np.nan)
                twit_score.append(np.nan)

        return (twit_stock, sector, industry, twit_score)


    def get_bull_bear_data_from_twitter(self) -> pd.DataFrame:
        twitter_data = self.parse_twitter_data("https://www.tradefollowers.com/strength/twitter_strongest.jsp?tf=1m")

        twitter_df = pd.DataFrame({'Symbol': twitter_data[0], 'Sector': twitter_data[1], 'Industry': twitter_data[2],
                                'Twit_30d_Bull': twitter_data[3]})

        # Remove NA values
        twitter_df.dropna(inplace=True)
        twitter_df.drop_duplicates(subset ="Symbol", keep='first', inplace=True)
        twitter_df.reset_index(drop=True, inplace=True)
        twitter_df["Twit_30d_Bull"] = twitter_df["Twit_30d_Bull"].replace(",", "", regex=True)
        twitter_df["Twit_30d_Bull"] = pd.to_numeric(twitter_df["Twit_30d_Bull"])

        return twitter_df


    def get_twitter_momentum_score(self) -> pd.DataFrame:
        twitter_data = self.parse_twitter_data("https://www.tradefollowers.com/active/twitter_active.jsp?tf=1m")

        twitter_momentum = pd.DataFrame({'Symbol': twitter_data[0], 'Sector': twitter_data[1], 'Industry': twitter_data[2],
                                        'Twit_30d_mom': twitter_data[3]})

        # Remove NA values
        twitter_momentum.dropna(inplace=True)
        twitter_momentum.drop_duplicates(subset ="Symbol",
                            keep = 'first', inplace = True)
        twitter_momentum.reset_index(drop=True,inplace=True)
        twitter_momentum = twitter_momentum.rename(columns={"Twit_30d_mom": "Twit_30d_Mom"})
        twitter_momentum["Twit_30d_Mom"] = twitter_momentum["Twit_30d_Mom"].replace(",", "", regex=True)
        twitter_momentum["Twit_30d_Mom"] = pd.to_numeric(twitter_momentum["Twit_30d_Mom"])

        # These columns are empty here, but will be filled in later, they are added so that the GUI can show them
        twitter_momentum["Twit_1d_Mom"] = np.nan
        twitter_momentum["Twit_7d_Mom"] = np.nan

        return twitter_momentum


    def get_twitter_data(self, symbol: str, name: str) -> Tuple[bool, dict]:
        momentum_data = requests.get("https://www.tradefollowers.com/stock/stock_list.jsp?s={}".format(name))
        soup = BeautifulSoup(momentum_data.text, "html.parser")
        table = soup.find_all('tr')
        data = {"Twit_1d_Mom": np.nan, "Twit_7d_Mom": np.nan}
        success = False

        for stock in table:
            stock_info = stock.find_all("td", {"class": "datalistcolumn"})
            if stock_info:
                page_symbol = stock_info[0].get_text().strip().replace("$", "")
                if symbol == page_symbol:
                    daily_momentum = float(stock_info[4].get_text().strip())
                    seven_day_momentum = float(stock_info[5].get_text().strip())
                    data["Twit_1d_Mom"] = daily_momentum
                    data["Twit_7d_Mom"] = seven_day_momentum
                    success = True
                    break

        return success, data


    def get_stock_info(self, symbol: str) -> str:
        stock_name = ""
        try:
            yahoo_data = requests.get("https://finance.yahoo.com/quote/{}".format(symbol))
            soup = BeautifulSoup(yahoo_data.text, "html.parser")
            stock_name = soup.find("h1", {"class": "D(ib) Fz(18px)"}).text.split("(")[0].rstrip()
        except:
            print("{} Something went wrong when parsing name for ticker {}.".format(DATA_GATHERER_MESSAGE_HEADER, symbol))

        return stock_name


    def get_stocklist(self, stocklist: stocklist_enum) -> pd.DataFrame:
        stocks_df = pd.DataFrame()

        if stocklist == stocklist_enum.Movers:
            stocks_df = self.get_most_active_with_positive_change()
        elif stocklist == stocklist_enum.CompanyInfo:
            stocks_df = self.get_monthly_sentiment_data_from_sentdex()
        elif stocklist == stocklist_enum.TwitterBullBear:
            stocks_df = self.get_bull_bear_data_from_twitter()
        elif stocklist == stocklist_enum.TwitterMomentum:
            stocks_df = self.get_twitter_momentum_score()

        return stocks_df

