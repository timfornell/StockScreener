import pandas as pd

from multiprocessing import Process


class Plotter(Process):
    def __init__(self, stock_data: pd.DataFrame):
        super(Plotter, self).__init__()
        self.plot_data = stock_data.copy()


    def set_plot_data(self, data: pd.DataFrame) -> None:
        self.plot_data = data.copy()


    def run(self):
        print("I am alive!")
