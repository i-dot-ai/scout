import logging
from uuid import UUID

from decorator import contextmanager
from sqlalchemy import or_
from sqlalchemy.orm import Session

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
from scout.TopicModelling.storage.postgres_models import Topic as SqTopic
from scout.TopicModelling.storage.postgres_models import TopicModelSpec as SqTopicModelSpec
from scout.TopicModelling.storage.postgres_models import ChunkTopicJoin as SqChunkTopicJoin

from scout.utils.storage.postgres_database import SessionLocal


pydantic_update_model_to_sqlalchemy_model = {
    TopicUpdate: SqTopic,
    TopicModelSpecUpdate: SqTopicModelSpec,
    ChunkTopicJoinUpdate: SqChunkTopicJoin,
}

pydantic_update_model_to_base_model = {
    TopicUpdate: PyTopic,
    TopicModelSpecUpdate: PyTopicModelSpec,
    ChunkTopicJoinUpdate: PyChunkTopicJoin,
}

pydantic_create_model_to_sqlalchemy_model = {
    TopicCreate: SqTopic,
    TopicModelSpecCreate: SqTopicModelSpec,
    ChunkTopicJoinCreate: SqChunkTopicJoin,
}

pydantic_create_model_to_base_model = {
    TopicCreate: PyTopic,
    TopicModelSpecCreate: PyTopicModelSpec,
    ChunkTopicJoinCreate: PyChunkTopicJoin,
}

pydantic_model_to_sqlalchemy_model_map = {
    PyTopic: SqTopic,
    PyTopicModelSpec: SqTopicModelSpec,
    PyChunkTopicJoin: SqChunkTopicJoin,
    TopicFilter: SqTopic,
    TopicModelSpecFilter: SqTopicModelSpec,
    ChunkTopicJoinFilter: SqChunkTopicJoin,
}

pydantic_model_to_sqlalchemy_model_map.update(pydantic_create_model_to_sqlalchemy_model)
pydantic_model_to_sqlalchemy_model_map.update(pydantic_update_model_to_sqlalchemy_model)

logging.basicConfig(level=logging.INFO, format='TOPIC MODELLING:\t%(message)s')
logger = logging.getLogger(__name__)

@contextmanager
def SessionManager() -> Session:
    db = SessionLocal()
    try:
        yield db
    except:
        logger.debug("Db operation failed... rolling back")
        db.rollback()
        raise
    finally:
        db.close()


def get_all(
    model: PyTopic | PyTopicModelSpec | PyChunkTopicJoin,
) -> list[PyTopic | PyTopicModelSpec | PyChunkTopicJoin] | None:
    with SessionManager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(model)
            result = db.query(sq_model).all()
            results = []
            for item in result:
                parsed_item = model.model_validate(item)
                results.append(parsed_item)  # Parse retrieved info into pydantic model and add to list
            return results
        except Exception as _:
            logger.exception(f"Failed to get all items, {model}")


def get_by_id(
    model: PyTopic | PyTopicModelSpec | PyChunkTopicJoin,
    object_id: UUID,
) -> PyTopic | PyTopicModelSpec | PyChunkTopicJoin | None:
    with SessionManager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(model)
            result = db.query(sq_model).filter_by(id=object_id).one_or_none()
            if result is None:
                return None
            parsed_item = model.model_validate(result)
            return parsed_item
        except Exception as _:
            logger.exception(f"Failed to get item by id, {model}, {object_id}")


def get_or_create_item(
    model: TopicCreate | TopicModelSpecCreate | ChunkTopicJoinCreate,
) -> PyTopic | PyTopicModelSpec | PyChunkTopicJoin :
    model_type = type(model)
    with SessionManager() as db:
        try:
            if model_type is TopicCreate:
                return _get_or_create_topic(model, db)
            if model_type is TopicModelSpecCreate:
                return _get_or_create_topic_model_spec(model, db)
            if model_type is ChunkTopicJoinCreate:
                return _get_or_create_chunk_topic_join(model, db)
        except Exception as _:
            logger.exception(f"Failed to get or create item, {model}")

def _get_or_create_topic(model: TopicCreate, db: Session) -> PyTopic:
    sq_model = SqTopic
    
    item_to_add = sq_model(
        topic_num=model.topic_num,
        representation=model.representation,
        summary=model.summary,
        primary_theme=model.primary_theme,
        top_words=model.top_words,
        num_documents=model.num_documents,
        topic_model_id=model.topic_model.id,
    )

    db.add(item_to_add)
    db.commit()
    db.flush()

    # for chunk in model.chunks:
    #     existing_chunk: SqChunk | None = db.query(SqChunk).get(chunk.id)
    #     db.execute(
    #         chunk_topic.insert().values(
    #             chunk_id=existing_chunk.id, topic_id=item_to_add.id
    #         )
    #     )

    return PyTopic.model_validate(item_to_add)

    return

