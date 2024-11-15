import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import create_engine, text

from scout.utils.storage.filesystem import S3StorageHandler


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


def assert_dir_exists(dir_name: str) -> None:
    assert os.path.exists(dir_name), f"Local directory {dir_name} does not exist"


def assert_folder_empty(dir_name: str) -> None:
    assert len(os.listdir(dir_name)) == 0, f"Local directory {dir_name} is not empty"


def assert_s3_dir_not_empty(test_data_dir: str) -> None:
    """
    Tests if a given s3 directory is not empty.
    """
    s3_storage_handler = S3StorageHandler()
    assert s3_storage_handler.list_all_items(test_data_dir) != [], "S3 directory is empty"


def assert_files_exist_in_local_dir(test_data_dir: str) -> None:
    """
    Tests if a given local directory is not empty and contains at least one file with an allowed extension.
    """
    assert os.listdir(test_data_dir) != [], "Local directory is empty"

    file_extensions = set(file.split(".")[-1] for file in os.listdir(test_data_dir))
    required_extensions = set(["pdf", "docx", "doc", "ppt", "pptx"])

    # Check if there's any overlap between the file extensions and required extensions
    assert not file_extensions.isdisjoint(
        required_extensions
    ), f"Local directory must contain at least one file with extension: {required_extensions}. Found files with extensions: {file_extensions}"


def reset_postgres_db() -> None:
    """Reset postgres database to empty state"""
    os.system("make reset-local-db")


def delete_local_vector_store(project_directory: Path) -> None:
    """Delete local vector store if exists"""
    vector_store_dir = project_directory / "VectorStore"
    if vector_store_dir.exists() and vector_store_dir.is_dir():
        shutil.rmtree(vector_store_dir)


def mock_get_project_directory(project_directory_name: str):
    # Read from `example_data` for tests not `.data`
    return Path("example_data") / Path(project_directory_name)
