"""
This script run the topic modelling pipeline for scout.
It take a selection of data from the database and runs a BERTopic pipeline.

"""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings

from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.TopicModelling.utils import load_topic_chunks
from scout.TopicModelling.utils import generate_default_stack
from scout.TopicModelling.topic_model import TopicModel

load_dotenv()

if __name__ == "__main__":

    project_name = "example_project" # Too add - All handler
    
    representation_llm = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    )  # Chosen LLM for evaluation of project against the criteria

    chunk_embedder = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment="text-embedding-3-large",
    ) # Sets up the embedder to embed the chunks for topic modelling

    storage_handler = PostgresStorageHandler()

    topic_chunks = load_topic_chunks(project_name, storage_handler)

    # Initialise topic model
    model_name = str(project_name) + "_topics"
    t_model = TopicModel(
        chunks=topic_chunks,
        model_name=model_name
    )

    t_model.embedd_chunks(chunk_embedder)

    # Build stack
    bert_stack = generate_default_stack()
