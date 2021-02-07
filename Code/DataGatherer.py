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
    return company_info


def parse_twitter_data(page) -> Tuple[list, list, list]:
    res = requests.get(page)
    soup = BeautifulSoup(res.text, "html.parser")
    twitter_stocks = soup.find_all('tr')

    twit_stock = []
    sector = []
    twit_score = []

    for stock in twitter_stocks:
        try:
            score = stock.find_all("td", {"class": "datalistcolumn"})
            twit_stock.append(score[0].get_text().replace('$','').strip())
            sector.append(score[2].get_text().replace('\n','').strip())
            twit_score.append(score[4].get_text().replace('\n','').strip())
        except:
            twit_stock.append(np.nan)
            sector.append(np.nan)
            twit_score.append(np.nan)
    
    return (twit_stock, sector, twit_score)


def get_bull_bear_data_from_twitter() -> pd.DataFrame:
    twitter_data = parse_twitter_data("https://www.tradefollowers.com/strength/twitter_strongest.jsp?tf=1m")
            
    twitter_df = pd.DataFrame({'Symbol': twitter_data[0], 'Sector': twitter_data[1], 'Twit_Bull_score': twitter_data[2]})

    # Remove NA values 
    twitter_df.dropna(inplace=True)
    twitter_df.drop_duplicates(subset ="Symbol", keep='first', inplace=True)
    twitter_df.reset_index(drop=True, inplace=True)
    
    return twitter_df


def get_twitter_momentum_score() -> pd.DataFrame:
    twitter_data = parse_twitter_data("https://www.tradefollowers.com/active/twitter_active.jsp?tf=1m")
    
    twitter_momentum = pd.DataFrame({'Symbol': twitter_data[0], 'Sector': twitter_data[1], 'Twit_mom': twitter_data[2]})

    # Remove NA values 
    twitter_momentum.dropna(inplace=True)
    twitter_momentum.drop_duplicates(subset ="Symbol", 
                        keep = 'first', inplace = True)
    twitter_momentum.reset_index(drop=True,inplace=True)
    return twitter_momentum

def data_gatherer():
    # movers = get_most_active_with_positive_change()
    # company_info = get_monthly_sentiment_data_from_sentdex()
    # twitter_data_bull_bear = get_bull_bear_data_from_twitter()
    # twitter_momentum = get_twitter_momentum_score()

    movers = pd.read_pickle("Database/movers.pkl")
    company_info = pd.read_pickle("Database/company_info.pkl")
    twitter_data_bull_bear = pd.read_pickle("Database/twitter.pkl")
    twitter_momentum = pd.read_pickle("Database/momentum.pkl")

    # Merge with "how='outer'" to not remove any symbols
    top_stocks = movers.merge(company_info, on='Symbol', how='outer')
    top_stocks = top_stocks.merge(twitter_data_bull_bear, on='Symbol', how='outer')
    top_stocks = top_stocks.merge(twitter_momentum, on='Symbol', how='outer')
    top_stocks.drop(['Market Cap', 'Avg Vol (3 month)'], axis=1, inplace=True)
    print(top_stocks)

data_gatherer()