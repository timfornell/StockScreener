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
        self.root.config(background="black")

        # Configure private variables
        self.sort_options = list(self.stocklist.columns)
        self.sort_variable_string = "Volume"
        self.sort_direction = False # False is descending and True is ascending
        self.sort_var = StringVar(self.root)

        # Define the different GUI widgets
        self.sort_label = Label(self.root, text="Sorting key:")
        self.sort_key = OptionMenu(self.root, self.sort_var, *self.sort_options, command=self.set_sort_variable)
        self.submit_sorting_option = Button(self.root, text="Apply sorting", command=self.sort_stocklist)
        self.sort_label.grid(row=0, column=0, sticky=W)
        self.sort_key.grid(row=0, column=1, sticky=W)
        self.submit_sorting_option.grid(row=0, column=2, sticky=W)

        self.number_of_stocks_label = Label(self.root, text="Number of stocks to show:")
        self.number_of_stocks_entry = Entry(self.root)
        self.number_of_stocks_entry.grid(row=1, column=0, sticky=W)
        self.submit_number_of_stocks = Button(self.root, text="Apply",
                                              command=self.update_stocklist)
        self.number_of_stocks_label.grid(row=1, column=0, sticky=W)
        self.number_of_stocks_entry.grid(row=1, column=1, sticky=W)
        self.submit_number_of_stocks.grid(row=1, column=2, sticky=W)

        # Setup treeview
        self.tree = ttk.Treeview(self.root, columns=tuple(self.stocklist.columns))
        for i, col in enumerate(self.stocklist.columns):
            self.tree.heading("#{}".format(i), text=col)
            self.tree.column("#{}".format(i), stretch=YES)

        self.tree.grid(row=len(self.stocklist.index), columnspan=len(list(self.stocklist.columns)), sticky=NSEW)
        self.treeview = self.tree

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


    # def build_table(self) -> None:
    #     tree.insert(parent='', index='end', iid=0, text="Label", values=list(stocklist.columns))

        # rows = []
        # cols = []
        
        # for i, label in enumerate(stocklist.columns):
        #     entry = Entry(relief=GROOVE)
        #     entry.grid(row=0, column=i, sticky=NSEW)
        #     entry.insert(END, "{}".format(label))
        #     cols.append(entry)
        
        # for j, stock in enumerate(stocklist.iterrows()):
        #     cols = []
            
        #     # stock[1] contains all data of interest
        #     for i, col in enumerate(stock[1]):
        #         entry = Entry(relief=GROOVE)
        #         # Row = j + 1 to take into account the headlines
        #         entry.grid(row=j + 1, column=i, sticky=NSEW)
        #         entry.insert(END, '{}'.format(col))
        #         cols.append(entry)

        #     rows.append(cols)


# def main():
#     stocks = data_gatherer()
#     sorted_stocks = sort_stocklist(stocks, "Volume", False)
#     sorted_stocks_head = sorted_stocks.head()

#     root = Tk()
    
#     # Sorting variable
#     sort_var = StringVar(root)
#     sort_var.set("Volume")

#     sort_options = [col for col in sorted_stocks.columns]
#     options = OptionMenu(root, sort_var, *sort_options)
#     options.pack()

#     button = Button(root, text="OK")
#     button.pack()

#     table = Frame(root)
#     table.pack(side=BOTTOM)

#     tree = ttk.Treeview(root, columns=tuple(sort_options))

#     build_table(tree, sorted_stocks_head)
#     mainloop()


app = GUI(Tk())
app.root.mainloop()