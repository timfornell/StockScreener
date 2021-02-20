from queue import Empty
import pandas as pd
import multiprocessing as mp
import time

from pathlib import Path
from DataCommon import DataCommon

from Definitions import DATA_FOLDER, DATA_INTERFACE_MESSAGE_HEADER, stocklist_enum

class DataInterface(DataCommon):
    def __init__(self, lock: mp.Lock, queue: mp.Queue):
        super().__init__(lock, queue)
        self.stocklist = pd.DataFrame()
        self.working_stocklist = pd.DataFrame()
        self.waiting_for_new_data = False

        print("{} Update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER))
        self.initialize_stocklist()


    def initialize_stocklist(self) -> None:
        with self.lock:
            self.stocklist = self.read_data()
            self.working_stocklist = self.stocklist.head()


    def update_stocklist(self) -> None:
        if self.waiting_for_new_data:
            try:
                # if not initialize:
                message = self.queue.get()
                print("{} Read message '{}'".format(DATA_INTERFACE_MESSAGE_HEADER, message))

                if DATA_INTERFACE_MESSAGE_HEADER in message:
                    print("{} Update stocklist!".format(DATA_INTERFACE_MESSAGE_HEADER))
                    with self.lock:
                        self.stocklist = self.read_data()
                        self.working_stocklist = self.stocklist.head()
            except Empty:
                print("{} No message found, sleeping...".format(DATA_INTERFACE_MESSAGE_HEADER))
                time.sleep(2)
            except Exception as e:
                print("{} Something went wrong, got: {}".format(DATA_INTERFACE_MESSAGE_HEADER, e))
        else:
            self.fill_queue_with_stocks_to_update()


    def fill_queue_with_stocks_to_update(self) -> None:
        pass


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
                print("{} Could not convert {} to an integer. Got {} instead. Will not update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER, num_stocks, e))


    def sort_working_stocklist(self, sort_variable: str, sort_direction: bool) -> bool:
        list_was_sorted = False
        if sort_variable in self.working_stocklist.columns:
            print("{} Sorting stocklist based on '{}'.".format(DATA_INTERFACE_MESSAGE_HEADER, sort_variable))
            self.working_stocklist = self.working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            list_was_sorted = True

        return list_was_sorted
