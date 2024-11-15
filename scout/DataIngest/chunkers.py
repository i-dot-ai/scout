import tempfile
from pathlib import Path
from typing import List, Optional

import requests
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

from scout.DataIngest.anonymizer import Anonymizer
from scout.DataIngest.models.schemas import ChunkCreate, File
from scout.utils.utils import logger


def download_to_tempfile(presigned_url: str, suffix: Optional[str] = None) -> Path:
    """
    Downloads content from a presigned URL to a temporary file.

    Args:
        presigned_url (str): The presigned URL to download from
        suffix (Optional[str]): Optional suffix for the temp file (e.g. '.pdf', '.zip')

    Returns:
        Path: Path to the temporary file

    Raises:
        requests.RequestException: If the download fails
    """
    # Create a temporary file that will be automatically cleaned up
    logger.info(f"Creating tempfile with suffix: {suffix}")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    logger.info(f"Tempfile created: {temp_file.name}")
    try:
        # Stream the download to avoid loading entire file into memory
        with requests.get(presigned_url, stream=True) as response:
            response.raise_for_status()

            # Write the content to the temporary file in chunks
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

        logger.info(f"Tempfile written to: {temp_file.name}")
        temp_file.close()
        return Path(temp_file.name)

    except requests.RequestException as e:
        # Clean up the temp file if download fails
        temp_file.close()
        logger.info(f"Tempfile closed with exception: {e}")
        Path(temp_file.name).unlink(missing_ok=True)
        raise e


def process_chunks(file: File, raw_chunks: list[Element]) -> list[ChunkCreate]:
    chunks = []
    for i, raw_chunk in enumerate(raw_chunks):
        raw_chunk = raw_chunk.to_dict()

        if "page_number" in raw_chunk["metadata"]:
            if isinstance(raw_chunk["metadata"]["page_number"], int):
                raw_chunk["metadata"]["page_numbers"] = raw_chunk["metadata"]["page_number"]
            elif isinstance(raw_chunk["metadata"]["page_number"], list):
                raw_chunk["metadata"]["page_numbers"] = raw_chunk["metadata"]["page_number"][0]
        else:
            raw_chunk["metadata"]["page_numbers"] = 0

        logger.info(f"file: {file}, type: {type(file)}")
        chunk = ChunkCreate(
            file=file,
            idx=i,
            text=raw_chunk["text"],
            page_num=raw_chunk["metadata"]["page_numbers"],
        )
        chunks.append(chunk)
    return chunks


def partition_and_chunk_file(
    file: File,
    temp_filepath: str,
    chunking_strategy: str,
    anonymise: bool = False,
) -> List[ChunkCreate]:
    # Chunking strategy options: https://docs.unstructured.io/open-source/core-functionality/partitioning#partition
    anonymizer = Anonymizer()
    logger.info(f"Partitioning file from temp file path: {temp_filepath}")
    elements = partition(filename=temp_filepath, strategy=chunking_strategy)
    logger.info(f"Finished Partitioning file: {elements}")

    logger.info(f"Chunking file by title: {elements}")
    raw_chunks = chunk_by_title(elements=elements, max_characters=2000, new_after_n_chars=1750)
    logger.info(f"Finished Chunking file by title: {raw_chunks}")

    if anonymise:
        logger.info("Anonymizing chunks")
        for raw_chunk in raw_chunks:
            raw_chunk.text = anonymizer.anonymize(raw_chunk.text).text
        logger.info("Finished Anonymizing chunks")

    logger.info(f"Processing chunks by title: {raw_chunks}")
    chunks = process_chunks(file=file, raw_chunks=raw_chunks)
    logger.info(f"Finished Processing chunks by title: {chunks}")

    temp_filepath.unlink(missing_ok=True)
    return chunks


def add_chunks_to_vector_store(chunks: List[ChunkCreate], project_id, vector_store) -> None:
    """Takes a list of Chunks and embeds them into the vector store

    Args:
        chunks (List[Chunk]): The chunks to be added to the vector store
    """
    batch_size = 160
    for i in range(0, len(chunks), batch_size):
        vector_store.add_texts(
            texts=[chunk.text for chunk in chunks[i : i + batch_size]],
            metadatas=[
                {
                    "uuid": str(chunk.id),
                    "project": str(project_id),
                    "parent_doc_uuid": str(chunk.file.id),
                    "page_num": chunk.page_num,
                }
                for chunk in chunks[i : i + batch_size]
            ],
            ids=[str(chunk.id) for chunk in chunks[i : i + batch_size]],
        )


def chunk_file(file: File, temp_filepath: Path, chunking_strategy: str, anonymise=False) -> List[ChunkCreate]:
    # Chunking strategy options: https://docs.unstructured.io/open-source/core-functionality/partitioning#partition
    if file.type != ".pdf":
        raise ValueError(f"File type {file.type} of {file.name} is not supported - must be PDF.")
    chunks = partition_and_chunk_file(file, temp_filepath, anonymise=anonymise, chunking_strategy=chunking_strategy)
    return chunks
