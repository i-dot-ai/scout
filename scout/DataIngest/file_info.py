import os

import instructor
from instructor.exceptions import InstructorRetryException
from openai import AzureOpenAI

from scout.DataIngest.models.schemas import ChunkCreate, File, FileInfo, FileUpdate
from scout.DataIngest.prompts import FILE_INFO_EXTRACTOR_SYSTEM_PROMPT
from scout.utils.storage.storage_handler import BaseStorageHandler

from scout.utils.utils import logger


def get_text_from_chunks(chunks: list[ChunkCreate], num_chunks: int):
    chunks = [chunk.text for chunk in chunks[:num_chunks]]
    text = " ".join(chunks)
    return text


def get_llm_file_info(project_name: str, file_name: str, text: str) -> FileInfo:
    """
    For a given file and text, get LLM generated metadata on file (FileInfo) e.g. name, summary.
    If LLM generated info fails - return blank FileInfo.
    """
    client = instructor.from_openai(
        AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        )
    )
    # Create prompt that will be used to generate file info
    sys_prompt = FILE_INFO_EXTRACTOR_SYSTEM_PROMPT.format(project_name=project_name, file_name=file_name)

    # Extract structured metadata for file from natural language using cheaper LLM
    try:
        file_info = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            response_model=FileInfo,
            messages=[
                {
                    "role": "system",
                    "content": sys_prompt,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            max_retries=3,
        )
    except InstructorRetryException as e:
        # Assumption that blank info is fine if we can't generate with LLM
        file_info = FileInfo()
        logger.error(f"{e} unable to get LLM generated file info for {file_name}, proceeding without...")

    logger.info("File info generated")
    return file_info


def get_file_update(file: File, file_info: FileInfo) -> FileUpdate:
    # Pre-populate a FileUpdate object with the details from File object
    file_update = FileUpdate(
        type=file.type,
        name=file.name,
        s3_bucket=getattr(file, "s3_bucket", None),
        s3_key=getattr(file, "s3_key", None),
        storage_kind=getattr(file, "storage_kind", "local"),
        project=getattr(file, "project", None),
        chunks=getattr(file, "chunks", []),
        id=file.id,
    )
    # Add the updated file info to update file - there is a chance that
    file_update.clean_name = file_info.clean_name
    file_update.source = file_info.source.value if file_info.source else None
    file_update.summary = file_info.summary
    file_update.published_date = file_info.published_date
    return file_update


def add_llm_generated_file_info(
    project_name: str, file: File, chunks_from_file: list[ChunkCreate], storage_handler: BaseStorageHandler
) -> File:
    text = get_text_from_chunks(chunks=chunks_from_file, num_chunks=20)
    llm_generated_file_info = get_llm_file_info(project_name=project_name, file_name=file.name, text=text)
    file_update = get_file_update(file=file, file_info=llm_generated_file_info)
    updated_file = storage_handler.update_item(file_update)
    return updated_file
