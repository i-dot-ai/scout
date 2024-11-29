from typing import List
from uuid import UUID

from scout.TopicModelling.models import Topic as PyTopic
from scout.TopicModelling.models import TopicCreate
from scout.TopicModelling.models import TopicFilter
from scout.TopicModelling.models import TopicUpdate
from scout.TopicModelling.models import TopicModelSpec as PyTopicModelSpec
from scout.TopicModelling.models import TopicModelSpecCreate
from scout.TopicModelling.models import TopicModelSpecFilter
from scout.TopicModelling.models import TopicModelSpecUpdate
from scout.TopicModelling.models import ChunkTopicJoin as PyChunkTopicJoin
from scout.TopicModelling.models import ChunkTopicJoinCreate
from scout.TopicModelling.models import ChunkTopicJoinFilter
from scout.TopicModelling.models import ChunkTopicJoinUpdate

from scout.TopicModelling.storage.postgres_interface import delete_item
from scout.TopicModelling.storage.postgres_interface import filter_items
from scout.TopicModelling.storage.postgres_interface import get_all
from scout.TopicModelling.storage.postgres_interface import get_by_id
from scout.TopicModelling.storage.postgres_interface import get_or_create_item
from scout.TopicModelling.storage.postgres_interface import update_item

from scout.TopicModelling.storage.postgres_models import Topic as SqTopic
from scout.TopicModelling.storage.postgres_models import TopicModelSpec as SqTopicModelSpec
from scout.TopicModelling.storage.postgres_models import ChunkTopicJoin as SqChunkTopicJoin

from scout.utils.storage.storage_handler import BaseStorageHandler

class TopicStorageHandelr(BaseStorageHandler):
    def __init__(self):
        super().__init__()
    
    def write_item(
            self, 
            model: TopicCreate | TopicModelSpecCreate | ChunkTopicJoinCreate,
        ) -> PyTopic | PyTopicModelSpec | PyChunkTopicJoin:
        return super().write_item(model)
    
    def write_items(
        self,
        models: List[TopicCreate | TopicModelSpecCreate | ChunkTopicJoinCreate],
        ) -> List[PyTopic | PyTopicModelSpec | PyChunkTopicJoin]:
        """Write a list of objects to a data store"""
        return [get_or_create_item(model) for model in models]

    def read_item(
        self,
        object_id: UUID,
        model: PyTopic | PyChunkTopicJoin | PyTopicModelSpec,
    ) -> PyTopic | PyChunkTopicJoin | PyTopicModelSpec | None:
        """Read an object from a data store"""
        return get_by_id(model=model, object_id=object_id)

    def read_items(
        self,
        object_ids: List[UUID],
        models: List[PyTopic | PyChunkTopicJoin | PyTopicModelSpec],
    ) -> List[PyChunkTopicJoin | PyTopicModelSpec | PyTopic]:
        """Read a list of objects from a data store"""
        return [get_by_id(model=model, object_id=object_id) for model, object_id in zip(models, object_ids)]

    def update_item(
        self,
        model: TopicUpdate | ChunkTopicJoinUpdate | TopicModelSpecUpdate,
    ) -> SqTopic | SqChunkTopicJoin | SqTopicModelSpec | None:
        """Update an object in a data store"""
        return update_item(model)

    def update_items(
        self,
        items: List[TopicUpdate | ChunkTopicJoinUpdate | TopicModelSpecUpdate],
    ) -> List[SqTopic | SqChunkTopicJoin | SqTopicModelSpec | None]:
        """Update a list of objects in a data store"""
        return [update_item(item) for item in items]

    def delete_item(self, model: PyTopic | PyChunkTopicJoin | PyTopicModelSpec) -> UUID:
        """Delete an object from a data store"""
        return delete_item(model)

    def delete_items(
        self,
        models: List[PyTopic | PyChunkTopicJoin | PyTopicModelSpec],
    ) -> List[UUID]:
        """Delete a list of objects from a data store"""
        return [delete_item(model) for model in models]

    def list_all_items(
        self, model: PyTopic | PyChunkTopicJoin | PyTopicModelSpec
    ) -> List[PyTopic | PyChunkTopicJoin | PyTopicModelSpec]:
        """List all objects of a given type from a data store"""
        return get_all(model)

    def read_all_items(
        self, model: PyTopic | PyChunkTopicJoin | PyTopicModelSpec,
    ) -> List[PyTopic | PyChunkTopicJoin | PyTopicModelSpec]:
        """Read all objects of a given type from a data store"""
        return get_all(model)

    def get_item_by_attribute(
        self,
        model: ChunkTopicJoinFilter | TopicFilter | TopicModelSpecFilter,
    ) -> List[PyTopic | PyChunkTopicJoin | PyTopicModelSpec]:
        return filter_items(model)
