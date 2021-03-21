import multiprocessing as mp
import pandas as pd
import tkinter
import webbrowser

from tkinter import *
from tkinter import simpledialog
from tkinter import ttk

from Plotter import *
from DataCommon import *
from DataInterface import DataInterface
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

        self.filter_frame = Frame(self.option_frames[3])
        self.filter_frame.pack(side=LEFT)

        self.plot_frame = Frame(self.option_frames[4])
        self.plot_frame.pack(side=LEFT)

        for i in range(5, NUMBER_OF_OPTION_FRAMES):
            label = Label(self.option_frames[i], text="Empty optionframe")
            label.pack(side=LEFT)

        self.tree_frame = Frame(self.root)
        self.tree_frame.pack(side=BOTTOM, fill="both", expand=True)


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
        self.submit_number_of_stocks = Button(self.num_stocks_frame, text="Apply", command=lambda: self.update_stocklist(callback=True))
        self.submit_number_of_stocks.pack(side=LEFT)

        # Refresh button
        self.refresh_stocklist_button = Button(self.refresh_frame, text="Refresh stocklist",
                                               state=DISABLED,
                                               command=self.refresh_stocklist_button_callback)
        self.refresh_stocklist_button.pack(side=LEFT)

        # Filter options
        self.filter_frame_label = Label(self.filter_frame, text="Active filters (evaluated top-down):")
        self.filter_frame_label.pack(side=TOP)
        self.selected_filter = StringVar(self.filter_frame, value=self.data_interface.get_active_filters()[0])
        self.active_filters_menu = OptionMenu(self.filter_frame, self.selected_filter, self.data_interface.get_active_filters()[0])
        self.active_filters_menu.pack(side=LEFT)
        self.remove_filter_button = Button(self.filter_frame, text="Remove filter", command=self.remove_filter_callback)
        self.remove_filter_button.pack(side=LEFT)
        self.edit_filter_button = Button(self.filter_frame, text="Edit filter", command=self.edit_filter_button_callback)
        self.edit_filter_button.pack(side=LEFT)

        # Plot options
        self.plot_label = Label(self.plot_frame, text="Plot options")
        self.plot_label.pack(side=TOP)
        self.plot_button = Button(self.plot_frame, text="Plot selected stock", command=self.plot_button_callback)
        self.plot_button.pack(side=LEFT)

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
        self.setup_popup_menus()

        # Bind keys to functions
        self.root.bind("<Return>", self.enter_key_callback)
        self.tree.bind("<Button-3>", self.right_click_callback)
        self.tree.bind("<Button-1>", self.mouse_click_callback)

        self.data_interface.set_working_stocklist(self.num_stocks)
        self.initialize_stocklist()


    def setup_popup_menus(self) -> None:
        """ Initialize popup menus

        Description
        -----------
        Setup the popup menus that should appear when a user right clicks anywhere in the treeview. The popup menu is
        different depending on if a header or a data row is clicked.
        """

        self.stock_popup = Menu(self.root, tearoff=0)
        self.stock_popup.add_command(label="Open on Yahoo Finance", command=self.open_yahoo_finance_webpage)
        self.stock_popup.add_command(label="Open on Marketwatch", command=self.open_marketwatch_webpage)
        self.stock_popup.add_command(label="Open on Tradefollowers", command=self.open_tradefollowers_webpage)
        self.stock_popup.add_command(label="Open on Sentdex", command=self.open_sentdex_webpage)

        self.filter_popup = Menu(self.root, tearoff=0)
        self.filter_popup.add_command(label="is NaN", command= lambda: self.filter_function(cell_is_nan, 0, "is_nan"))
        self.filter_popup.add_command(label="is not NaN", command= lambda: self.filter_function(cell_is_not_nan, 1, "not_nan"))
        self.filter_popup.add_separator()

        self.filter_popup.add_command(label="Text contains", command= lambda: self.filter_function(cell_contains, 3, "str"))
        self.filter_popup.add_command(label="Text does not contain", command= lambda: self.filter_function(cell_does_not_contain, 4, "str"))
        self.filter_popup.add_command(label="Text equal to", command= lambda: self.filter_function(cell_string_equals, 5, "str"))
        self.filter_popup.add_command(label="Text not equal to", command= lambda: self.filter_function(cell_string_not_equals, 6, "str"))
        self.filter_popup.add_separator()

        self.filter_popup.add_command(label="Number greater than", command= lambda: self.filter_function(cell_greater_than, 8, "num"))
        self.filter_popup.add_command(label="Number greater than or qual to", command= lambda: self.filter_function(cell_greater_than_or_equal, 9, "num"))
        self.filter_popup.add_command(label="Number less than", command= lambda: self.filter_function(cell_less_than, 10, "num"))
        self.filter_popup.add_command(label="Number less than or equal to", command= lambda: self.filter_function(cell_less_than_or_equal, 11, "num"))
        self.filter_popup.add_command(label="Number equal to", command= lambda: self.filter_function(cell_num_equals, 12, "num"))
        self.filter_popup.add_command(label="Number not equal to", command= lambda: self.filter_function(cell_num_not_equals, 13, "num"))


    """ Treeview related """
    def initialize_stocklist(self) -> None:
        print("{} Initialize stocklist to {} stocks.".format(GUI_MESSAGE_HEADER, self.num_stocks))
        self.data_interface.set_working_stocklist(self.num_stocks)
        self.clear_tree()
        self.fill_tree()

    def fill_tree(self) -> None:
        for i, stock in enumerate(self.data_interface.get_working_stocklist().iterrows()):
            self.insert_data(i, stock)


    def insert_data(self, id, stock) -> None:
        self.treeview.insert("", "end", iid=id, values=tuple(stock[1]))


    def clear_tree(self) -> None:
        # Clear current tree
        for row in self.treeview.get_children():
            self.treeview.delete(row)


    def update_stocklist(self, callback=False) -> None:
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


    def check_for_new_data(self) -> None:
        # print("{} Checking for new data to load...".format(GUI_MESSAGE_HEADER))
        if self.data_interface.update_stocklist():
            # This should not be forced, a button sould appear if this returns true
            if self.refresh_stocklist_button["state"] == DISABLED:
                self.refresh_stocklist_button["state"] = NORMAL

        self.root.after(500, self.check_for_new_data)


    """ Callback functions """
    def mouse_click_callback(self, event) -> None:
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            heading = self.tree.heading(column)
            if heading["text"] == self.sort_variable_string:
                self.change_sort_direction(mouse_click=True)

            self.set_sort_variable(heading["text"], mouse_click=True)
            self.sort_stocklist()


    def right_click_callback(self, event) -> None:
        """ Handle right click on treeview

        Description
        -----------
        Decides what to do when the treeview is right clicked and where to place the popup menu.

        """

        try:
            region = self.tree.identify("region", event.x, event.y)
            if region == "cell":
                self.tree.selection_set(self.tree.identify_row(event.y))
                self.stock_popup.selection = self.tree.set(self.tree.identify_row(event.y))
                self.stock_popup.post(event.x_root, event.y_root)
            elif region == "heading":
                column = self.tree.identify_column(event.x)
                # Since the treeview can't select a column the heading needs to be stored somewhere else
                self.heading_to_filter = self.tree.heading(column)
                self.filter_popup.post(event.x_root, event.y_root)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.stock_popup.grab_release()


    def enter_key_callback(self, event) -> None:
        focused_widget = self.root.focus_get()
        if focused_widget is self.number_of_stocks_entry:
            self.update_stocklist(callback=True)


    def refresh_stocklist_button_callback(self):
        self.data_interface.set_working_stocklist(self.num_stocks)
        self.sort_stocklist()
        self.refresh_stocklist_button["state"] = DISABLED


    def edit_filter_button_callback(self) -> None:
        self.edit_filter()


    def remove_filter_callback(self) -> None:
        self.data_interface.remove_filter(self.selected_filter.get())
        self.apply_filters()


    def plot_button_callback(self) -> None:
        selected_stock = self.tree.item(self.tree.focus())
        if selected_stock["values"]:
            # Selected stock is only a list and doesn't contain any column headings
            selected_stock = {key: value for key, value in zip(self.sort_options, selected_stock["values"])}
            stock_data = self.data_interface.get_stock_data_over_time(selected_stock)

            plotter = Plotter(stock_data)
            plotter.start()



    """ Right click functions """
    def open_yahoo_finance_webpage(self):
        stock_symbol = self.stock_popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_yahoo_finance_webpage(stock_symbol))


    def open_marketwatch_webpage(self):
        stock_symbol = self.stock_popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_marketwatch_webpage(stock_symbol))


    def open_tradefollowers_webpage(self):
        stock_symbol = self.stock_popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_tradefollowers_webpage(stock_symbol))


    def open_sentdex_webpage(self):
        stock_symbol = self.stock_popup.selection["Symbol"]
        webbrowser.open_new_tab(self.data_interface.get_sentdex_webpage(stock_symbol))


    """ Filter functions """
    def filter_function(self, filter_func, menu_index, type="") -> None:
        """ Filter data based on a criteria

        Description
        -----------
        Callback function for when the user right clicks a column heading. Depending on what option was clicked either
        prompt the used for the criteria to filter and the apply the filter or directly apply it.

        Parameters
        ----------
        filter_func : str
            A string indicating what logical operation to perform
        type : str
            A string indicating if it is a number or a string that should be filtered

        """
        column = self.heading_to_filter["text"]
        operation = self.filter_popup.entrycget(menu_index, "label").split(" ")
        operation = " ".join(operation[1::]) if len(operation) > 1 else operation[0]
        label = " ".join([column, operation])

        if type == "str" or type == "num":
            filter_value = self.get_filter_parameters(type)["val"]
            if filter_value != None:
                if (isinstance(filter_value, int) or isinstance(filter_value, float)) and type == "num":
                    label += " {}".format(filter_value)
                elif filter_value and isinstance(filter_value, str) and type == "str":
                    filter_value = filter_value.rstrip()
                    label += " " + filter_value

                self.data_interface.filter_working_stocklist(column, filter_func, label, filter_value)
        else:
            self.data_interface.filter_working_stocklist(column, filter_func, label)

        self.apply_filters()


    def get_filter_parameters(self, type) -> dict:
        retval = {"val": None}
        if type == "num":
            retval["val"] = simpledialog.askfloat("num", "Enter value:", parent=self.root)
        elif type == "str":
            retval["val"] = simpledialog.askstring("num", "Enter string:", parent=self.root)

        return retval


    def apply_filters(self) -> None:
        self.update_active_filter_list()
        self.clear_tree()
        self.data_interface.perform_filtering()
        self.update_stocklist()


    def update_active_filter_list(self) -> None:
        active_filters = self.data_interface.get_active_filters()
        self.active_filters_menu["menu"].delete(0, "end")
        for i, filter in enumerate(active_filters):
            if i == 0:
                self.selected_filter.set(filter)
            self.active_filters_menu["menu"].add_command(label=filter, command=tkinter._setit(self.selected_filter, filter))


    def edit_filter(self) -> None:
        index, filter = self.data_interface.get_filter(self.selected_filter.get())
        if index >= 0 and filter != None:
            if isinstance(filter["val"], float) or isinstance(filter["val"], int):
                new_value = self.get_filter_parameters("num")["val"]
            elif isinstance(filter["val"], str):
                new_value = self.get_filter_parameters("str")["val"]

            if new_value != None:
                filter["val"] = new_value
                self.data_interface.replace_filter_at_index(filter, index)

                self.apply_filters()


    """ Sort functions """
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


    def sort_stocklist(self) -> None:
        if self.data_interface.sort_working_stocklist(self.sort_variable_string, self.sort_direction):
            self.clear_tree()

            # Draw new sorted stocklist
            self.update_stocklist()
