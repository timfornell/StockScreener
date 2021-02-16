# Import relevant packages
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader as web
import requests
import yahoo_fin.stock_info as ya

from alpha_vantage.sectorperformance import SectorPerformances
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
from bs4 import BeautifulSoup
from typing import List, Tuple
from pathlib import Path
from datetime import date


def get_most_active_with_positive_change() -> list:
    # Get the 100 most traded stocks for the trading day
    movers = ya.get_day_most_active()
    movers = movers[movers['% Change'] >= 0]

    return movers


def get_monthly_sentiment_data_from_sentdex() -> pd.DataFrame:
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
                print("No data found, continue with next ticker.")

    company_info = pd.DataFrame(data={'Symbol': ticker_name,
                                      'Sentiment': sentiment,
                                      'Direction': sentiment_trend,
                                      'Mentions':mentions})

    company_info["Mentions"] = company_info["Mentions"].replace(",", "", regex=True)
    company_info["Mentions"] = pd.to_numeric(company_info["Mentions"])

    return company_info


def parse_twitter_data(page) -> Tuple[list, list, list, list]:
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


def get_bull_bear_data_from_twitter() -> pd.DataFrame:
    twitter_data = parse_twitter_data("https://www.tradefollowers.com/strength/twitter_strongest.jsp?tf=1m")

    twitter_df = pd.DataFrame({'Symbol': twitter_data[0], 'Sector': twitter_data[1], 'Industry': twitter_data[2],
                               'Twit_30d_Bull': twitter_data[3]})

    # Remove NA values
    twitter_df.dropna(inplace=True)
    twitter_df.drop_duplicates(subset ="Symbol", keep='first', inplace=True)
    twitter_df.reset_index(drop=True, inplace=True)
    twitter_df["Twit_30d_Bull"] = twitter_df["Twit_30d_Bull"].replace(",", "", regex=True)
    twitter_df["Twit_30d_Bull"] = pd.to_numeric(twitter_df["Twit_30d_Bull"])

    return twitter_df


def get_twitter_momentum_score() -> pd.DataFrame:
    twitter_data = parse_twitter_data("https://www.tradefollowers.com/active/twitter_active.jsp?tf=1m")

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
    return twitter_momentum


def get_twitter_data(symbol, name) -> dict:
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


def get_stock_info(symbol) -> str:
    stock_name = np.nan
    try:
        yahoo_data = requests.get("https://finance.yahoo.com/quote/{}".format(symbol))
        soup = BeautifulSoup(yahoo_data.text, "html.parser")
        stock_name = soup.find("h1", {"class": "D(ib) Fz(18px)"}).text
    except:
        print("Something went wrong when parsin name for ticker {}.".format(symbol))

    return stock_name


def update_stocks_with_missing_data(stock_df) -> pd.DataFrame:
    n = len(stock_df["Symbol"])
    for i, stock in stock_df.iterrows():
        if stock["Name"] is np.nan and stock["Symbol"] != "SP500":
            stock_name = get_stock_info(stock["Symbol"])
            if stock_name is not np.nan:
                stock_df.loc[i, "Name"] = stock_name
            else:
                stock_df = stock_df.drop([i], axis=0)
                continue

        # sentiment_data = get_sentiment_data(stock["Name"])
        twitter_momentum = get_twitter_data(stock["Symbol"], stock_df.loc[i, "Name"])
        stock_df.loc[i, "Twit_1d_Mom"] = twitter_momentum["Twit_1d_Mom"]
        stock_df.loc[i, "Twit_7d_Mom"] = twitter_momentum["Twit_7d_Mom"]
        print("Finished with {} ({}), {}/{}".format(stock_df.loc[i, "Name"], stock["Symbol"], i, n))

    return stock_df


def merge_sector_and_industry_columns(stock_df) -> pd.DataFrame:
    stock_df["Sector"] = stock_df["Sector_x"].combine_first(stock_df["Sector_y"])
    stock_df = stock_df.drop(["Sector_x", "Sector_y"], axis=1)
    stock_df["Industry"] = stock_df["Industry_x"].combine_first(stock_df["Industry_y"])
    stock_df = stock_df.drop(["Industry_x", "Industry_y"], axis=1)
    return stock_df


def data_gatherer() -> pd.DataFrame:
    # The intention of these function calls is to build a list of interesting stocks
    data_folder = Path("Database/{}".format(date.today()))
    if not data_folder.exists():
        Path.mkdir(data_folder)

    if not any(Path(data_folder).iterdir()):
        movers = get_most_active_with_positive_change()
        company_info = get_monthly_sentiment_data_from_sentdex()
        twitter_data_bull_bear = get_bull_bear_data_from_twitter()
        twitter_momentum = get_twitter_momentum_score()
        movers.to_pickle(Path.joinpath(data_folder, "movers.pkl"))
        company_info.to_pickle(Path.joinpath(data_folder, "company_info.pkl"))
        twitter_data_bull_bear.to_pickle(Path.joinpath(data_folder, "twitter.pkl"))
        twitter_momentum.to_pickle(Path.joinpath(data_folder, "momentum.pkl"))
    else:
        movers = pd.read_pickle(Path.joinpath(data_folder, "movers.pkl"))
        company_info = pd.read_pickle(Path.joinpath(data_folder, "company_info.pkl"))
        twitter_data_bull_bear = pd.read_pickle(Path.joinpath(data_folder, "twitter.pkl"))
        twitter_momentum = pd.read_pickle(Path.joinpath(data_folder, "momentum.pkl"))

    # Merge with "how='outer'" to not remove any symbols
    top_stocks = movers.merge(company_info, on='Symbol', how='outer')
    top_stocks = top_stocks.merge(twitter_data_bull_bear, on='Symbol', how='outer')
    top_stocks = top_stocks.merge(twitter_momentum, on='Symbol', how='outer')
    top_stocks.drop(['Market Cap'], axis=1, inplace=True)
    top_stocks = merge_sector_and_industry_columns(top_stocks)

    return top_stocks