def _get_or_create_topic_model_spec(model: TopicModelSpecCreate, db: Session) -> PyTopicModelSpec:
    sq_model = SqTopicModelSpec

    item_to_add = sq_model(
        name=model.name,
        num_docs=model.num_docs,
        computation_time=model.computation_time,
        num_topics=model.num_topics,
    )

    db.add(item_to_add)
    db.commit()
    db.flush()

    return PyTopicModelSpec.model_validate(item_to_add)

def _get_or_create_chunk_topic_join(model: ChunkTopicJoinCreate, db: Session) -> PyChunkTopicJoin:
    sq_model = SqChunkTopicJoin

    item_to_add = sq_model(
        chunk_id=model.chunk_id,
        relvenace_score=model.relevance_score,
    )

    db.add(item_to_add)
    db.commit()
    db.flush
    return PyChunkTopicJoin.model_validate(item_to_add)

def delete_item(
        model: PyTopic | PyTopicModelSpec | PyChunkTopicJoin,
) -> UUID:
    with SessionManager() as db:
        try:
            sq_model = pydantic_model_to_sqlalchemy_model_map.get(type(model))
            item = db.query(sq_model).get(model.id)
            db.delete(item)
            db.commit()
            return model.id
        except Exception as _:
            logger.exception(f"Failed to delete item, {model}")

def update_item(
        model: TopicUpdate | TopicModelSpecUpdate | ChunkTopicJoinUpdate,
) -> PyTopic | PyTopicModelSpec | PyChunkTopicJoin | None:
    model_type = type(model)
    with SessionManager() as db:
        try:
            if model_type is TopicUpdate:
                return _update_topic(model, db)
            if model_type is TopicModelSpecUpdate:
                return _update_topic_model_spec(model, db)
            if model_type is ChunkTopicJoinUpdate:
                return _update_chunk_topic_join(model, db)
        except Exception as _:
            logger.exception(f"Failed to update item, {model}")

def _update_topic(model, db):
    sq_model = pydantic_update_model_to_sqlalchemy_model.get(type(model))
    item = db.query(sq_model).filter(sq_model.id == model.id).one_or_none()

    if item is None:
        return None
    
    item.representation=model.representation
    item.summary=model.summary
    item.primary_theme=model.primary_theme
    item.top_words=model.top_words
    item.num_documents=model.num_documents

    db.commit()
    db.flush()
    
    return PyTopic.model_validate(item)

def _update_topic_model_spec(model, db):
    sq_model = pydantic_update_model_to_sqlalchemy_model.get(type(model))
    item = db.query(sq_model).filter(sq_model.id == model.id).one_or_none()

    if item is None:
        return None
    
    item.name=model.name
    item.num_docs=model.num_docs
    item.computation_time=model.computation_time
    item.num_topics=model.num_topics
    item.topics=[db.query(SqTopic).get(topic.id) for topic in model.topics]

    db.commit()
    db.flush()

    return PyTopicModelSpec.model_validate(item)

def _update_chunk_topic_join():
    return


def filter_items(
        model: TopicFilter | TopicModelSpecFilter | ChunkTopicJoinFilter,
) -> list[PyTopic | PyTopicModelSpec | PyChunkTopicJoin]:
    model_type = type(model)
    with SessionManager() as db:
        try:
            if model_type is TopicFilter:
                return _filter_topic(model, db)
            if model_type is TopicModelSpecFilter:
                return _filter_topic_model_spec(model, db)
            if model_type is ChunkTopicJoinFilter:
                return _filter_chunk_topic_join(model, db)
        except Exception as _:
            logger.exception(f"Failed to filter items, {model}")

def _filter_topic(model, db):
    query=db.query(SqTopic)
    if model.representation:
        query = query.filter(SqTopic.representation.ilike(f"%{model.representation}"))
    if model.summary:
        query = query.filter(SqTopic.summary.ilike(f"%{model.summary}"))
    if model.primary_theme:
        query = query.filter(SqTopic.primary_theme.ilike(f"%{model.primary_theme}"))
    if model.top_words:
        query = query.filter(SqTopic.top_words.ilike(f"%{model.top_words}"))
    if model.num_documents:
        query = query.filter(SqTopic.num_documents == model.num_documents)

    result = query.all()
    results = []
    for item in result:
        results.append(PyTopic.model_validate(item))
    return results

def _filter_topic_model_spec(model, db):
    query=db.query(SqTopicModelSpec)
    if model.name:
        query = query.filter(SqTopicModelSpec.name.ilike(f"%{model.name}"))
    if model.num_docs:
        query = query.filter(SqTopicModelSpec.num_docs == model.num_docs)
    if model.num_topics:
        query = query.filter(SqTopicModelSpec.num_topics == model.num_topics)

    result = query.all()
    results = []
    for item in result:
        results.append(PyTopic.model_validate(item))
    return results


def _filter_chunk_topic_join():
    return



