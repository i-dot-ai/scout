import time

from typing import Any
from typing import Mapping
from bertopic import BERTopic
from tqdm import tqdm

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

