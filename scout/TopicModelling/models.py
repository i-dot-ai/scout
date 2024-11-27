from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, Extra
from scout.DataIngest.models.schemas import ChunkBase


global_model_config = ConfigDict(
    from_attributes=True,  # Use ORM to retrieve objects
    extra=Extra.ignore,  # Ignore any extra values that get passed in when serializing
    use_enum_values=True,  # Use enum values rather than raw enum
)

# Topics


class TopicModelSpecBase(BaseModel):
    # Allows pydantic/sqlalchemy to use ORM to pull out related objects instead of just references to them
    model_config = global_model_config

    id: UUID
    name: str
    num_docs: int
    computation_time: float
    num_topics: int
    created_datetime: datetime
    updated_datetime: Optional[datetime]


class TopicModelSpecCreate(BaseModel):
    name: str
    num_docs: int
    computation_time: float
    num_topics: int
    topics: Optional[list["TopicBase"]] = None


class TopicModelSpecUpdate(TopicModelSpecCreate):
    id: UUID


class TopicModelSpecFilter(BaseModel):
    name: Optional[str] = None
    num_docs: Optional[int] = None
    computation_time: Optional[float] = None
    num_topics: Optional[int] = None


class TopicModelSpec(TopicModelSpecBase):

    topics: Optional[list["TopicBase"]] = Field(default_factory=list)


class TopicBase(BaseModel):
    # Allows pydantic/sqlalchemy to use ORM to pull out related objects instead of just references to them
    model_config = global_model_config

    id: UUID
    topic_num: int
    representation: str
    summary: str
    primary_theme: str
    top_words: List[str]
    num_documents: int
    created_datetime: datetime
    updated_datetime: Optional[datetime]


class TopicCreate(BaseModel):

    topic_num: int
    representation: str
    summary: str
    primary_theme: str
    top_words: List[str]
    num_documents: int
    topic_model: Optional["TopicModelSpecBase"] = None
    chunks: Optional["ChunkBase"] = None


class TopicUpdate(TopicCreate):
    id: UUID


class TopicFilter(BaseModel):

    topic_num: Optional[int] = None
    representation: Optional[str] = None
    summary: Optional[str] = None
    primary_theme: Optional[str] = None
    top_words: Optional[list[str]] = Field(default_factory=list)
    num_documents: Optional[int] = None
    topic_model: Optional["TopicModelSpecBase"]


class Topic(TopicBase):
    topic_model: Optional["TopicModelSpecBase"] = None


class ChunkTopicJoinBase(BaseModel):
    # Allows pydantic/sqlalchemy to use ORM to pull out related objects instead of just references to them
    model_config = global_model_config

    chunk_id: UUID
    topic_id: UUID
    relevance_score: float
    created_datetime: datetime
    updated_datetime: Optional[datetime]


class ChunkTopicJoinCreate(BaseModel):
    chunk_id: UUID
    topic_id: UUID
    relevance_score: float


class ChunkTopicJoinUpdate(ChunkTopicJoinCreate):
    id: UUID


class ChunkTopicJoinFilter(BaseModel):
    chunk_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None


class ChunkTopicJoin(ChunkTopicJoinBase):
    topics: Optional[list["TopicBase"]] = Field(default_factory=list)

