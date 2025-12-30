# backend/exercise_classifier/dataset_manager.py

import os
import pandas as pd

MAIN_DATASET = "data/exercise_features.csv"
AUTOSET = "data/autolabel/features_autoset.csv"


class DatasetManager:
    def __init__(self):
        os.makedirs("data/autolabel", exist_ok=True)
        if not os.path.exists(AUTOSET):
            open(AUTOSET, "w").close()

    def load_main(self):
        return pd.read_csv(MAIN_DATASET)

    def load_autoset(self):
        try:
            return pd.read_csv(AUTOSET)
        except Exception:
            return pd.DataFrame()

    def append_autoset_row(self, row_dict: dict):
        """Row dict must contain all feature columns + 'label' field."""
        df = pd.DataFrame([row_dict])
        df.to_csv(AUTOSET, mode="a", index=False, header=False if os.path.getsize(AUTOSET) > 0 else True)

    def merged(self):
        df_main = self.load_main()
        df_auto = self.load_autoset()
        return pd.concat([df_main, df_auto], ignore_index=True)
