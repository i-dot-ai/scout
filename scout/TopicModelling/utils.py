

from scout.DataIngest.models.schemas import ProjectFilter
from scout.DataIngest.models.schemas import ChunkFilter
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler

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