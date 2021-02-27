import pandas as pd
import multiprocessing as mp

from DataInterface import DataInterface
from tkinter import *
from tkinter import ttk

from Definitions import GUI_MESSAGE_HEADER


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
                SortFrame (LEFT):
                    SortKeyFrame (TOP):
                        SortLabel (LEFT)
                        SortKeyDropDownList (RIGHT)
                    SortKeyButtonsFrame (BOTTOM):
                        SortingDirectionButton (LEFT)
                        SubmitSortingOptionsButton (RIGHT)
                NumStocksFrame (RIGHT):
                    NumStocksEntryFrame (TOP):
                        NumberOfStocksLabel (LEFT)
                        NumberOfStocksEntry (RIGHT)
                    NumStocksApplyButton (BOTTOM)
            TreeFrame (BOTTOM):
                ScrollFrame (LEFT):
                    VerticalScrollBar (LEFT)
                TreeView (RIGHT)
        """

        # Define the different GUI widgets
        self.options_frame = Frame(self.root)
        self.options_frame.pack(side=TOP)

        self.sort_frame = Frame(self.options_frame)
        self.sort_frame.pack(side=LEFT)
        self.sort_key_frame = Frame(self.sort_frame)
        self.sort_key_frame.pack(side=TOP)
        self.sort_key_buttons = Frame(self.sort_frame)
        self.sort_key_buttons.pack(side=BOTTOM)

        self.num_stocks_frame = Frame(self.options_frame)
        self.num_stocks_frame.pack(side=RIGHT, ipadx=30)

        self.num_stocks_entry_frame = Frame(self.num_stocks_frame)
        self.num_stocks_entry_frame.pack(side=TOP)

        self.tree_frame = Frame(self.root)
        self.tree_frame.pack(side=BOTTOM, fill="both", expand=True)

        self.scroll_frame = Frame(self.tree_frame)
        self.scroll_frame.pack(side=LEFT, fill="y")


    def initialize_user_interface(self) -> None:
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
        self.sort_var = StringVar(self.sort_key_frame, value=self.sort_variable_string)
        self.sort_label = Label(self.sort_key_frame, text="Sorting key:")
        self.sort_key = OptionMenu(self.sort_key_frame, self.sort_var, *self.sort_options, command=self.set_sort_variable)
        self.sort_label.pack(side=LEFT)
        self.sort_key.pack(side=RIGHT)

        self.submit_sorting_option = Button(self.sort_key_buttons, text="Apply sorting", command=self.sort_stocklist)
        self.sorting_direction_button = Button(self.sort_key_buttons,
                                                text="Direction: {}".format(self.get_sort_direction()),
                                                                            command=self.change_sort_direction)
        self.submit_sorting_option.pack(side=RIGHT)
        self.sorting_direction_button.pack(side=LEFT)

        # Number of stocks to display
        self.number_of_stocks_label = Label(self.num_stocks_entry_frame, text="Number of stocks to show:")
        self.number_of_stocks_entry = Entry(self.num_stocks_entry_frame)
        self.number_of_stocks_label.pack(side=LEFT)
        self.number_of_stocks_entry.pack(side=RIGHT)

        self.submit_number_of_stocks = Button(self.num_stocks_frame, text="Apply", command=self.update_stocklist)
        self.submit_number_of_stocks.pack(side=BOTTOM)

        # Setup treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=tuple(self.sort_options), selectmode='browse')
        self.tree.bind("<Button-1>", self.mouse_click)
        self.tree.pack(side=RIGHT, fill="both", expand=True)

        for i, col in enumerate(self.sort_options):
            self.tree.heading("{}".format(i), text=col)
            self.tree.column("{}".format(i), stretch=YES, width=120)

        self.tree["show"] = "headings"
        self.treeview = self.tree

        self.vert_scrollbar = Scrollbar(self.scroll_frame, orient="vertical", command=self.tree.yview)
        self.vert_scrollbar.pack(side=LEFT, fill="y", anchor=W)
        self.tree.configure(yscrollcommand=self.vert_scrollbar.set)

        # Bind keys to functions
        self.root.bind("<Return>", self.enter_key_callback)

        self.data_interface.set_working_stocklist(self.num_stocks)
        self.initialize_stocklist()


    def mouse_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            heading = self.tree.heading(column)
            if heading["text"] == self.sort_variable_string:
                self.change_sort_direction(mouse_click=True)

            self.set_sort_variable(heading["text"], mouse_click=True)
            self.sort_stocklist()


    def enter_key_callback(self, event):
        focused_widget = self.root.focus_get()
        if focused_widget is self.number_of_stocks_entry:
            self.update_stocklist()


    def get_sort_direction(self):
        return "Ascending" if self.sort_direction else "Descending"


    def switch_sort_direction(self):
        self.sort_direction = not self.sort_direction
        self.sorting_direction_button.configure(text="Direction: {}".format(self.get_sort_direction()))


    def change_sort_direction(self, mouse_click=False):
        self.switch_sort_direction()

        if not mouse_click:
            self.sort_stocklist()


    def set_sort_variable(self, selection, mouse_click=False) -> None:
        if selection != self.sort_variable_string:
            self.sort_variable_string = selection

            if mouse_click:
                self.sort_var.set(selection)


    def initialize_stocklist(self) -> None:
        print("{} Initialize stocklist to {} stocks.".format(GUI_MESSAGE_HEADER, self.num_stocks))
        self.data_interface.set_working_stocklist(self.num_stocks)
        self.clear_tree()
        self.fill_tree()


    def update_stocklist(self, sorting=False) -> None:
        if not sorting:
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
        for i, stock in enumerate(self.data_interface.get_working_stocklist().iterrows()):
            self.insert_data(i, stock)


    def sort_stocklist(self) -> None:
        if self.data_interface.sort_working_stocklist(self.sort_variable_string, self.sort_direction):
            self.clear_tree()

            # Draw new sorted stocklist
            self.update_stocklist(sorting=True)


    def insert_data(self, id, stock) -> None:
        self.treeview.insert("", "end", iid=id, values=tuple(stock[1]))


    def clear_tree(self) -> None:
        # Clear current tree
        for row in self.treeview.get_children():
            self.treeview.delete(row)


    def check_for_new_data(self) -> None:
        # print("{} Checking for new data to load...".format(GUI_MESSAGE_HEADER))
        if self.data_interface.update_stocklist():
            # This should not be forced, a button sould appear if this returns true
            self.sort_stocklist()

        self.root.after(500, self.check_for_new_data)
