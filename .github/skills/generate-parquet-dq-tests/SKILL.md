---
name: generate-parquet-dq-tests
description: >-
  TODO: One or two sentences — what the skill generates, when to invoke it,
  and what it must refuse (framework/Jenkins/conftest). Example pattern:
  "Creates parquet_files test modules from docs/parquet-aggregated-data-mapping.md …"
disable-model-invocation: true
---

# Generate Parquet DQ tests

Complete this skill as **Step 2** of the PyTest DQ assignment. Read first:

- `PyTest DQ Framework/docs/test-automation-strategy.md` — **§5 Skill contract**, **§6 Test design standard**
- `docs/parquet-aggregated-data-mapping.md` — dataset definitions (expected SQL comes from here)

**Do not** paste expected SQL for the three named datasets into this skill.  
**Do not** instruct the agent to copy SQL from `data_dev/`.

When finished, every `TODO` below must be replaced. Run the **Skill review** checklist before using the skill to generate tests.

## When this skill applies


- Use this skill when asked to create or update test modules for target Parquet datasets under `PyTest DQ Framework/tests/dq checks/parquet_files/`.
- The core framework (connectors, DQ library, fixtures, `pytest.ini`, `requirements.txt`) must already exist.
- Refuse requests to generate or modify base framework code, `conftest.py`, `Jenkinsfile`, or `data_dev` pipeline code.

## Inputs you must have

- Target dataset name (matching the folder name under `/parquet_data/`).
- Dataset definition and column mapping from `docs/parquet-aggregated-data-mapping.md`.
- Author / ticket id for the test module header.
- If mapping is missing or unclear, stop and request the mapping details from the user.
- **Forbidden sources:** Never read, extract, or copy queries from `data_dev/` (such as `queries.py` or parquet loader SQL).

## Hard rules

1. **Path:** Test module must be placed at `PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`.
2. **One dataset per module:** Exactly one test file per dataset. Do not combine multiple datasets into a single file.
3. **Source vs Target:** Source is PostgreSQL (`db_connection.get_data_sql(...)`); Target is Parquet (`parquet_reader.process(...)`). Never swap them.
4. **Mapping-only SQL:** Expected SQL must be derived solely from `docs/parquet-aggregated-data-mapping.md`.
5. **No dataset SQL in SKILL.md:** This skill file must remain dataset-agnostic and contain no hardcoded queries for specific datasets.
6. **No pipeline artifacts in SQL:** Do not add `UNION`, sign inversions, or extra `WHERE` clauses unless specified in the mapping.
7. **Library methods only:** Test bodies must delegate directly to `data_quality_library` methods. Do not write raw pandas assertions inside test functions.
8. **Markers:** Apply `@pytest.mark.parquet_data`, `@pytest.mark.<dataset_name>`, and mark only `test_check_dataset_is_not_empty` with `@pytest.mark.smoke`.
9. **Not-null columns:** Must validate all mapped output columns for the dataset.

## Workflow

1. Read the target dataset's specification in `docs/parquet-aggregated-data-mapping.md`.
2. Identify source 3NF tables, foreign key joins, grouping dimensions (grain), and aggregation functions (measures).
3. Formulate the clean PostgreSQL expected query matching the mapping columns and grain.
4. Generate the test file using the standard module skeleton.
5. Populate fixtures, markers, dataset target paths (`/parquet_data/<dataset_name>`), and the not-null column list.

## Template

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): TICKET-1234
Author(s): <name>
"""

import pytest


@pytest.fixture(scope='module')
def source_data(db_connection):
    source_query = """
    -- expected query derived from mapping (grain + measures + joins)
    """
    return db_connection.get_data_sql(source_query)


@pytest.fixture(scope='module')
def target_data(parquet_reader):
    target_path = '/parquet_data/<dataset_name>'
    return parquet_reader.process(target_path, include_subfolders=True)


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.<dataset_name>
def test_check_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_data_completeness(source_data, target_data, data_quality_library):
    data_quality_library.check_data_completeness(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_count(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_uniqueness(target_data, data_quality_library):
    data_quality_library.check_duplicates(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(target_data, ['<col_1>', '<col_2>', '<col_3>'])```

## SQL derivation (generic)

1. **Source Tables and Joins:** Identify core 3NF tables referenced in the mapping (e.g., `visits`, `facilities`, `patients`) and establish joins using primary/foreign key relationships (e.g., `visits.facility_id = facilities.facility_id`).
2. **Grain and GROUP BY:** Place all grouping columns designated in the mapping into both the `SELECT` and `GROUP BY` clauses.
3. **Dates:** Extract or cast date fields as specified (e.g., `DATE(visit_timestamp) AS visit_date`).
4. **Names and Strings:** Apply required string concatenation or formatting (e.g., `CONCAT(first_name, ' ', last_name) AS full_name`).
5. **Aggregates and Measures:** Apply aggregation functions (`MIN`, `AVG`, `SUM`, etc.) with necessary precision/rounding (e.g., `ROUND(AVG(...)::numeric, 2)`) and alias each measure to match the target column name in the mapping.
6. **Filters:** Only include `WHERE` filters if explicitly defined in the data mapping document. Do not invent filters or borrow them from ETL pipelines.

## After generation

- Execute pytest against the target environment using `-m "parquet_data"`.
- If test assertions fail, record and report the discrepancies as transformation or data defects.
- **Never** rewrite or tweak the expected SQL query to force a green test run if the query accurately reflects the mapping requirements.

---

## Skill review (self-check before Step 3)

Confirm all boxes pass before generating dataset test modules:

- [x] Does not contain concrete expected SQL for `facility_name_min_time_spent_per_visit_date`, `facility_type_avg_time_spent_per_visit_date`, or `patient_sum_treatment_cost_per_facility_type`
- [x] Does not instruct to use `data_dev/` or parquet loader SQL
- [x] Includes completeness, count, uniqueness, and not-null checks
- [x] Uses correct fixture directions (Postgres = source, Parquet = target) and realistic DQ assertions
- [x] All `TODO` placeholders are removed
