import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

TopicSchemaBase = declarative_base()

class TopicModelSpec(TopicSchemaBase):
    __tablename__ = "topic_model"
    __table_args__ = {"schema": "topic_modelling"}

    name = Column(String)
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    num_docs = Column(Integer)
    computation_time = Column(Float)
    num_topics = Column(Integer)
    created_datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_datetime = Column(DateTime(timezone=True), onupdate=func.now())

    topics = relationship("Topic", back_populates="topic_model")


class Topic(TopicSchemaBase):
    __tablename__ = "topics"
    __table_args__ = {"schema": "topic_modelling"}

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    topic_num = Column(Integer)
    representation = Column(String)
    summary = Column(String)
    primary_theme = Column(String)
    top_words = Column(ARRAY(String))
    num_documents = Column(Integer)
    created_datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_datetime = Column(DateTime(timezone=True), onupdate=func.now())

    topic_model_id = Column(UUID, ForeignKey("topic_modelling.topic_model.id"))
    topic_model = relationship("TopicModelSpec", back_populates="topics")

    chunk_associations = relationship("ChunkTopicJoin", back_populates="topic")

class ChunkTopicJoin(TopicSchemaBase):
    __tablename__ = 'chunk_topic_associations'
    __table_args__ = {'schema': 'topic_modelling'}

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    chunk_id = Column(UUID, nullable=False)  # Reference to base application's chunk
    topic_id = Column(UUID, ForeignKey('topic_modelling.topics.id'))
    relevance_score = Column(Float, nullable=False)

    topic = relationship("Topic", back_populates="chunk_associations")

