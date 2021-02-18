# Import relevant packages
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader as web
import requests
import yahoo_fin.stock_info as ya
import multiprocessing as mp

from alpha_vantage.sectorperformance import SectorPerformances
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
from bs4 import BeautifulSoup
from typing import List, Tuple
from pathlib import Path
from datetime import date
from Definitions import DATA_FOLDER, DATA_GATHERER_MESSAGE_HEADER, STOCKLISTS



class DataGatherer():
    def __init__(self, lock: mp.Lock):
        self.lock = lock
        self.stocklists = {key: pd.DataFrame for key in STOCKLISTS}
        self.lists_to_update = list(STOCKLISTS)


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
        self.stocklists[stocklist]["Twit_1d_Mom"] = np.nan
        self.stocklists[stocklist]["Twit_7d_Mom"] = np.nan

        return twitter_momentum


    def get_twitter_data(self, symbol: str, name: str) -> dict:
        momentum_data = requests.get("https://www.tradefollowers.com/stock/stock_list.jsp?s={}".format(name))
        soup = BeautifulSoup(momentum_data.text, "html.parser")
        table = soup.find_all('tr')
        data = {"Twit_1d_Mom": np.nan, "Twit_7d_Mom": np.nan}

        for stock in table:
            stock_info = stock.find_all("td", {"class": "datalistcolumn"})
            if stock_info:
                page_symbol = stock_info[0].get_text().strip().replace("$", "")
                if symbol == page_symbol:
                    daily_momentum = float(stock_info[4].get_text().strip())
                    seven_day_momentum = float(stock_info[5].get_text().strip())
                    data["Twit_1d_Mom"] = daily_momentum
                    data["Twit_7d_Mom"] = seven_day_momentum
                    break

        return data


    def get_stock_info(self, symbol: str) -> str:
        stock_name = np.nan
        try:
            yahoo_data = requests.get("https://finance.yahoo.com/quote/{}".format(symbol))
            soup = BeautifulSoup(yahoo_data.text, "html.parser")
            stock_name = soup.find("h1", {"class": "D(ib) Fz(18px)"}).text
        except:
            print("{} Something went wrong when parsin name for ticker {}.".format(DATA_GATHERER_MESSAGE_HEADER, symbol))

        return stock_name


    def update_stocks_with_missing_data(self) -> None:
        stock_df = []
        for i, stock in stock_df.iterrows():
            if stock["Name"] is np.nan and stock["Symbol"] != "SP500":
                stock_name = self.get_stock_info(stock["Symbol"])
                if stock_name is not np.nan:
                    stock_df.loc[i, "Name"] = stock_name
                else:
                    stock_df = stock_df.drop([i], axis=0)
                    continue

            # sentiment_data = get_sentiment_data(stock["Name"])
            twitter_momentum = self.get_twitter_data(stock["Symbol"], stock_df.loc[i, "Name"])
            stock_df.loc[i, "Twit_1d_Mom"] = twitter_momentum["Twit_1d_Mom"]
            stock_df.loc[i, "Twit_7d_Mom"] = twitter_momentum["Twit_7d_Mom"]
            print("{} Finished with {} ({}), {}/{}".format(DATA_GATHERER_MESSAGE_HEADER,
                                                           stock_df.loc[i, "Name"],
                                                           stock["Symbol"], i))

        return stock_df


    def get_stocklist(self, stocklist: STOCKLISTS) -> None:
        if stocklist == STOCKLISTS.Movers:
            self.stocklists[stocklist] = self.get_most_active_with_positive_change()
        elif stocklist == STOCKLISTS.CompanyInfo:
            self.stocklists[stocklist] = self.get_monthly_sentiment_data_from_sentdex()
        elif stocklist == STOCKLISTS.TwitterBullBear:
            self.stocklists[stocklist] = self.get_bull_bear_data_from_twitter()
        elif stocklist == STOCKLISTS.TwitterMomentum:
            self.stocklists[stocklist] = self.get_twitter_momentum_score()


    def gather_data(self) -> None:
        try:
            if not DATA_FOLDER.exists():
                with self.lock:
                    Path.mkdir(DATA_FOLDER)

            if not any(Path(DATA_FOLDER).iterdir()):
                with self.lock:
                    for stocklist in STOCKLISTS:
                        self.get_stocklist(stocklist)
                        self.stocklists[stocklist].to_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(stocklist.name)))
            else:
                self.read_data()
        except Exception as e:
            print("{} Failed to gather data, got {}".format(DATA_GATHERER_MESSAGE_HEADER, e))


    def read_data(self) -> None:
        try:
            with self.lock:
                print("{} Reading data...".format(DATA_GATHERER_MESSAGE_HEADER))
                self.movers = pd.read_pickle(Path.joinpath(DATA_FOLDER, "movers.pkl"))
                self.company_info = pd.read_pickle(Path.joinpath(DATA_FOLDER, "company_info.pkl"))
                self.twitter_data_bull_bear = pd.read_pickle(Path.joinpath(DATA_FOLDER, "twitter.pkl"))
                self.twitter_momentum = pd.read_pickle(Path.joinpath(DATA_FOLDER, "momentum.pkl"))
                print("{} Finished reading data".format(DATA_GATHERER_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to read data, got {}".format(DATA_GATHERER_MESSAGE_HEADER, e))
