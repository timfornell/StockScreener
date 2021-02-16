import multiprocessing as mp
from GUI import GUI
from DataGatherer import update_stocks_with_missing_data
from tkinter import *
import sys


def run_GUI(event):
    print("Starting GUI!")
    app = GUI(Tk(), event)
    app.root.mainloop()
    print("GUI finished!")


def run_data_gatherer(event):
    print("run_data_gatherer waiting for GUI to initialize...")
    event.wait()
    print("run_data_gatherer started running!", event.is_set())


if __name__ == "__main__":
    # Fix to work around multiprocessing in a venv
    # https://stackoverflow.com/questions/54480527/multiprocessing-asyncresult-get-hangs-in-python-3-7-2-but-not-in-3-6
    if sys.prefix != sys.base_prefix:
        import _winapi
        import multiprocessing.spawn
        multiprocessing.spawn.set_executable(_winapi.GetModuleFileName(0))

    event = mp.Event()
    gui_proc = mp.Process(name="GUI", target=run_GUI, args=(event,))
    gui_proc.start()

    data_proc = mp.Process(name="Data_Gatherer", target=run_data_gatherer, args=(event,))
    data_proc.start()