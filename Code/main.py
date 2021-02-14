from multiprocessing import Process
from GUI import GUI
from DataGatherer import update_stocks_with_missing_data
from tkinter import *

if __name__ == "__main__":
    app = GUI(Tk())
    app.root.mainloop()

    # data_proc = Process(target=update_stocks_with_missing_data)
    # data_proc.start()
    # data_proc.join()