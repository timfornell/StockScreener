from queue import Empty
import pandas as pd
import multiprocessing as mp
import time

from pathlib import Path
from DataCommon import DataCommon

from Definitions import DATA_FOLDER, DATA_GATHERER_MESSAGE_HEADER, DATA_INTERFACE_MESSAGE_HEADER, ENOUGH_STOCKS_UPDATED_TO_SIGNAL, stocklist_enum

class DataInterface(DataCommon):
    def __init__(self, lock: mp.Lock, queue: mp.Queue):
        super().__init__(lock, queue)
        self.stocklist = pd.DataFrame()
        self.working_stocklist = pd.DataFrame()
        self.waiting_for_new_data = False
        self.num_stocks_requested_to_update = 0
        self.next_stock_to_request = 0

        print("{} Update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER))
        self.initialize_stocklist()


    def initialize_stocklist(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        with self.lock:
            self.stocklist = self.read_data()
            self.working_stocklist = self.stocklist.head()


    def update_stocklist(self) -> bool:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        update_treeview = False
        if self.waiting_for_new_data:
            try:
                message = self.queue[DATA_INTERFACE_MESSAGE_HEADER].get_nowait()
                # print("{} Read message '{}'".format(DATA_INTERFACE_MESSAGE_HEADER, message))

                if "NEW_DATA" in message:
                    self.waiting_for_new_data = False
                    print("{} Update stocklist!".format(DATA_INTERFACE_MESSAGE_HEADER))
                    with self.lock:
                        self.stocklist = self.read_data()
                        # The working stocklist is not updated until specifically told so
                        update_treeview = True
            except Empty:
                pass
                # print("{} No message found, sleeping...".format(DATA_INTERFACE_MESSAGE_HEADER))
            except Exception as e:
                pass
                # print("{} Something went wrong, got: {}".format(DATA_INTERFACE_MESSAGE_HEADER, e))
        else:
            self.fill_queue_with_stocks_to_update()

        return update_treeview


    def fill_queue_with_stocks_to_update(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        self.waiting_for_new_data = True
        for i, stock in enumerate(self.stocklist[self.next_stock_to_request::].iterrows()):
            null_values = stock[1].isnull()

            if self.num_stocks_requested_to_update % ENOUGH_STOCKS_UPDATED_TO_SIGNAL == 0 and self.num_stocks_requested_to_update > 0:
                self.next_stock_to_request = i
                self.num_stocks_requested_to_update = 0
                break
            elif null_values.values.any() and stock[1]["Symbol"] and not stock[1]["Updated"]:
                null_columns = [col for col, is_null in null_values.iteritems() if is_null]
                message = "UPDATE {}".format(stock[1]["Symbol"])

                # The number of stocks isn't necesarily evenly dividable by ENOUGH_STOCKS_UPDATED_TO_SIGNAL
                if i == len(self.stocklist.index) - 1:
                    message = message.replace("UPDATE", "FINAL_UPDATE")

                message += ">{}".format(";".join(null_columns))
                print("{} Putting '{}' in queue.".format(DATA_INTERFACE_MESSAGE_HEADER, message))
                self.queue[DATA_GATHERER_MESSAGE_HEADER].put(message)
                self.num_stocks_requested_to_update += 1


    def get_stocklist(self) -> pd.DataFrame:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        return self.stocklist


    def get_working_stocklist(self) -> pd.DataFrame:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        return self.working_stocklist


    def set_working_stocklist(self, num_stocks: str) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        if num_stocks.lower() == "all":
            self.working_stocklist = self.stocklist
        else:
            try:
                num_stocks = int(num_stocks)
                self.working_stocklist = self.stocklist.head(num_stocks)
            except Exception as e:
                print("{} Could not convert {} to an integer. Got {} instead. Will not update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER, num_stocks, e))


    def sort_working_stocklist(self, sort_variable: str, sort_direction: bool) -> bool:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        list_was_sorted = False
        if sort_variable in self.working_stocklist.columns:
            print("{} Sorting stocklist based on '{}'.".format(DATA_INTERFACE_MESSAGE_HEADER, sort_variable))
            self.working_stocklist = self.working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            list_was_sorted = True

        return list_was_sorted
