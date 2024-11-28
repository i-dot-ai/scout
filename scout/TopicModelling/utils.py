
import os

from bertopic.backend import OpenAIBackend
from bertopic.representation import KeyBERTInspired
from bertopic.representation import OpenAI
from bertopic.vectorizers import ClassTfidfTransformer
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from scout.DataIngest.models.schemas import ProjectFilter
from scout.DataIngest.models.schemas import ChunkFilter
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.TopicModelling.representation_prompts import summarization_prompt, primary_theme_prompt

def load_topic_chunks(project_name: str, storage_handler: PostgresStorageHandler):
    """ Load topic chunks for modelling
    
    
    """

    filter = ProjectFilter(name=project_name)
    project = storage_handler.get_item_by_attribute(filter)

    # Get chunks
    chunk_filter = [ChunkFilter(file=file) for file in project[0].files]
    chunks = [storage_handler.get_item_by_attribute(file) for file in chunk_filter]
    chunks = [chunk for file in chunks for chunk in file]

    return chunks

def generate_default_stack(embedding_model, embedding_client, representation_llm):
    """Build the BERTStack for the model. This can be refactored to be customised ast a later date
    Effectively, the process is:
    1. Select the embedding model (based on the one used in the chunker)
    2. Dimensionality reduction
    3. Clustering
    4. Tokenizer
    5. ctfidf Topic Representation
    6. Representation model
    """

    embedding_model = OpenAIBackend(
        embedding_client, embedding_model, batch_size=500, delay_in_seconds=0.5
    )  # Select open ai model change as appropriate

    umap_model = UMAP(
        n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=336
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=15,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 3))
    ctfidf_model = ClassTfidfTransformer(
        bm25_weighting=True, reduce_frequent_words=True
    )

    baseline_representation_model = KeyBERTInspired()
    # openai_representation_model = select_representation_model('openai')

    representation_model = {
        "Main": baseline_representation_model,
        # "summary": baseline_representation_model,
        # "Primary theme": baseline_representation_model
        "openai": OpenAI(
            representation_llm,
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            chat=True,
            exponential_backoff=True,
        ),
        "summary": OpenAI(
            representation_llm,
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            chat=True,
            exponential_backoff=True,
            prompt=summarization_prompt,  # noqa: F405 - summarization_prompt may be undefined
            nr_docs=20,
        ),
        "Primary theme": OpenAI(
            representation_llm,
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            chat=True,
            exponential_backoff=True,
            prompt=primary_theme_prompt,  # noqa: F405 - primary_theme_prompt may be undefined
            nr_docs=5,
        ),
    }

    model_stack = {
        "embedding_model": embedding_model,  # Step 1 - Extract embeddings
        "umap_model": umap_model,  # Step 2 - Reduce dimensionality
        "hdbscan_model": hdbscan_model,  # Step 3 - Cluster reduced embeddings
        "vectorizer_model": vectorizer_model,  # Step 4 - Tokenize topics
        "ctfidf_model": ctfidf_model,  # Step 5 - Extract topic words
        "representation_model": representation_model,  # Step 6 - (Optional) Fine-tune topic represenations
    }

    return model_stack

def save_outputs(topic_model, storage_handler, evaluation_metrics=None):
    # Extract information from topic model
    topic_outputs = topic_model.outputs()

    try:
        print("Adding topics")
        topics = storage_handler.write_items(topic_outputs)  # Save topics
    except Exception as _:
        print("Failed to add topics")

    return None