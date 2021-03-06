import sys
import multiprocessing as mp

from tkinter import *
from multiprocessing.managers import BaseManager

from DataInterface import DataInterface
from Definitions import DATA_GATHERER_MESSAGE_HEADER, DATA_INTERFACE_MESSAGE_HEADER, GUI_MESSAGE_HEADER
from GUI import GUI
from DataGatherer import DataGatherer


def run_data_interface(event: mp.Event, lock: mp.Lock, queue: mp.Queue):
    app = GUI(Tk(), event, lock, queue)
    app.root.mainloop()


def run_data_gatherer(event: mp.Event, lock: mp.Lock, queue: mp.Queue):
    print("{} Data gatherer starting...".format(DATA_GATHERER_MESSAGE_HEADER))
    data_gatherer = DataGatherer(lock, queue)
    data_gatherer.gather_new_data()
    print("{} Data gathering finished!".format(DATA_GATHERER_MESSAGE_HEADER))
    event.set()
    print("{} Event set! Will start gathering missing data...".format(DATA_GATHERER_MESSAGE_HEADER))

    while True:
        data_gatherer.check_message_queue()


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
    # The queue is intended to be used to signal the data interface when new data can be read
    dg_queue = mp.Queue()
    di_queue = mp.Queue()
    queue = {DATA_GATHERER_MESSAGE_HEADER: dg_queue, DATA_INTERFACE_MESSAGE_HEADER: di_queue}

    data_if_proc = mp.Process(name="Data_Interface", target=run_data_interface, args=(event, lock, queue))
    data_if_proc.start()

    data_gath_proc = mp.Process(name="Data_Gatherer", target=run_data_gatherer, args=(event, lock, queue))
    data_gath_proc.start()

    data_if_proc.join()

    data_if_proc.kill()
    data_gath_proc.kill()
