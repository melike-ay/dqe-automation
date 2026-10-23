from typing import List, Optional
import pandas as pd


class DataQualityLibrary:
    """
    A library of static methods for performing data quality checks on pandas DataFrames.
    Uses assertions to ensure data meets expected conditions with clear diagnostic messages.
    """

    @staticmethod
    def check_dataset_is_not_empty(df: pd.DataFrame) -> None:
        """Smoke check to verify dataframe exists and contains rows."""
        assert df is not None, "Dataset is None."
        assert not df.empty, "Dataset is empty (contains 0 rows)."
        assert len(df) > 0, f"Expected dataset to contain rows, got {len(df)} rows."

    @staticmethod
    def check_count(df_expected: pd.DataFrame, df_actual: pd.DataFrame) -> None:
        """Validates that the row counts of source and target datasets match."""
        expected_count = len(df_expected)
        actual_count = len(df_actual)
        diff = actual_count - expected_count
        assert expected_count == actual_count, (
            f"Row count mismatch! Expected (Postgres): {expected_count}, "
            f"Actual (Parquet): {actual_count}. Difference: {diff}"
        )

    @staticmethod
    def check_data_completeness(df_expected: pd.DataFrame, df_actual: pd.DataFrame) -> None:
        """Validates that all expected rows and columns exist in actual dataset, ignoring row order."""
        assert df_expected is not None and df_actual is not None, "One of the DataFrames is None."

        df_exp = df_expected.copy()
        df_act = df_actual.copy()

        # Normalize column names to lowercase
        df_exp.columns = [str(col).lower().strip() for col in df_exp.columns]
        df_act.columns = [str(col).lower().strip() for col in df_act.columns]

        # Verify all expected columns exist
        missing_cols = set(df_exp.columns) - set(df_act.columns)
        assert not missing_cols, f"Missing columns in target Parquet dataset: {missing_cols}"

        # Align columns to same order
        common_cols = [c for c in df_exp.columns if c in df_act.columns]
        df_exp = df_exp[common_cols]
        df_act = df_act[common_cols]

        # Normalize data formats (dates and floats) for reliable comparison
        for col in common_cols:
            if pd.api.types.is_float_dtype(df_exp[col]) or pd.api.types.is_float_dtype(df_act[col]):
                df_exp[col] = df_exp[col].astype(float).round(2)
                df_act[col] = df_act[col].astype(float).round(2)
            elif pd.api.types.is_datetime64_any_dtype(df_exp[col]) or pd.api.types.is_datetime64_any_dtype(df_act[col]):
                df_exp[col] = pd.to_datetime(df_exp[col]).dt.strftime("%Y-%m-%d")
                df_act[col] = pd.to_datetime(df_act[col]).dt.strftime("%Y-%m-%d")
            else:
                df_exp[col] = df_exp[col].astype(str).str.strip()
                df_act[col] = df_act[col].astype(str).str.strip()

        # Sort values so row order does not cause false failures
        df_exp_sorted = df_exp.sort_values(by=common_cols).reset_index(drop=True)
        df_act_sorted = df_act.sort_values(by=common_cols).reset_index(drop=True)

        # Check count alignment
        assert len(df_exp_sorted) == len(df_act_sorted), (
            f"Completeness check failed due to row count mismatch. "
            f"Expected rows: {len(df_exp_sorted)}, Actual rows: {len(df_act_sorted)}"
        )

        # Compare values
        mismatches = df_exp_sorted.compare(df_act_sorted)
        assert mismatches.empty, (
            f"Data completeness check failed! Discrepancies found between source and target:\n"
            f"{mismatches.head(10)}"
        )

    @staticmethod
    def check_duplicates(df: pd.DataFrame, column_names: Optional[List[str]] = None) -> None:
        """Validates that there are no duplicate records on specified columns (or all columns)."""
        subset = column_names if column_names else df.columns.tolist()
        duplicate_rows = df[df.duplicated(subset=subset, keep=False)]
        assert duplicate_rows.empty, (
            f"Uniqueness check failed! Found {len(duplicate_rows)} duplicate rows across {subset}:\n"
            f"{duplicate_rows.head(10)}"
        )

    @staticmethod
    def check_not_null_values(df: pd.DataFrame, column_names: Optional[List[str]] = None) -> None:
        """Validates that the specified columns contain no NULL / NaN / None values."""
        cols_to_check = column_names if column_names else df.columns.tolist()
        null_issues = {}

        for col in cols_to_check:
            if col not in df.columns:
                null_issues[col] = "Column not found in dataset"
            else:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    null_issues[col] = f"{null_count} null rows"

        assert not null_issues, f"Not-Null check failed! Nulls found in columns: {null_issues}"

    # Alias to support legacy naming if referenced anywhere
    check_data_full_data_set = check_data_completeness