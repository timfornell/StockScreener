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
        self.filtered_working_stocklist = pd.DataFrame()
        self.using_filtered_stocklist = False
        self.active_filters = {}
        self.waiting_for_new_data = False
        self.num_stocks_requested_to_update = 0
        self.next_stock_to_request = 0

        print("{} Update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER))
        self.initialize_stocklist()


    def initialize_stocklist(self) -> None:
        """ Initialize the stocklist and the working_stocklist variables

        """

        with self.lock:
            self.stocklist = self.read_data()
            self.working_stocklist = self.stocklist.head().copy()


    def update_stocklist(self) -> bool:
        """ Interface to either get or request new data

        Description
        -----------
        This function has two purposes:
            - Fill the queue with stocks that has missing values so that the DataGatherer can update them
            - Update the internal variables 'stocklist' and 'working_stocklist' if the DataGatherer has signaled that
              new data is available.

        Returns
        -------
        bool
            A boolean telling the GUI instance if it should update the treeview. Is 'True' if new data has been read.

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
        """ Put stocks that should be updated in the queue

        Description
        -----------
        Loop through the stocklist to find stocks thas has missing data and put up to ENOUGH_STOCKS_UPDATED_TO_SIGNAL
        stocks in the queue for the DataGatherer to update.

        """

        self.waiting_for_new_data = True
        for i, stock in enumerate(self.stocklist[self.next_stock_to_request::].iterrows()):
            null_values = stock[1].isnull()

            if (self.num_stocks_requested_to_update % ENOUGH_STOCKS_UPDATED_TO_SIGNAL == 0 and
                self.num_stocks_requested_to_update > 0):
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
        return self.stocklist


    def get_working_stocklist(self) -> pd.DataFrame:
        """ Get the stocklist currently viewed in the treeview of the GUI

        Description
        -----------
        Either return the working_stocklist or the filtered_working_stocklist depending on if any filters are active or
        not.

        Returns
        -------
        pandas.DataFrame
            A dataframe containing all stocks currently being displayed in the treeview.

        """
        if not self.using_filtered_stocklist:
            return self.working_stocklist
        else:
            return self.filtered_working_stocklist


    def set_working_stocklist(self, num_stocks: str) -> None:
        """ Change the stocks in the working_stocklist

        Description
        -----------
        Change what the working_stocklist contains, can either be the same as the original stocklist or a subset of it
        specified by the input.

        Parameters
        ----------
        num_stocks : str
            A string that is inputted by the user indicating how many stocks to view.

        """

        if num_stocks.lower() == "all":
            self.working_stocklist = self.stocklist.copy()
        else:
            try:
                num_stocks = int(num_stocks)
                self.working_stocklist = self.stocklist.head(num_stocks).copy()
            except Exception as e:
                print("{} Could not convert {} to an integer. Got {} instead. \
                       Will not update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER, num_stocks, e))


    def sort_working_stocklist(self, sort_variable: str, sort_direction: bool) -> bool:
        """ Sort the currently viewed stocklist

        Description
        -----------
        Sort either the working_stocklist or the filtered_working_stocklist based on a sort_variable and a sort_direction.
        The filtered_working_stocklist is sorted if any filters are activated.

        Parameters
        ----------
        sort_variable : str
            Column name to sort on, must exist in the working_stocklist
        sort_direction : bool
            Indicating which direction to sort in, True = Ascending.

        Returns
        -------
        bool
            If the list was sorted successfully True is returned

        """

        list_was_sorted = False
        if sort_variable in self.working_stocklist.columns:
            print("{} Sorting stocklist based on '{}'.".format(DATA_INTERFACE_MESSAGE_HEADER, sort_variable))
            if self.using_filtered_stocklist and sort_variable in self.filtered_working_stocklist.columns:
                self.filtered_working_stocklist = self.filtered_working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            else:
                self.working_stocklist = self.working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            list_was_sorted = True


        return list_was_sorted


    def filter_working_stocklist(self, column: str, filter_func: function, value=None) -> None:
        """ Filter the currently viewed stocklist

        Description
        -----------
        Filter the stocklist currently viewed in the GUI based on a condition.

        Parameters
        ----------
        column : str
            String indicating which column the filter should be applied to
        filter_func : function
            The function that performs the filtering
        value
            Optional argument, can either be a number or string depending on the condition

        """

        self.using_filtered_stocklist = True
        if self.filtered_working_stocklist.empty or column in self.active_filters.keys():
            self.filtered_working_stocklist = self.working_stocklist.copy()

        print("Filter {} using: x {} {}".format(column, filter_func, value))
        self.active_filters[column] = {"func": filter_func, "val": value}
        print(self.active_filters)
        self.filtered_working_stocklist[column] = filter_func(self.filtered_working_stocklist[column], value)
        self.filtered_working_stocklist = self.filtered_working_stocklist.dropna(subset=[column])


