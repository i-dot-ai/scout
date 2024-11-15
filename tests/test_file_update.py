import uuid

from scout.DataIngest.models.schemas import ChunkCreate, FileCreate, FileUpdate, ProjectCreate
from scout.utils.storage.postgres_database import SessionLocal
from scout.utils.storage.postgres_models import Chunk as SqChunk
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler


def test_file_update_maintains_chunks():
    """Test that updating a file maintains its chunk relationships"""
    storage_handler = PostgresStorageHandler()

    project = ProjectCreate(name="test_project", id=uuid.uuid4())

    created_project = storage_handler.write_item(project)

    file_id = uuid.uuid4()
    file = FileCreate(
        name="test_file.pdf",
        type=".pdf",
        id=file_id,
        project=created_project,
        s3_key="dummy_s3_key",
        s3_bucket="dummy_s3_bucket",
    )
    created_file = storage_handler.write_item(file)
    assert created_file is not None
    # Create some test chunks
    chunks = [
        ChunkCreate(idx=1, text="Test chunk 1", page_num=1, file=created_file),
        ChunkCreate(idx=2, text="Test chunk 2", page_num=1, file=created_file),
    ]
    assert chunks is not None
    # Write chunks to database
    created_chunks = storage_handler.write_items(chunks)

    # Create a file update with new metadata but same chunks
    file_update = FileUpdate(
        id=created_file.id,
        name="test_file.pdf",
        type=".pdf",
        clean_name="Updated Clean Name",
        summary="Updated Summary",
        chunks=created_chunks,
    )

    # Perform the update
    updated_file = storage_handler.update_item(file_update)

    # Verify the update
    assert updated_file is not None
    assert updated_file.clean_name == "Updated Clean Name"
    assert updated_file.summary == "Updated Summary"
    assert len(updated_file.chunks) == 2

    # Verify chunks are still properly linked
    with SessionLocal() as db:
        db_chunks = db.query(SqChunk).filter(SqChunk.file_id == updated_file.id).all()
        assert len(db_chunks) == 2, f"Expected 2 chunks, got {len(db_chunks)}"
        for chunk in db_chunks:
            assert chunk.file_id == updated_file.id


def test_file_update_without_chunks():
    """Test that updating a file without specifying chunks doesn't affect existing chunks"""
    storage_handler = PostgresStorageHandler()

    # Create a project first
    project = ProjectCreate(name="test_project", id=uuid.uuid4())
    created_project = storage_handler.write_item(project)

    # Create initial file with chunks
    file_id = uuid.uuid4()
    file = FileCreate(
        name="test_file2.pdf",
        type=".pdf",
        id=file_id,
        project=created_project,
        s3_key="dummy_s3_key",
        s3_bucket="dummy_s3_bucket",
    )
    created_file = storage_handler.write_item(file)
    assert created_file is not None

    # Create and write initial chunks
    initial_chunks = [ChunkCreate(idx=1, text="Initial chunk 1", page_num=1, file=created_file)]
    storage_handler.write_items(initial_chunks)

    # Update file without specifying chunks
    file_update = FileUpdate(id=created_file.id, name="test_file2.pdf", type=".pdf", clean_name="New Clean Name")

    updated_file = storage_handler.update_item(file_update)
    assert updated_file is not None

    # Verify chunks are preserved with debug info
    with SessionLocal() as db:
        db_chunks = db.query(SqChunk).filter(SqChunk.file_id == updated_file.id).all()
        print(f"Searching for file_id: {updated_file.id}")
        all_chunks = db.query(SqChunk).all()
        print(f"All chunks in db: {all_chunks}")
        print(f"Chunk file IDs: {[chunk.file_id for chunk in all_chunks]}")
        print(f"Found chunks: {db_chunks}")
        assert len(db_chunks) == 1, f"Expected 1 chunk, got {len(db_chunks)}"
        assert db_chunks[0].text == "Initial chunk 1"
