import pandas as pd

from DataGatherer import data_gatherer
from tkinter import *

def sort_stocklist(stock_list, sort_key, ascending) -> pd.DataFrame:
    if sort_key in stock_list.columns:
        return stock_list.sort_values(by=[sort_key], ascending=ascending)
    else:
        return stock_list


def build_table(stocklist):
    rows = []
    cols = []
    
    for i, label in enumerate(stocklist.columns):
        entry = Entry(relief=GROOVE)
        entry.grid(row=0, column=i, sticky=NSEW)
        entry.insert(END, "{}".format(label))
        cols.append(entry)
    
    for j, stock in enumerate(stocklist.iterrows()):
        cols = []
        
        # stock[1] contains all data of interest
        for i, col in enumerate(stock[1]):
            entry = Entry(relief=GROOVE)
            # Row = j + 1 to take into account the headlines
            entry.grid(row=j + 1, column=i, sticky=NSEW)
            entry.insert(END, '{}'.format(col))
            cols.append(entry)

        rows.append(cols)


def main():
    stocks = data_gatherer()
    sorted_stocks = sort_stocklist(stocks, "Twit_Bull_score", False)
    sorted_stocks_head = sorted_stocks.head()

    build_table(sorted_stocks_head)
    mainloop()


main()