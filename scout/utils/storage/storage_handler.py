from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import TypeVar
from typing import Union
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
from scout.utils.storage.postgres_models import Chunk as SqChunk
from scout.utils.storage.postgres_models import Criterion as SqCriterion
from scout.utils.storage.postgres_models import File as SqFile
from scout.utils.storage.postgres_models import Project as SqProject
from scout.utils.storage.postgres_models import Result as SqResult
from scout.utils.storage.postgres_models import User as SqUser

T = TypeVar("T")
CreateT = TypeVar(
    "CreateT",
    CriterionCreate,
    ChunkCreate,
    FileCreate,
    ProjectCreate,
    ResultCreate,
    UserCreate,
)
UpdateT = TypeVar(
    "UpdateT",
    CriterionUpdate,
    ChunkUpdate,
    FileUpdate,
    ProjectUpdate,
    ResultUpdate,
    UserUpdate,
)
FilterT = TypeVar(
    "FilterT",
    CriterionFilter,
    ChunkFilter,
    FileFilter,
    ProjectFilter,
    ResultFilter,
    UserFilter,
)
PyT = TypeVar("PyT", PyCriterion, PyChunk, PyFile, PyProject, PyResult, PyUser)
SqT = TypeVar("SqT", SqCriterion, SqChunk, SqFile, SqProject, SqResult, SqUser)


class BaseStorageHandler(ABC, Generic[T]):
    @abstractmethod
    def __init__(self):
        """Initialize the storage handler"""

    @abstractmethod
    def write_item(self, model: CreateT) -> PyT:
        """Write an object to a data store"""

    @abstractmethod
    def write_items(self, models: List[CreateT]) -> List[PyT]:
        """Write a list of objects to a data store"""

    @abstractmethod
    def read_item(self, object_id: UUID, model: PyT) -> Union[PyT, None]:
        """Read an object from a data store"""

    @abstractmethod
    def read_items(self, object_ids: List[UUID], models: List[PyT]) -> List[PyT]:
        """Read a list of objects from a data store"""

    @abstractmethod
    def update_item(self, model: UpdateT) -> Union[SqT, None]:
        """Update an object in a data store"""

    @abstractmethod
    def update_items(self, items: List[UpdateT]) -> List[Union[SqT, None]]:
        """Update a list of objects in a data store"""

    @abstractmethod
    def delete_item(self, model: PyT) -> UUID:
        """Delete an object from a data store"""

    @abstractmethod
    def delete_items(self, models: List[PyT]) -> List[UUID]:
        """Delete a list of objects from a data store"""

    @abstractmethod
    def list_all_items(self, model: PyT) -> List[PyT]:
        """List all objects of a given type from a data store"""

    @abstractmethod
    def read_all_items(self, model: PyT) -> List[PyT]:
        """Read all objects of a given type from a data store"""

    @abstractmethod
    def get_item_by_attribute(self, model: FilterT) -> List[PyT]:
        """Get items by attribute from a data store"""
