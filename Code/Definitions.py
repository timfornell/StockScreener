from datetime import date
from pathlib import Path

DATA_FOLDER = Path("Database/{}".format(date.today()))
DATA_INTERFACE_MESSAGE_HEADER = "@DI:"
DATA_GATHERER_MESSAGE_HEADER = "@DG:"
GUI_MESSAGE_HEADER = "@GUI:"