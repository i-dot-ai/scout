import os
from pathlib import Path

import pytest
from langchain_core.vectorstores import VectorStore
from openai import AzureOpenAI

from scout.Pipelines.utils import get_or_create_vector_store

from .utils import delete_local_vector_store, reset_postgres_db

# For the tests, read from the example data directory
# For actual running of pipeline, use `.data` folder


@pytest.fixture
def project_directory_name():
    # This is currently hardcoded.
    return "example_project"


@pytest.fixture
def project_directory():
    return Path("example_data") / Path("example_project")


@pytest.fixture
def example_vector_store(project_directory) -> VectorStore:
    vector_store_path = project_directory / Path("VectorStore")
    vector_store_path.mkdir(parents=True, exist_ok=True)
    vector_store = get_or_create_vector_store(vector_store_path)
    return vector_store


def pytest_addoption(parser):
    parser.addoption(
        "--reset-db",
        action="store",
        nargs="*",  # allows multiple arguments
        default=[],
        help="Reset specified databases before running tests can be <all>, <postgres> and or <vector_store>",
    )


@pytest.fixture(autouse=True)
def reset_database(request, project_directory: Path):
    dbs_to_reset = request.config.getoption("--reset-db")
    if dbs_to_reset:
        for db in dbs_to_reset:
            print(f"Resetting {db} database...")
            if db == "postgres":
                reset_postgres_db()
            elif db == "vector_store":
                delete_local_vector_store(project_directory)
            elif db == "all":
                reset_postgres_db()
                delete_local_vector_store(project_directory)
            else:
                raise ValueError(f"Unknown database: {db}")


@pytest.fixture
def llm():
    llm = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    )
    return llm


@pytest.fixture
def criteria_csv_list():
    return ["example_data/criteria/example_2.csv", "example_data/criteria/example_3.csv"]


@pytest.fixture
def connection_string():
    return "postgresql://postgres:insecure@localhost:5432/ipa-scout"  # pragma: allowlist secret
