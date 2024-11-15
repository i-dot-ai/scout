import sqlite3
from typing import List
from typing import Type
from typing import Union
from uuid import UUID

from pydantic import BaseModel

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
from scout.utils.storage.storage_handler import BaseStorageHandler

models_to_store = [
    PyResult,
    PyCriterion,
    PyFile,
    PyProject,
    PyChunk,
    PyUser,
]

CreateT = Union[CriterionCreate, ChunkCreate, FileCreate, ProjectCreate, ResultCreate, UserCreate]
UpdateT = Union[CriterionUpdate, ChunkUpdate, FileUpdate, ProjectUpdate, ResultUpdate, UserUpdate]
FilterT = Union[CriterionFilter, ChunkFilter, FileFilter, ProjectFilter, ResultFilter, UserFilter]
PyT = Union[PyCriterion, PyChunk, PyFile, PyProject, PyResult, PyUser]


class SQLiteStorageHandler(BaseStorageHandler):
    def __init__(self, path_to_file: str = ".data/main.db"):
        super().__init__()
        self.client = sqlite3.connect(path_to_file)
        self.cursor = self.client.cursor()

        for model in models_to_store:
            self._create_table_from_pydantic(model)

    def write_item(self, model: CreateT) -> PyT:
        table_name = model.__class__.__name__.lower()
        columns = ", ".join(model.dict().keys())
        placeholders = ", ".join("?" * len(model.dict()))
        values = tuple(model.dict().values())

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.client.commit()

        return self.read_item(model.uuid, type(model))

    def write_items(self, models: List[CreateT]) -> List[PyT]:
        if not models:
            return []

        table_name = models[0].__class__.__name__.lower()
        columns = ", ".join(models[0].dict().keys())
        placeholders = ", ".join("?" * len(models[0].dict()))

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = [tuple(model.dict().values()) for model in models]

        self.cursor.executemany(sql, values)
        self.client.commit()

        return self.read_items([model.uuid for model in models], type(models[0]))

    def read_item(self, object_id: UUID, model: PyT) -> Union[PyT, None]:
        table_name = model.__name__.lower()
        sql = f"SELECT * FROM {table_name} WHERE uuid = ?"
        self.cursor.execute(sql, (str(object_id),))
        row = self.cursor.fetchone()

        if row:
            return model(**dict(zip([column[0] for column in self.cursor.description], row)))
        return None

    def read_items(self, object_ids: List[UUID], models: List[PyT]) -> List[PyT]:
        if not object_ids or not models:
            return []

        table_name = models[0].__name__.lower()
        sql = f"SELECT * FROM {table_name} WHERE uuid IN ({', '.join('?' * len(object_ids))})"
        self.cursor.execute(sql, [str(uuid) for uuid in object_ids])
        rows = self.cursor.fetchall()

        return [models[0](**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]

    def update_item(self, model: UpdateT) -> Union[PyT, None]:
        table_name = model.__class__.__name__.lower()
        set_clause = ", ".join(f"{k} = ?" for k in model.dict().keys() if k != "uuid")
        values = tuple(v for k, v in model.dict().items() if k != "uuid") + (str(model.uuid),)

        sql = f"UPDATE {table_name} SET {set_clause} WHERE uuid = ?"
        self.cursor.execute(sql, values)
        self.client.commit()

        return self.read_item(model.uuid, type(model))

    def update_items(self, items: List[UpdateT]) -> List[Union[PyT, None]]:
        if not items:
            return []

        updated_items = []
        for item in items:
            updated_item = self.update_item(item)
            updated_items.append(updated_item)

        return updated_items

    def delete_item(self, model: PyT) -> UUID:
        table_name = model.__class__.__name__.lower()
        sql = f"DELETE FROM {table_name} WHERE uuid = ?"
        self.cursor.execute(sql, (str(model.uuid),))
        self.client.commit()
        return model.uuid

    def delete_items(self, models: List[PyT]) -> List[UUID]:
        if not models:
            return []

        table_name = models[0].__class__.__name__.lower()
        uuids = [str(model.uuid) for model in models]
        sql = f"DELETE FROM {table_name} WHERE uuid IN ({', '.join('?' * len(uuids))})"
        self.cursor.execute(sql, uuids)
        self.client.commit()
        return [model.uuid for model in models]

    def list_all_items(self, model: PyT) -> List[PyT]:
        table_name = model.__name__.lower()
        sql = f"SELECT * FROM {table_name}"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        return [model(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]

    def read_all_items(self, model: PyT) -> List[PyT]:
        return self.list_all_items(model)

    def get_item_by_attribute(self, model: FilterT) -> List[PyT]:
        table_name = model.__class__.__name__.lower().replace("filter", "")
        conditions = " AND ".join(f"{key} = ?" for key, value in model.dict().items() if value is not None)
        values = tuple(value for value in model.dict().values() if value is not None)

        sql = f"SELECT * FROM {table_name} WHERE {conditions}"
        self.cursor.execute(sql, values)
        rows = self.cursor.fetchall()

        model_class = next(m for m in models_to_store if m.__name__.lower() == table_name)
        return [model_class(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]

    def _create_table_from_pydantic(self, model: Type[BaseModel]):
        table_name = model.__name__.lower()
        columns = []

        for field_name, field_type in model.__annotations__.items():
            sqlite_type = None
            if field_type is int:
                sqlite_type = "INTEGER"
            elif field_type is str:
                sqlite_type = "TEXT"
            elif field_type is float:
                sqlite_type = "REAL"
            elif field_type is bool:
                sqlite_type = "INTEGER"
            if sqlite_type is not None:
                columns.append(f"{field_name} {sqlite_type}")
            else:
                columns.append(f"{field_name}")

        columns_str = ", ".join(columns)
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str});"

        self.cursor.execute(create_table_sql)
        self.client.commit()
