from unittest.mock import patch

from langchain_core.vectorstores import VectorStore
from openai import AzureOpenAI

from scout.DataIngest.models.schemas import CriterionGate
from scout.Pipelines.generate_llm_flags import generate_llm_flags_for_project
from scout.Pipelines.ingest_criteria import ingest_criteria_from_local_dir
from scout.Pipelines.ingest_project_data import ingest_project_files
from scout.utils.storage.filesystem import S3StorageHandler
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler

from .utils import check_table_rows, mock_get_project_directory


@patch("scout.Pipelines.ingest_project_data.get_project_directory", mock_get_project_directory)
def test_llm_flag_one_project(
    project_directory_name: str,
    example_vector_store: VectorStore,
    criteria_csv_list: list[str],
    connection_string: str,
    llm: AzureOpenAI,
) -> None:
    storage_handler = PostgresStorageHandler()
    s3_storage_handler = S3StorageHandler()
    # TODO: We use the create db test to set up the project - these should be made standalone tests eventually.
    ingest_criteria_from_local_dir(
        gate_filepaths=criteria_csv_list,
        storage_handler=storage_handler,
    )
    project_name = ingest_project_files(
        project_directory_name=project_directory_name,
        vector_store=example_vector_store,
        storage_handler=storage_handler,
        s3_storage_handler=s3_storage_handler,
    )
    pre_flag_counts = {"project": 1, "file": 3, "chunk": 3, "criterion": 5, "user": 1}

    gate_review = CriterionGate.GATE_2
    generate_llm_flags_for_project(
        project_name=project_name,
        storage_handler=storage_handler,
        llm=llm,
        vector_store=example_vector_store,
        gate_review=gate_review,
    )
    # We should expect the same number of rows as in the create db test.
    # We should now expect 3 new rows in the results table from LLM flag.
    expected_counts = {**pre_flag_counts, "result": 3}
    check_table_rows(connection_string, expected_counts=expected_counts)
