import os
import pandas as pd


class ParquetReader:
    @staticmethod
    def process(target_path: str, include_subfolders: bool = True) -> pd.DataFrame:
        """
        Reads parquet file(s) from a given path or directory (including partitioned subfolders).
        Returns a consolidated pandas DataFrame.
        """
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Parquet target path does not exist: {target_path}")

        if os.path.isdir(target_path):
            if include_subfolders:
                # read_parquet handles directory with partition subfolders
                df = pd.read_parquet(target_path, engine="pyarrow")
            else:
                files = [os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith(".parquet")]
                if not files:
                    raise FileNotFoundError(f"No parquet files found in {target_path}")
                df = pd.concat([pd.read_parquet(f, engine="pyarrow") for f in files], ignore_index=True)
        else:
            df = pd.read_parquet(target_path, engine="pyarrow")

        return df