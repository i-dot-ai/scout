import datetime
import uuid
from unittest.mock import Mock

import pytest
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel

from scout.DataIngest.file_info import get_file_update
from scout.DataIngest.models.schemas import File, FileInfo
from scout.utils.storage.filesystem import S3StorageHandler
from scout.utils.storage.storage_handler import BaseStorageHandler


class MockProject(BaseModel):
    name: str
    id: str = "mock_project_id"


class MockFile(BaseModel):
    name: str
    type: str
    id: str = "mock_file_id"


class MockChunk(BaseModel):
    text: str
    id: str = "mock_chunk_id"
    file: MockFile
    page_num: int = 1


@pytest.fixture
def mock_storage_handler():
    return Mock(spec=BaseStorageHandler)


@pytest.fixture
def mock_s3_storage_handler():
    return Mock(spec=S3StorageHandler)


@pytest.fixture
def mock_vector_store():
    return Mock(spec=VectorStore)


def test_get_file_update():
    file = File(
        id=uuid.uuid4(),
        created_datetime=datetime.datetime.now(),
        updated_datetime=datetime.datetime.now(),
        type=".pdf",
        name="My test file.pdf",
    )
    file_info = FileInfo(
        clean_name="Clean Test File", summary="Test summary", source="IPA", published_date="01-01-2023"
    )
    empty_file_info = FileInfo()

    file_update = get_file_update(file=file, file_info=file_info)
    assert file_update.name == "My test file.pdf"
    assert file_update.clean_name == "Clean Test File"
    assert file_update.summary == "Test summary"
    assert file_update.source == "IPA"
    assert file_update.published_date == "01-01-2023"

    file_update_missing_info = get_file_update(file=file, file_info=empty_file_info)
    assert file_update_missing_info.name == "My test file.pdf"
    assert not file_update_missing_info.clean_name
    assert not file_update_missing_info.summary
    assert not file_update_missing_info.source
    assert not file_update_missing_info.published_date
