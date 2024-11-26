import time

import pandas as pd
import numpy as np
from typing import Any
from typing import Mapping
from bertopic import BERTopic
from tqdm import tqdm
from scout.TopicModelling.models import TopicCreate as Topic

class TopicModel:
    def __init__(
        self,
        chunks,
        model_name: str,
    ):
        self.chunks = chunks
        self.model_name = model_name

        # Unpack chunks
        self.text = [chunk.text for chunk in self.chunks]
        self.document_ids = [chunk.id for chunk in self.chunks]

    def embedd_chunks(
        self,
        embedder,
    ):
        self.embeddings = []

        for chunk in tqdm(self.text, desc="Embedding chunks..."):
            self.embeddings.append((embedder.embed_query(chunk)))

        self.embeddings = np.array(self.embeddings)

    def create_model(self, params, bert_stack):
        self.params = params  # For meta data
        self.model = BERTopic(**params, **bert_stack)

    def fit(self, save: str = False) -> Mapping[str, Any]:
        """Train Topic Model
        Args:
            save: Name of the file to save to. A JSON in current directory
        """

        # Create the BERT model
        # Train model and record computation time
        start = time.time()
        self.topics = self.model.fit_transform(self.text, self.embeddings)
        end = time.time()
        computation_time = float(end - start)

        self.result = {
            "num_docs": len(self.text),
            "model": self.model_name,
            "params": self.params,
            "computation_time": computation_time,
            "num_topics": len(self.model.get_topics()),
        }

        return
    
    def fetch_topics(self):
        # Extract topic data
        topics = self.model.get_topic_info()

        try:
            # Convert the representations into strings not lists of length 1
            topics["summary"] = topics["summary"].apply(
                lambda x: x[0] if isinstance(x, list) else x
            )
            topics["Primary theme"] = topics["Primary theme"].apply(
                lambda x: x[0] if isinstance(x, list) else x
            )
            topics["openai"] = topics["openai"].apply(
                lambda x: x[0] if isinstance(x, list) else x
            )

            # Top n words
            topic_top_words_raw = self.model.get_topics(full=False)
            topics_top_words = {}

            # Serialise for sqlite storage
            for i in topic_top_words_raw:
                if (
                    i > -2
                ):  # Can be set to remove topic -1, which is the dumping topic. May want to make this more production ready
                    words_only = [word_prob[0] for word_prob in self.model.get_topic(i)]
                    topics_top_words.update({i: words_only})

        except Exception as _:
            print("Failed to get and serialise topics")

        try:
            # Select only relevant cols
            cols = ["Topic", "Count", "openai", "summary", "Primary theme"]
            topics = topics[cols]
            # Rename cols
            col_map = {
                "Topic": "topic_num",
                "Count": "num_documents",
                "openai": "representation",
                "summary": "summary",
                "Primary theme": "primary_theme",
            }

            topics = topics.rename(columns=col_map)
            topics = topics.to_dict(orient="index")

        except Exception as _:
            print("Failed to prep topics")

        try:
            print("Create Topic Objects")

            topics_to_add = []
            for topic_index in topics:

                if topic_index in topics_top_words:

                    topic_to_add = Topic(
                        **topics[topic_index],
                        top_words=topics_top_words[topic_index],
                        topic_model=self.model_spec
                    )
                    topics_to_add.append(topic_to_add)

        except Exception as _:
            print("Failed to create topics")

        return topics_to_add

    def fetch_documents(self):
        # Create DF of document UUID and topic id
        df = pd.DataFrame({"document_uuid": self.document_ids})
        df["topic"] = self.topics[0]  # Index 0 is topic id, 1 has probabilities
        df["topic_prob"] = [max(probs) for probs in self.topics[1]]
        return df

    def outputs(self):
        # Code to fetch outputs

        try:
            topics = self.fetch_topics()  # To create topic data set
            documents = self.fetch_documents()  # To add topic to a chunk

            # Map each topic to a Topic object
            # Create doc uuid - topic map
            topic_to_chunk_uuids = (
                documents.groupby("topic")["document_uuid"].apply(list).to_dict()
            )
            uuid_to_chunk = {chunk.id: chunk for chunk in self.chunks}

            for topic in topics:
                topic_uuids = topic_to_chunk_uuids.get(topic.topic_num, [])
                topic.chunks = [
                    uuid_to_chunk[uuid] for uuid in topic_uuids if uuid in uuid_to_chunk
                ]
                topic.topic_model = self.model_spec

        except Exception as _:
            print("Failed to get topics")

        return topics