"""
This script run the topic modelling pipeline for scout.
It take a selection of data from the database and runs a BERTopic pipeline.

"""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI

from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.TopicModelling.utils import load_topic_chunks
from scout.TopicModelling.utils import generate_default_stack
from scout.TopicModelling.utils import save_outputs
from scout.TopicModelling.topic_model import TopicModel
from scout.TopicModelling.models import TopicModelSpecCreate as TopicModelSpec

load_dotenv()

if __name__ == "__main__":

    project_name = "example_project" # Too add - All handler
    
    representation_llm = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    )  # Chosen LLM for evaluation of project against the criteria

    embedding_client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    ) # Sets up the embedder to embed the chunks for topic modelling

    embedding_model = "text-embedding-3-large"

    storage_handler = PostgresStorageHandler()

    topic_chunks = load_topic_chunks(project_name, storage_handler)

    # Initialise topic model
    model_name = str(project_name) + "_topics"
    t_model = TopicModel(
        chunks=topic_chunks,
        model_name=model_name
    )

    t_model.embedd_chunks(embedding_client, embedding_model=embedding_model)

    # Build stack
    bert_stack = generate_default_stack(embedding_model, embedding_client, representation_llm)

    # Hyperparameters - tune to specific case 
    model_parameters = {
        "min_topic_size": 10,
        "calculate_probabilities": True,
        "verbose": True,
    }

    t_model.create_model(params=model_parameters, bert_stack=bert_stack)

    print("Training model...")
    t_model.fit()

    # CReate project to save here
    t_model.model_spec = TopicModelSpec(
        name=t_model.model_name,
        num_docs=t_model.result.get("num_docs"),
        computation_time=t_model.result.get("computation_time"),
        num_topics=t_model.result.get("num_topics"),
    )
    t_model.model_spec = storage_handler.write_item(t_model.model_spec)

    print("Saving outputs...")
    save_outputs(t_model, storage_handler)
