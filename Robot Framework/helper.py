from io import StringIO
from pathlib import Path

import pandas as pd


def read_html_table(table_element):
    """Read a native HTML table or Plotly table trace into a DataFrame."""
    if table_element.tag_name.lower() == "table":
        html = table_element.get_attribute("outerHTML")
        return pd.read_html(StringIO(html))[0]

    traces = table_element.parent.execute_script(
        "return arguments[0].data || [];", table_element
    )
    table_trace = next(
        (trace for trace in traces if trace.get("type") == "table"), None
    )
    if table_trace is None:
        raise AssertionError("No HTML table or Plotly table trace was found.")

    headers = table_trace["header"]["values"]
    values = table_trace["cells"]["values"]
    df = pd.DataFrame({header: column for header, column in zip(headers, values)})
    return df.rename(columns={
        "Facility Type": "facility_type",
        "Visit Date": "visit_date",
        "Average Time Spent": "avg_time_spent",
    })


def read_parquet_dataset(folder, filter_date=None, date_column="date",
                         drop_date_column=False, expected_columns=None):
    """
    Read a (partitioned) Parquet dataset into a DataFrame.
    If filter_date (YYYY-MM-DD) is given, keep the seven-day window ending
    on that date, matching the report's rolling-week table.
    """
    dataset_folder = Path(folder)
    if expected_columns is not None:
        expected_columns = set(expected_columns)
        child_folders = [path for path in dataset_folder.iterdir() if path.is_dir()]
        candidates = []
        for child_folder in child_folders:
            sample_file = next(child_folder.rglob("*.parquet"), None)
            if sample_file is None:
                continue
            sample_columns = set(pd.read_parquet(sample_file).columns)
            if expected_columns.issubset(sample_columns):
                candidates.append(child_folder)

        if len(candidates) != 1:
            raise AssertionError(
                f"Expected one Parquet dataset matching columns "
                f"{sorted(expected_columns)}, found {len(candidates)}."
            )
        folder = candidates[0]

    df = pd.read_parquet(folder)

    if expected_columns is not None and "partition_date" in df.columns:
        if "partition_date" not in expected_columns:
            df = df.drop(columns=["partition_date"])

    if filter_date and str(filter_date).strip().upper() != "NONE":
        if date_column not in df.columns:
            raise AssertionError(
                f"Column '{date_column}' not found in Parquet data. "
                f"Available columns: {list(df.columns)}"
            )
        end_date = pd.to_datetime(filter_date).normalize()
        start_date = end_date - pd.Timedelta(days=6)
        values = pd.to_datetime(df[date_column], errors="coerce").dt.normalize()
        df = df[values.between(start_date, end_date)]

    if str(drop_date_column).lower() == "true" and date_column in df.columns:
        df = df.drop(columns=[date_column])

    return df.reset_index(drop=True)


def _normalize_value(value):
    """Convert any cell to a comparable string (e.g. 1, 1.0, '1' -> '1')."""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
        return str(number)
    except ValueError:
        return text


def _normalize(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime("%Y-%m-%d")
        df[column] = df[column].map(_normalize_value)
    return df


def compare_dataframes(html_df, parquet_df):
    """
    Compare two DataFrames for an exact match (row order is ignored).
    Raises AssertionError with a list of differences if they don't match.
    """
    left = _normalize(html_df)
    right = _normalize(parquet_df)

    if set(left.columns) != set(right.columns):
        raise AssertionError(
            "Column mismatch!\n"
            f"HTML columns:    {list(left.columns)}\n"
            f"Parquet columns: {list(right.columns)}"
        )

    columns = list(left.columns)
    right = right[columns]

    left["_dup"] = left.groupby(columns).cumcount()
    right["_dup"] = right.groupby(columns).cumcount()

    merged = left.merge(right, how="outer", on=columns + ["_dup"], indicator=True)
    diff = merged[merged["_merge"] != "both"].drop(columns="_dup")

    if diff.empty:
        return True

    diff["_merge"] = diff["_merge"].map({
        "left_only": "ONLY IN HTML",
        "right_only": "ONLY IN PARQUET",
    })
    diff = diff.rename(columns={"_merge": "source"})

    raise AssertionError(
        f"DataFrames do not match! HTML rows: {len(left)}, "
        f"Parquet rows: {len(right)}, differences: {len(diff)}\n\n"
        f"{diff.to_string(index=False)}"
    )