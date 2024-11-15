import os
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings


def get_or_create_vector_store(vector_store_directory: Path):
    embedding_function = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment="text-embedding-3-large",
    )

    vector_store = Chroma(
        embedding_function=embedding_function,
        persist_directory=str(vector_store_directory),
        collection_metadata={
            "hnsw:M": 2048,
            "hnsw:search_ef": 20,
        },  # included to avoid M too small error on retrival
    )
    return vector_store
