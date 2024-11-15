from typing import List
from uuid import UUID

from scout.DataIngest.models.schemas import Chunk as PyChunk
from scout.DataIngest.models.schemas import ChunkCreate
from scout.DataIngest.models.schemas import ChunkFilter
from scout.DataIngest.models.schemas import ChunkUpdate
from scout.DataIngest.models.schemas import Criterion as PyCriterion
from scout.DataIngest.models.schemas import CriterionCreate
from scout.DataIngest.models.schemas import CriterionFilter
from scout.DataIngest.models.schemas import CriterionUpdate
from scout.DataIngest.models.schemas import File as PyFile
from scout.DataIngest.models.schemas import FileCreate
from scout.DataIngest.models.schemas import FileFilter
from scout.DataIngest.models.schemas import FileUpdate
from scout.DataIngest.models.schemas import Project as PyProject
from scout.DataIngest.models.schemas import ProjectCreate
from scout.DataIngest.models.schemas import ProjectFilter
from scout.DataIngest.models.schemas import ProjectUpdate
from scout.DataIngest.models.schemas import Result as PyResult
from scout.DataIngest.models.schemas import ResultCreate
from scout.DataIngest.models.schemas import ResultFilter
from scout.DataIngest.models.schemas import ResultUpdate
from scout.DataIngest.models.schemas import User as PyUser
from scout.DataIngest.models.schemas import UserCreate
from scout.DataIngest.models.schemas import UserFilter
from scout.DataIngest.models.schemas import UserUpdate
from scout.utils.storage.postgres_interface import delete_item
from scout.utils.storage.postgres_interface import filter_items
from scout.utils.storage.postgres_interface import get_all
from scout.utils.storage.postgres_interface import get_by_id
from scout.utils.storage.postgres_interface import get_or_create_item
from scout.utils.storage.postgres_interface import update_item
from scout.utils.storage.postgres_models import Chunk as SqChunk
from scout.utils.storage.postgres_models import Criterion as SqCriterion
from scout.utils.storage.postgres_models import File as SqFile
from scout.utils.storage.postgres_models import Project as SqProject
from scout.utils.storage.postgres_models import Result as SqResult
from scout.utils.storage.postgres_models import User as SqUser
from scout.utils.storage.storage_handler import BaseStorageHandler


class PostgresStorageHandler(BaseStorageHandler):
    def __init__(self):
        super().__init__()

    def write_item(
        self,
        model: CriterionCreate | ChunkCreate | FileCreate | ProjectCreate | ResultCreate | UserCreate,
    ) -> PyProject | PyResult | PyUser | PyChunk | PyFile | PyCriterion:
        """Write an object to a data store"""
        return get_or_create_item(model)

    def write_items(
        self,
        models: List[CriterionCreate | ChunkCreate | FileCreate | ProjectCreate | ResultCreate | UserCreate],
    ) -> List[PyProject | PyResult | PyUser | PyChunk | PyFile | PyCriterion]:
        """Write a list of objects to a data store"""
        return [get_or_create_item(model) for model in models]

    def read_item(
        self,
        object_id: UUID,
        model: PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser,
    ) -> PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser | None:
        """Read an object from a data store"""
        return get_by_id(model=model, object_id=object_id)

    def read_items(
        self,
        object_ids: List[UUID],
        models: List[PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser],
    ) -> List[PyProject | PyResult | PyUser | PyChunk | PyFile | PyCriterion]:
        """Read a list of objects from a data store"""
        return [get_by_id(model=model, object_id=object_id) for model, object_id in zip(models, object_ids)]

    def update_item(
        self,
        model: CriterionUpdate | ChunkUpdate | FileUpdate | ProjectUpdate | ResultUpdate | UserUpdate,
    ) -> SqCriterion | SqChunk | SqFile | SqProject | SqResult | SqUser | None:
        """Update an object in a data store"""
        return update_item(model)

    def update_items(
        self,
        items: List[CriterionUpdate | ChunkUpdate | FileUpdate | ProjectUpdate | ResultUpdate | UserUpdate],
    ) -> List[SqCriterion | SqChunk | SqFile | SqProject | SqResult | SqUser | None]:
        """Update a list of objects in a data store"""
        return [update_item(item) for item in items]

    def delete_item(self, model: PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser) -> UUID:
        """Delete an object from a data store"""
        return delete_item(model)

    def delete_items(
        self,
        models: List[PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser],
    ) -> List[UUID]:
        """Delete a list of objects from a data store"""
        return [delete_item(model) for model in models]

    def list_all_items(
        self, model: PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser
    ) -> List[PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser]:
        """List all objects of a given type from a data store"""
        return get_all(model)

    def read_all_items(
        self, model: PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser
    ) -> List[PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser]:
        """Read all objects of a given type from a data store"""
        return get_all(model)

    def get_item_by_attribute(
        self,
        model: UserFilter | ProjectFilter | ResultFilter | ChunkFilter | CriterionFilter | FileFilter,
    ) -> List[PyCriterion | PyChunk | PyFile | PyProject | PyResult | PyUser]:
        return filter_items(model)
