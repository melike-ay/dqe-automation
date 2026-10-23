import sys
import os
import pytest

# Ensure the framework root is in Python's path so imports from 'src' always resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.connectors.postgres.postgres_connector import PostgresConnectorContextManager
from src.data_quality.data_quality_validation_library import DataQualityLibrary
from src.connectors.file_system.parquet_reader import ParquetReader


def pytest_addoption(parser):
    """
    Defines custom CLI options for database connection parameters.
    """
    parser.addoption("--db_host", action="store", default="localhost", help="Database host (default: localhost)")
    parser.addoption("--db_port", action="store", default="5434", help="Database port (default: 5434)")
    parser.addoption("--db_name", action="store", default="mydatabase", help="Database name (default: mydatabase)")
    parser.addoption("--db_user", action="store", default=None, help="Database username (required)")
    parser.addoption("--db_password", action="store", default=None, help="Database password (required)")


def pytest_configure(config):
    """
    Validates that required database options are provided before running tests.
    Avoids failing during --help or marker discovery.
    """
    if config.option.help:
        return

    required_options = ["--db_user", "--db_password"]
    for option in required_options:
        if not config.getoption(option):
            pytest.exit(f"Missing required command-line option: {option}", returncode=1)


@pytest.fixture(scope="session")
def db_connection(request):
    """
    Session-scoped fixture providing a PostgreSQL database connector context.
    """
    db_host = request.config.getoption("--db_host")
    db_port = request.config.getoption("--db_port")
    db_name = request.config.getoption("--db_name")
    db_user = request.config.getoption("--db_user")
    db_password = request.config.getoption("--db_password")

    try:
        with PostgresConnectorContextManager(
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_name=db_name,
            db_port=db_port,
        ) as db_connector:
            yield db_connector
    except Exception as e:
        pytest.fail(f"Failed to initialize PostgresConnectorContextManager: {e}")


@pytest.fixture(scope="session")
def parquet_reader():
    """
    Session-scoped fixture providing an instance of ParquetReader.
    """
    try:
        reader = ParquetReader()
        yield reader
    except Exception as e:
        pytest.fail(f"Failed to initialize ParquetReader: {e}")


@pytest.fixture(scope="session")
def data_quality_library():
    """
    Session-scoped fixture providing an instance of DataQualityLibrary.
    """
    try:
        dq_lib = DataQualityLibrary()
        yield dq_lib
    except Exception as e:
        pytest.fail(f"Failed to initialize DataQualityLibrary: {e}")