import copy
from typing import List
from typing import Optional

from flashrank import Ranker
from flashrank import RerankRequest
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from pydantic import Field


class ReRankRetriever(BaseRetriever):
    vectorstore: VectorStore
    search_type: str = "similarity"
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        rerank: bool = True,
    ) -> List[Document]:
        modified_search_kwargs = copy.deepcopy(self.search_kwargs)
        modified_search_kwargs["k"] = self.search_kwargs["k"] * 3  # boost this number before re ranking
        ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=".data")

        if self.search_type == "similarity":
            docs = self.vectorstore.similarity_search(query, **modified_search_kwargs)
        elif self.search_type == "similarity_score_threshold":
            docs_and_similarities = self.vectorstore.similarity_search_with_relevance_scores(
                query, **modified_search_kwargs
            )
            docs = [doc for doc, _ in docs_and_similarities]
        elif self.search_type == "mmr":
            docs = self.vectorstore.max_marginal_relevance_search(query, **modified_search_kwargs)
        else:
            raise ValueError(f"search_type of {self.search_type} not allowed.")

        if len(docs) < self.search_kwargs["k"]:
            raise RuntimeError("Document retrieval has not returned enough documents.")

        if rerank:
            re_rank_docs = [{"id": idx, "text": document.page_content} for idx, document in enumerate(docs)]

            rerank_request = RerankRequest(query=query, passages=re_rank_docs)
            results = ranker.rerank(rerank_request)

            ids_to_keep = [res["id"] for res in results][: self.search_kwargs["k"]]
            docs = [docs[i] for i in ids_to_keep if i < len(docs)]

        # Expand docs to include surrounding chunks
        expanded_docs = self._expand_docs(docs)

        return expanded_docs

    def _expand_docs(self, docs: List[Document]) -> List[Document]:
        expanded_docs = []
        for doc in docs:
            file_name = doc.metadata.get("source")
            idx = doc.metadata.get("idx")
            if file_name is None or idx is None:
                expanded_docs.append(doc)
                continue

            expanded_docs.append(doc)

            # Get the chunk above
            above_chunk = self._get_chunk(file_name, idx - 1)
            if above_chunk:
                expanded_docs.append(above_chunk)

            # Get the chunk below
            below_chunk = self._get_chunk(file_name, idx + 1)
            if below_chunk:
                expanded_docs.append(below_chunk)

        return expanded_docs

    def _get_chunk(self, file_name: str, idx: int) -> Optional[Document]:
        # Implement this method to retrieve a specific chunk from the vectorstore
        # This is a placeholder implementation and needs to be adapted to your specific vectorstore
        try:
            chunk = self.vectorstore.get_document(file_name=file_name, idx=idx)
            return chunk
        except Exception:
            return None
