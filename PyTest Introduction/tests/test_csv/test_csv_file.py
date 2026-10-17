import pytest
import re

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def test_file_not_empty(read_csv):
    assert not read_csv.empty, (
        "Assertion Error: The CSV file is completely empty or has no data rows."
    )


# 2. Validate there are no duplicate rows (validate_csv, xfail)
@pytest.mark.xfail(reason="Expected to fail if duplicate rows are present in the CSV")
@pytest.mark.validate_csv
def test_duplicates(read_csv):
    duplicates = read_csv[read_csv.duplicated()]
    assert duplicates.empty, (
        f"Assertion Error: Found {len(duplicates)} duplicate row(s) in the CSV file."
    )


# 3. Validate the schema of the file (validate_csv)
@pytest.mark.validate_csv
def test_validate_schema(read_csv, validate_schema):
    expected_schema = ["id", "name", "age", "email", "is_active"]
    validate_schema(read_csv.columns, expected_schema)


# 4. Validate that age column contains valid values (validate_csv, skip)
@pytest.mark.skip(reason="Skipping age validation test as per requirements")
@pytest.mark.validate_csv
def test_age_column_valid(read_csv):
    for _, row in read_csv.iterrows():
        age_str = str(row["age"]).strip()
        assert age_str.isdigit(), (
            f"Assertion Error: Age for ID {row['id']} is not an integer: '{age_str}'"
        )
        age = int(age_str)
        assert 0 <= age <= 100, (
            f"Assertion Error: Age for ID {row['id']} is out of valid range (0-100): {age}"
        )


# 5. Validate that email column contains valid email addresses (validate_csv)
@pytest.mark.validate_csv
def test_email_column_valid(read_csv):
    for _, row in read_csv.iterrows():
        email = str(row["email"]).strip()
        assert re.match(EMAIL_REGEX, email), (
            f"Assertion Error: Invalid email format '{email}' found for row ID {row['id']}."
        )


# 6. Validate is_active for id=1 and id=2 with parametrize
@pytest.mark.parametrize("target_id, expected_is_active", [
    ("1", "False"),
    ("2", "True"),
])
def test_active_players(read_csv, target_id, expected_is_active):
    matched_rows = read_csv[read_csv["id"] == str(target_id)]
    assert not matched_rows.empty, (
        f"Assertion Error: Player with ID {target_id} was not found in CSV."
    )
    actual_value = str(matched_rows.iloc[0]["is_active"]).strip()
    assert actual_value == expected_is_active, (
        f"Assertion Error: Expected is_active={expected_is_active} for ID {target_id}, "
        f"but got '{actual_value}'"
    )


# 7. Validate is_active for id=2 without parametrize (Unmarked)
def test_active_player(read_csv):
    target_id = "2"
    expected_is_active = "True"
    matched_rows = read_csv[read_csv["id"] == target_id]
    assert not matched_rows.empty, (
        f"Assertion Error: Player with ID {target_id} was not found in CSV."
    )
    actual_value = str(matched_rows.iloc[0]["is_active"]).strip()
    assert actual_value == expected_is_active, (
        f"Assertion Error: Expected is_active={expected_is_active} for ID {target_id}, "
        f"but got '{actual_value}'"
    )
