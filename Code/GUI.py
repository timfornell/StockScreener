import webbrowser
import pandas as pd
import multiprocessing as mp

from DataInterface import DataInterface
from tkinter import *
from tkinter import ttk

from Definitions import GUI_MESSAGE_HEADER, NUMBER_OF_OPTION_FRAMES


class GUI(Frame):
    def __init__(self, root, event, lock, queue):
        print("{} GUI is waiting for data gatherer...".format(GUI_MESSAGE_HEADER))
        event.wait()
        print("{} Data gatherer has finished: {}, starting GUI!".format(GUI_MESSAGE_HEADER, event.is_set()))
        self.data_interface = DataInterface(lock, queue)
        self.id = 0
        self.num_stocks = "10"
        self.root = root
        self.initialize_user_interface()
        print("{} GUI has initialized!".format(GUI_MESSAGE_HEADER))
        self.root.after(100, self.check_for_new_data)


    def intitialize_GUI_layout(self) -> None:
        """ Create and connect all Frames that are used to place stuff in the GUI

        Description
        -----------
        This function creates an empty layout of Frames and connects them to each other so that information in the GUI
        is displayed in a somewhat orderly manner. The layout is currently like this:

        RootFrame (main window):
            OptionsFrame (TOP):
                SortFrame: SortLabel, SortKeyDropDownList, SortingDirectionButton, SubmitSortingOptionsButton
                NumStocksFrame: NumberOfStocksLabel, NumberOfStocksEntry, NumStocksApplyButton
                RefreshFrame: RefreshStocklistButton
            TreeFrame (BOTTOM): VerticalScrollBar, TreeView
        """

        # Define the different GUI widgets
        self.options_frame = Frame(self.root)
        self.options_frame.pack(side=TOP, fill="x")

        self.option_frames = []
        for i in range(NUMBER_OF_OPTION_FRAMES):
            self.option_frames.append(Frame(self.options_frame))
            self.option_frames[i].pack(side=LEFT, padx=10)

        self.sort_frame = Frame(self.option_frames[0])
        self.sort_frame.pack(side=LEFT)

        self.num_stocks_frame = Frame(self.option_frames[1])
        self.num_stocks_frame.pack(side=LEFT)

        self.refresh_frame = Frame(self.option_frames[2])
        self.refresh_frame.pack(side=LEFT)

        for i in range(3, NUMBER_OF_OPTION_FRAMES):
            label = Label(self.option_frames[i], text="Empty optionframe")
            label.pack(side=LEFT)

        self.tree_frame = Frame(self.root)
        self.tree_frame.pack(side=BOTTOM, fill="both", expand=True)


    def initialize_user_interface(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        # Configure the root object
        self.root.title("Stock Screener")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.config(background="white")

        # Configure private variables
        self.sort_options = list(self.data_interface.get_stocklist().columns)
        self.sort_variable_string = "Volume"
        self.sort_direction = False # False is descending and True is ascending

        self.intitialize_GUI_layout()

        # Sort options
        self.sort_label = Label(self.sort_frame, text="Sorting Options:")
        self.sort_label.pack(side=TOP)
        self.sort_var = StringVar(self.sort_frame, value=self.sort_variable_string)
        self.sort_key = OptionMenu(self.sort_frame, self.sort_var, *self.sort_options, command=self.set_sort_variable)
        self.sort_key.pack(side=LEFT)

        self.submit_sorting_option = Button(self.sort_frame, text="Apply sorting", command=self.sort_stocklist)
        self.sorting_direction_button = Button(self.sort_frame,
                                               text="Direction: {}".format(self.get_sort_direction()),
                                               command=self.change_sort_direction)
        self.submit_sorting_option.pack(side=LEFT)
        self.sorting_direction_button.pack(side=LEFT)

        # Number of stocks to display
        self.number_of_stocks_label = Label(self.num_stocks_frame, text="Number of stocks to show:")
        self.number_of_stocks_label.pack(side=TOP)
        self.number_of_stocks_entry = Entry(self.num_stocks_frame)
        self.number_of_stocks_entry.pack(side=LEFT)
        self.submit_number_of_stocks = Button(self.num_stocks_frame, text="Apply", command=self.update_stocklist)
        self.submit_number_of_stocks.pack(side=LEFT)

        # Refresh button
        self.refresh_stocklist_button = Button(self.refresh_frame, text="Refresh stocklist",
                                               state=DISABLED,
                                               command=self.refresh_stocklist_button_callback)
        self.refresh_stocklist_button.pack(side=LEFT)

        # Setup treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=tuple(self.sort_options), selectmode='browse')
        self.vert_scrollbar = Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vert_scrollbar.set)

        self.vert_scrollbar.pack(side=LEFT, fill="y", anchor=W)
        self.tree.pack(side=LEFT, fill="both", expand=True)

        for i, col in enumerate(self.sort_options):
            self.tree.heading("{}".format(i), text=col)
            self.tree.column("{}".format(i), stretch=YES, width=120)

        self.tree["show"] = "headings"
        self.treeview = self.tree

        # Rightclick menu
        self.popup = Menu(self.root, tearoff=0)
        self.popup.add_command(label="Open on Yahoo Finance", command=self.open_yahoo_finance_webpage)
        self.popup.add_command(label="Open on Marketwatch", command=self.open_marketwatch_webpage)
        self.popup.add_command(label="Open on Tradefollowers", command=self.open_tradefollowers_webpage)
        self.popup.add_command(label="Open on Sentdex", command=self.open_sentdex_webpage)
        # Separator can be used to separate several options visually
        # self.popup.add_separator()

        # Bind keys to functions
        self.root.bind("<Return>", self.enter_key_callback)
        self.tree.bind("<Button-3>", self.right_click_tree)
        self.tree.bind("<Button-1>", self.mouse_click)

        self.data_interface.set_working_stocklist(self.num_stocks)
        self.initialize_stocklist()


    def mouse_click(self, event):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            heading = self.tree.heading(column)
            if heading["text"] == self.sort_variable_string:
                self.change_sort_direction(mouse_click=True)

            self.set_sort_variable(heading["text"], mouse_click=True)
            self.sort_stocklist()


    def open_yahoo_finance_webpage(self):
        stock_symbol = self.popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_yahoo_finance_webpage(stock_symbol))


    def open_marketwatch_webpage(self):
        stock_symbol = self.popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_marketwatch_webpage(stock_symbol))


    def open_tradefollowers_webpage(self):
        stock_symbol = self.popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_tradefollowers_webpage(stock_symbol))


    def open_sentdex_webpage(self):
        stock_symbol = self.popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_sentdex_webpage(stock_symbol))


    def right_click_tree(self, event):
        try:
            region = self.tree.identify("region", event.x, event.y)
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.popup.post(event.x_root, event.y_root)
            if region == "cell":
                self.popup.selection = self.tree.set(self.tree.identify_row(event.y))
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.popup.grab_release()


    def enter_key_callback(self, event):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        focused_widget = self.root.focus_get()
        if focused_widget is self.number_of_stocks_entry:
            self.update_stocklist(callback=True)


    def refresh_stocklist_button_callback(self):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        self.data_interface.set_working_stocklist(self.num_stocks)
        self.sort_stocklist()
        self.refresh_stocklist_button["state"] = DISABLED


    def get_sort_direction(self):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        return "Ascending" if self.sort_direction else "Descending"


    def switch_sort_direction(self):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        self.sort_direction = not self.sort_direction
        self.sorting_direction_button.configure(text="Direction: {}".format(self.get_sort_direction()))


    def change_sort_direction(self, mouse_click=False):
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        self.switch_sort_direction()

        if not mouse_click:
            self.sort_stocklist()


    def set_sort_variable(self, selection, mouse_click=False) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        if selection != self.sort_variable_string:
            self.sort_variable_string = selection

            if mouse_click:
                self.sort_var.set(selection)


    def initialize_stocklist(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        print("{} Initialize stocklist to {} stocks.".format(GUI_MESSAGE_HEADER, self.num_stocks))
        self.data_interface.set_working_stocklist(self.num_stocks)
        self.clear_tree()
        self.fill_tree()


    def update_stocklist(self, callback=False) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        if callback:
            new_value = self.number_of_stocks_entry.get()
            old_value = self.num_stocks

            if new_value == old_value:
                return
            else:
                self.num_stocks = new_value
                self.data_interface.set_working_stocklist(self.num_stocks)

            print("{} Limit stocklist to {}.".format(GUI_MESSAGE_HEADER, self.num_stocks))
            self.data_interface.set_working_stocklist(self.num_stocks)
            self.clear_tree()

        self.fill_tree()


    def fill_tree(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        for i, stock in enumerate(self.data_interface.get_working_stocklist().iterrows()):
            self.insert_data(i, stock)


    def sort_stocklist(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        if self.data_interface.sort_working_stocklist(self.sort_variable_string, self.sort_direction):
            self.clear_tree()

            # Draw new sorted stocklist
            self.update_stocklist()


    def insert_data(self, id, stock) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        self.treeview.insert("", "end", iid=id, values=tuple(stock[1]))


    def clear_tree(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        # Clear current tree
        for row in self.treeview.get_children():
            self.treeview.delete(row)


    def check_for_new_data(self) -> None:
        """

        Description
        -----------

        Parameters
        ----------

        Returns
        -------

        """

        # print("{} Checking for new data to load...".format(GUI_MESSAGE_HEADER))
        if self.data_interface.update_stocklist():
            # This should not be forced, a button sould appear if this returns true
            if self.refresh_stocklist_button["state"] == DISABLED:
                self.refresh_stocklist_button["state"] = NORMAL

        self.root.after(500, self.check_for_new_data)
