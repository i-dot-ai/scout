import os
from pathlib import Path
from typing import List, Tuple

from langchain_core.vectorstores import VectorStore

from scout.DataIngest.chunkers import add_chunks_to_vector_store, chunk_file, download_to_tempfile
from scout.DataIngest.file_info import add_llm_generated_file_info
from scout.DataIngest.models.schemas import Chunk, File, FileCreate, Project, ProjectCreate
from scout.DataIngest.s3_download import convert_to_pdf_from_s3, s3_key_from_presigned_url
from scout.DataIngest.utils import get_project_directory, get_project_name_with_date_time, sanitise_project_name
from scout.utils.storage.filesystem import S3StorageHandler
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.utils.storage.storage_handler import BaseStorageHandler
from scout.utils.utils import logger


def create_file_from_presigned_url(
    presigned_url: str, project: Project, s3_storage_handler: S3StorageHandler, storage_handler: PostgresStorageHandler
) -> File:
    s3_key = s3_key_from_presigned_url(presigned_url)
    logger.info(f"Saving file with S3 key: {s3_key}")
    file_name = s3_key.split("/")[-1]  # Get the last part of the path
    logger.info(f"File name: {file_name}")
    file_create = FileCreate(
        name=file_name,
        s3_key=s3_key,
        type=os.path.splitext(file_name)[1],
        project=project,
        s3_bucket=s3_storage_handler.bucket_name,
    )
    file = storage_handler.write_item(file_create)
    return file


def save_files_to_db_and_temp(
    presigned_urls: List[str],
    project: Project,
    s3_storage_handler: S3StorageHandler,
    storage_handler: PostgresStorageHandler,
) -> List[Tuple[File, Path]]:
    """Saves files at the presigned URLs to the database and to a temp folder."""
    created_files = [
        create_file_from_presigned_url(
            url, project=project, s3_storage_handler=s3_storage_handler, storage_handler=storage_handler
        )
        for url in presigned_urls
    ]
    temp_filepaths = [download_to_tempfile(url) for url in presigned_urls]
    return zip(created_files, temp_filepaths)


def chunk_embed_save_from_temp_filepath(
    file: File,
    temp_filepath: Path,
    storage_handler: PostgresStorageHandler,
    project: Project,
    vector_store: VectorStore,
    chunking_strategy: str,
):
    assert file.type == ".pdf"
    try:
        logger.info(f"Trying to Chunk file: {file.name}")
        chunks = chunk_file(file=file, temp_filepath=temp_filepath, anonymise=True, chunking_strategy=chunking_strategy)
        new_chunks: List[Chunk] = storage_handler.write_items(chunks)
        for i, new_chunk in enumerate(new_chunks):
            new_chunk.file = chunks[i].file
        chunks = new_chunks
    except FileNotFoundError as e:
        logger.error(e)

    # Now we can create LLM file attributes. This uses instructor and the file_info_extractor prompt.
    add_llm_generated_file_info(
        project_name=project.name, file=file, chunks_from_file=chunks, storage_handler=storage_handler
    )
    add_chunks_to_vector_store(chunks=chunks, vector_store=vector_store, project_id=project.id)


def ingest_project_files(
    project_directory_name: str,
    vector_store: VectorStore,
    storage_handler: BaseStorageHandler = PostgresStorageHandler(),
    s3_storage_handler: S3StorageHandler = S3StorageHandler(),
    chunking_partition_strategy: str = "fast",
) -> str:
    """
    Ingest all project files in a given folder. This converts files to PDF, uploads to S3 storage,
    chunks the text content of files and saves info to a Postgres database and a vector store
    (for chunks).

    Args:
        project_directory_name: name of folder where the project files are saved (within .data folder)
        vector_store: for embedding file chunks
        storage_handler: for saving to database
        s3_storage_handler: for saving to S3
        strategy: one of ["auto", "hi_res", "fast" and "ocr_only"] as in
            https://docs.unstructured.io/open-source/core-functionality/partitioning#partition

    Returns:
        Project name (as string)
    """
    project_name = get_project_name_with_date_time(project_directory_name)
    print(f"project_name: {project_name}")
    project_folder_path = get_project_directory(project_directory_name)
    print(f"project_folder_path: {project_folder_path}")

    # Create project in DB
    project = ProjectCreate(name=project_name)
    project = storage_handler.write_item(project)

    # Upload files to s3
    s3_file_keys = s3_storage_handler.upload_folder_contents(
        str(project_folder_path),
        recursive=True,
        prefix=sanitise_project_name(project.name) + "/raw/",
    )
    logger.info(f"Uploaded {s3_file_keys} files to s3")

    # send files to libreoffice service and convert to pdf.
    logger.info(f"Converting {s3_file_keys} files to pdf")
    s3_converted_file_keys = convert_to_pdf_from_s3(s3_file_keys)
    logger.info(f"Converted {s3_converted_file_keys} files to pdf")

    # Get presigned urls for these files - save file info to DB and files to temp for chunking
    presigned_urls = s3_storage_handler.presigned_url_list(sanitise_project_name(project.name) + "/processed/")
    files_to_chunk = save_files_to_db_and_temp(
        presigned_urls=presigned_urls,
        project=project,
        s3_storage_handler=s3_storage_handler,
        storage_handler=storage_handler,
    )

    # Chunks, embed and save file metadata to DB and vector store from temp files
    logger.info("Chunking and embedding files")
    for file, temp_filepath in files_to_chunk:
        chunk_embed_save_from_temp_filepath(
            file=file,
            temp_filepath=temp_filepath,
            storage_handler=storage_handler,
            project=project,
            vector_store=vector_store,
            chunking_strategy=chunking_partition_strategy,
        )

    # Project name is useful for checks
    return project.name
