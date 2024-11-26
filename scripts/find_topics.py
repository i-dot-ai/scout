"""
This script run the topic modelling pipeline for scout.
It take a selection of data from the database and runs a BERTopic pipeline.

"""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI

from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.TopicModelling.utils import load_topic_chunks

load_dotenv()

if __name__ == "__main__":

    project_name = "example_project"

    storage_handler = PostgresStorageHandler()

    topic_chunks = load_topic_chunks(project_name, storage_handler)