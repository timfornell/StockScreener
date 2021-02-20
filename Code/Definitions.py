from datetime import date
from pathlib import Path
from enum import Enum

DATA_FOLDER = Path("Database/{}".format(date.today()))
DATA_INTERFACE_MESSAGE_HEADER = "@DI:"
DATA_GATHERER_MESSAGE_HEADER = "@DG:"
GUI_MESSAGE_HEADER = "@GUI:"

# Stocklist definitions
stocklist_enum = Enum("Stocklists",
                 "Movers " +
                 "CompanyInfo " +
                 "TwitterBullBear " +
                 "TwitterMomentum")

ENOUGH_STOCKS_PARSED_TO_SIGNAL = 2