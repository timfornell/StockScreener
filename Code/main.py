import sys
import multiprocessing as mp

from DataInterface import DataInterface
from GUI import GUI
from DataGatherer import DataGatherer
from tkinter import *


def run_GUI(data_interface: DataInterface, event: mp.Event, lock: mp.Lock):
    print("GUI waiting for data gatherer to finish.")
    event.wait()
    print("Data gatherer has finished: {}, starting GUI!".format(event.is_set()))
    app = GUI(Tk(), data_interface, event, lock)
    app.root.mainloop()
    print("GUI finished!")


def run_data_gatherer(data_interface: DataInterface, event: mp.Event, lock: mp.Lock):
    print("Data gatherer starting...")
    data_gatherer = DataGatherer(lock)
    data_gatherer.gather_data()
    with lock:
        print("Data gatherer acquired lock to update data interface.")
        data_interface.update_stocklist()
        print("Data is updated")

    event.set()
    print("Event set! Will start gathering missing data...")



if __name__ == "__main__":
    # Workaround to fix multiprocessing in a venv
    # https://stackoverflow.com/questions/54480527/multiprocessing-asyncresult-get-hangs-in-python-3-7-2-but-not-in-3-6
    if sys.prefix != sys.base_prefix:
        import _winapi
        import multiprocessing.spawn
        multiprocessing.spawn.set_executable(_winapi.GetModuleFileName(0))

    # The event is used to signal between the data gatherer and the GUI during startup that there is data available
    event = mp.Event()
    # The lock is intended to protect the DataInterface object to be accessed at the same time
    lock = mp.Lock()
    data_interface = DataInterface()

    gui_proc = mp.Process(name="GUI", target=run_GUI, args=(data_interface, event, lock,))
    gui_proc.start()

    data_proc = mp.Process(name="Data_Gatherer", target=run_data_gatherer, args=(data_interface, event, lock,))
    data_proc.start()