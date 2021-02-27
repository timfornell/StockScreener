from datetime import date
from pathlib import Path
from enum import Enum

DATA_FOLDER = Path("Database/{}".format(date.today()))
STOCKLIST_PICKLE_FILE = "CompleteStocklist"
DATA_INTERFACE_MESSAGE_HEADER = "@DI:"
DATA_GATHERER_MESSAGE_HEADER = "@DG:"
DATA_COMMON_MESSAGE_HEADER = "@DC:"
GUI_MESSAGE_HEADER = "@GUI:"

STOCK_SYMBOL_POSITION = 1

# Stocklist definitions
stocklist_enum = Enum("Stocklists",
                 "Movers " +
                 "CompanyInfo " +
                 "TwitterBullBear " +
                 "TwitterMomentum")

ENOUGH_STOCKS_UPDATED_TO_SIGNAL = 5
