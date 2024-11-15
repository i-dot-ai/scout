from typing import Dict, List, Tuple
from unittest.mock import patch

from dotenv import load_dotenv
from langchain_core.vectorstores import VectorStore
from sqlalchemy import create_engine, text

from scout.Pipelines.ingest_criteria import ingest_criteria_from_local_dir
from scout.Pipelines.ingest_project_data import ingest_project_files
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler

from .utils import mock_get_project_directory

load_dotenv()


def check_table_rows(connection_string: str, expected_counts: Dict[str, int]) -> List[Tuple[str, bool, int, int]]:
    """
    Check if tables have the expected number of rows within a threshold.

    Args:
        connection_string: Database connection string
        expected_counts: Dictionary mapping table names to their expected row counts

    Returns:
        List of tuples: (table_name, passed_check, actual_count, expected_count)
    """
    engine = create_engine(connection_string)
    results = []

    with engine.connect() as conn:
        for table_name, expected_count in expected_counts.items():
            try:
                # Get actual row count
                actual_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

                # Check if count is correct
                passed = actual_count == expected_count

                results.append((table_name, passed, actual_count, expected_count))

                # Print result
                status = "PASSED" if passed else "FAILED"
                print(f"{table_name}: {status} (Expected: {expected_count}, Actual: {actual_count})")

            except Exception as e:
                print(f"Error checking {table_name}: {str(e)}")
                results.append((table_name, False, -1, expected_count))

    # Print summary
    passed_count = sum(1 for r in results if r[1])
    print(f"\nTotal passed: {passed_count}/{len(results)} checks")

    return results


@patch("scout.Pipelines.ingest_project_data.get_project_directory", mock_get_project_directory)
def test_create_db_from_local_dir(
    project_directory_name: str,
    example_vector_store: VectorStore,
    criteria_csv_list: List[str],
    connection_string: str,
    expected_counts: Dict[str, int] = {"project": 1, "file": 3, "chunk": 3, "criterion": 5, "user": 1},
) -> str:
    """Chunks files and check DB populated."""
    storage_handler = PostgresStorageHandler()
    # Make sure DB is empty
    expected_counts_at_start = {"project": 0, "file": 0, "chunk": 0, "criterion": 0, "user": 1}
    results = check_table_rows(connection_string, expected_counts_at_start)
    for result in results:
        assert result[1], "Database should be empty at start"

    # Ingest criteria
    ingest_criteria_from_local_dir(
        gate_filepaths=criteria_csv_list,
        storage_handler=storage_handler,
    )

    # Ingest project_files
    output_project_name = ingest_project_files(
        project_directory_name, vector_store=example_vector_store, storage_handler=storage_handler
    )

    table_rows = check_table_rows(connection_string, expected_counts)
    assert all(result[1] for result in table_rows), table_rows  # "Database should be populated"
    return output_project_name
