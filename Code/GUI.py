import pandas as pd

from DataGatherer import data_gatherer
from tkinter import *
from tkinter import ttk


class GUI(Frame):
    def __init__(self, root):
        self.id = 0
        self.num_stocks = 10
        self.ascending = False
        self.root = root
        self.stocklist = data_gatherer()
        self.working_stocklist = self.stocklist.head()
        self.initialize_user_interface()

    
    def initialize_user_interface(self) -> None:
        # Configure the root object 
        self.root.title("Stock Screener")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.config(background="white")

        # Configure private variables
        self.sort_options = list(self.stocklist.columns)
        self.sort_variable_string = "Volume"
        self.sort_direction = False # False is descending and True is ascending
        
        # Define the different GUI widgets
        self.options_frame = Frame(self.root)
        self.options_frame.pack(side=TOP)

        # Sort options
        self.sort_frame = Frame(self.options_frame)
        self.sort_frame.pack(side=TOP)
        self.sort_var = StringVar(self.sort_frame)
        self.sort_label = Label(self.sort_frame, text="Sorting key:")
        self.sort_key = OptionMenu(self.sort_frame, self.sort_var, *self.sort_options, command=self.set_sort_variable)
        self.submit_sorting_option = Button(self.sort_frame, text="Apply sorting", command=self.sort_stocklist)
        self.sort_label.pack(side=TOP)
        self.sort_key.pack(side=LEFT)
        self.submit_sorting_option.pack(side=RIGHT)

        # Number of stocks to display
        self.num_stocks_frame = Frame(self.options_frame)
        self.num_stocks_frame.pack(side=BOTTOM)
        self.number_of_stocks_label = Label(self.num_stocks_frame, text="Number of stocks to show:")
        self.number_of_stocks_entry = Entry(self.num_stocks_frame)
        self.number_of_stocks_entry.pack(side=LEFT)
        self.submit_number_of_stocks = Button(self.num_stocks_frame, text="Apply",
                                              command=self.update_stocklist)
        self.number_of_stocks_label.pack(side=TOP)
        self.number_of_stocks_entry.pack(side=LEFT)
        self.submit_number_of_stocks.pack(side=RIGHT)

        # Setup treeview
        self.tree_frame = Frame(self.root)
        self.tree_frame.pack(side=BOTTOM)
        self.tree = ttk.Treeview(self.tree_frame, columns=tuple(self.stocklist.columns), selectmode='browse')
        self.tree.pack(side=LEFT, fill="x")
    
        for i, col in enumerate(self.stocklist.columns):
            self.tree.heading("{}".format(i), text=col)
            self.tree.column("{}".format(i), stretch=YES)

        self.tree["show"] = "headings"
        self.treeview = self.tree

        self.vert_scrollbar = Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.vert_scrollbar.pack(side=RIGHT, fill="y")

        self.tree.configure(yscrollcommand=self.vert_scrollbar.set)

        self.update_stocklist(initialize=True)


    def set_sort_variable(self, selection) -> None:
        self.sort_variable_string = selection


    def update_stocklist(self, initialize=False, sorting=False) -> None:
        if not initialize and not sorting:
            self.num_stocks = int(self.number_of_stocks_entry.get())
                
        print("Limit stocklist to {}.".format(self.num_stocks))
        
        if not sorting:
            self.working_stocklist = self.stocklist.head(self.num_stocks)
            self.clear_tree()
        
        for i, stock in enumerate(self.working_stocklist.iterrows()):
            self.insert_data(i, stock)


    def sort_stocklist(self) -> None:
        if self.sort_variable_string in self.working_stocklist.columns:
            print("Sorting stocklist based on '{}'.".format(self.sort_variable_string))
            self.working_stocklist = self.working_stocklist.sort_values(by=[self.sort_variable_string],
                                                                        ascending=self.ascending)
            self.clear_tree()

            # Draw new sorted stocklist
            self.update_stocklist(sorting=True)


    def insert_data(self, id, stock) -> None:
        # For some reason 'text=' corresponds to the first column in the tree
        self.treeview.insert("", "end", iid=id, text=stock[1][0], values=tuple(stock[1][1::]))

    
    def clear_tree(self) -> None:
        # Clear current tree
        for row in self.treeview.get_children():
            self.treeview.delete(row)


app = GUI(Tk())
app.root.mainloop()