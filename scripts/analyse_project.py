"""
This script ingests documents for a project (documents in varied formats e.g. PDF, PPT, DOC)
and then evaluates them against specified criteria using an LLM.

This data is saved to a Postgres database, and can then be viewed in the frontend.

See the project README for instructions on how to run.
"""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI

from scout.DataIngest.models.schemas import CriterionGate
from scout.DataIngest.utils import get_vector_store_directory
from scout.Pipelines.generate_llm_flags import generate_llm_flags_for_project
from scout.Pipelines.ingest_criteria import ingest_criteria_from_local_dir
from scout.Pipelines.ingest_project_data import ingest_project_files
from scout.Pipelines.utils import get_or_create_vector_store
from scout.utils.storage.filesystem import S3StorageHandler
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.utils.utils import logger

load_dotenv()


if __name__ == "__main__":
    # These are your settings
    project_directory_name = "example_project"  # Folder in `.data` with project files
    gate_review = CriterionGate.GATE_3  # Criteria to review against
    criteria_csv_list = [
        ".data/criteria/example_2.csv",
        ".data/criteria/example_3.csv",
    ]
    llm = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    )  # Chosen LLM for evaluation of project against the criteria

    # Define data stores: Postgres database, vector store, S3 bucket for files
    storage_handler = PostgresStorageHandler()
    vector_store_directory = get_vector_store_directory(project_directory_name)
    vector_store = get_or_create_vector_store(vector_store_directory)
    s3_storage_handler = S3StorageHandler()

    # Ingest project data - convert to PDF and chunk
    project_name = ingest_project_files(
        project_directory_name=project_directory_name,
        vector_store=vector_store,
        storage_handler=storage_handler,
        s3_storage_handler=s3_storage_handler,
    )
    logger.info(f"Ingested project files for {project_name}")

    # Ingest criteria CSVs
    ingest_criteria_from_local_dir(gate_filepaths=criteria_csv_list, storage_handler=storage_handler)
    logger.info("Criteria ingested")

    # Now evaluate projects against specified criteria and gate
    generate_llm_flags_for_project(
        project_name=project_name,
        storage_handler=storage_handler,
        llm=llm,
        vector_store=vector_store,
        gate_review=gate_review,
    )
    logger.info("Finished LLM evaluation")
