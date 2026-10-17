import pytest
import pandas as pd
from pathlib import Path

# Fixture to read the CSV file 
@pytest.fixture(scope="session")
def read_csv(path_to_file=None):
    """
    Reads the CSV file using pandas and returns the DataFrame.
    Resolves the default path if path_to_file is not explicitly passed.
    """
    if path_to_file is None:
        base_dir = Path(__file__).resolve().parent.parent
        path_to_file = base_dir / "src" / "data" / "data.csv"

    if not path_to_file.exists():
        pytest.fail(f"CSV file not found at: {path_to_file}")

    # Read all columns as strings to preserve formatting
    df = pd.read_csv(path_to_file, dtype=str)
    return df

# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema():
    """
    Fixture function to validate the actual schema against the expected schema.
    """
    def _validate(actual_schema, expected_schema):
        actual_list = list(actual_schema)
        expected_list = list(expected_schema)
        assert actual_list == expected_list, (
            f"Schema Error: Expected columns {expected_list}, but found {actual_list}"
        )
    return _validate

# Pytest hook to mark unmarked tests with a custom mark
def pytest_collection_modifyitems(items, config):
    """
    Dynamically assigns the 'unmarked' marker to tests that do not have explicit marks.
    """
    for item in items:
        user_marks = [
            mark for mark in item.iter_markers()
            if mark.name not in ("parametrize", "usefixtures")
        ]
        if not user_marks and not list(item.iter_markers()):
            item.add_marker(pytest.mark.unmarked)