from pathlib import Path
import pandas as pd


class Olist:
    """
    The Olist class provides methods to interact with Olist's e-commerce data.

    Methods:
        get_data():
            Loads and returns a dictionary where keys are dataset names (e.g., 'sellers', 'orders')
            and values are pandas DataFrames loaded from corresponding CSV files.

        ping():
            Prints "pong" to confirm the method is callable.
    """
    def get_data(self):
        """
        This function returns a Python dict.
        Its keys should be 'sellers', 'orders', 'order_items' etc...
        Its values should be pandas.DataFrames loaded from csv files
        """
        csv_path = Path("~/.workintech/olist/data/csv").expanduser()

        file_paths = list(csv_path.iterdir())

        file_names = [file.name for file in file_paths]

        key_names = [name.replace(".csv","").replace("_dataset","").replace("olist_","") for name in file_names]

        data = {}

        for path, name in zip(file_paths, key_names):
            data[name] = pd.read_csv(path)
    
        return data

    def ping(self):
        """
        You call ping I print pong.
        """
        print("pong")
