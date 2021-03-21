from datetime import date
from pathlib import Path
from enum import Enum

DATA_FOLDER = Path("Database")
CURRENT_DATA_FOLDER = Path.joinpath(DATA_FOLDER, "{}".format(date.today()))
TIME_SORTED_DATA = Path.joinpath(DATA_FOLDER, "StockDataOverTime")
STOCKLIST_PICKLE_FILE = "CompleteStocklist"
DATA_INTERFACE_MESSAGE_HEADER = "@DI:"
DATA_GATHERER_MESSAGE_HEADER = "@DG:"
DATA_COMMON_MESSAGE_HEADER = "@DC:"
GUI_MESSAGE_HEADER = "@GUI:"

# Stocklist definitions
stocklist_enum = Enum("Stocklists",
                 "Movers " +
                 "CompanyInfo " +
                 "TwitterBullBear " +
                 "TwitterMomentum")

ENOUGH_STOCKS_UPDATED_TO_SIGNAL = 5

# GUI Definitions
NUMBER_OF_OPTION_FRAMES = 10
