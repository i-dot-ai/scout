import os
from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID

import regex as re
from langchain_core.vectorstores import VectorStore
from openai import APIConnectionError, APIError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from scout.DataIngest.models.schemas import Chunk, CriterionCreate, File, ProjectCreate,ProjectUpdate, ResultCreate
from scout.LLMFlag.prompts import (
    CORE_SCOUT_PERSONA,
    DOCUMENT_EXTRACT_PROMPT,
    DOCUMENT_EXTRACTS_HEADER,
    SYSTEM_EVIDENCE_POINTS_PROMPT,
    SYSTEM_HYPOTHESIS_PROMPT,
    SYSTEM_QUESTION_PROMPT,
    USER_EVIDENCE_POINTS_PROMPT,
    USER_QUESTION_PROMPT,
    USER_REGENERATE_HYPOTHESIS_PROMPT,
    SUMMARIZE_RESPONSES_PROMPT
)
from scout.LLMFlag.retriever import ReRankRetriever
from scout.utils.storage.storage_handler import BaseStorageHandler
from scout.utils.utils import logger


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    before_sleep=lambda retry_state: logger.info(f"Retrying in {retry_state.next_action.sleep} seconds..."),
)
def api_call_with_retry(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except RateLimitError:
        logger.warning("Rate limit reached. Retrying...")
        raise
    except APIConnectionError:
        logger.warning("API connection error. Retrying...")
        raise
    except APIError as e:
        logger.error(f"API error occurred: {str(e)}")
        raise


class BaseEvaluator(ABC):
    def __init__(self):
        """Initialise the evaluator"""
        self.hypotheses = "None"
        self.temp=0

    @abstractmethod
    def evaluate_question(self, criteria_uuid: str) -> List[str]:
        """Get answers to a single question"""

    @abstractmethod
    def evaluate_questions(self, criteria_uuids: List[str]) -> List[str]:
        """Get answers to a list of questions"""

    @abstractmethod
    def _define_model(self):
        """Define the model that is the evaluator"""

    def semantic_search(self, query: str, k: int, filters: dict):
        # do retrieval
        search_kwargs = {"k": k, "filter": filters}
        retriever = ReRankRetriever(
            vectorstore=self.vector_store,
            search_type="similarity",
            search_kwargs=search_kwargs,
        )
        extracts = retriever.get_relevant_documents(query)

        # get files for metadata
        files = [
            self.storage_handler.read_item(object_id=UUID(extract.metadata["parent_doc_uuid"]), model=File)
            for extract in extracts
        ]

        # add extracts to prompt
        prompt = DOCUMENT_EXTRACTS_HEADER
        for idx, extract in enumerate(extracts):
            file = files[idx]
            if file is None:
                continue
            prompt += DOCUMENT_EXTRACT_PROMPT.format(
                file_name=getattr(file, "clean_name", file.name),
                source=getattr(file, "source", None),
                summary=getattr(file, "summary", None),
                date=getattr(file, "published_date", None),
                text=extract.page_content,
            )
        return prompt, extracts

    def answer_question(
        self,
        question: str,
        evidence: str = None,
        k=3,
    ) -> Tuple:
        """Question answering logic for llms with error handling and retries"""

        try:
            # do q and a for each evidence point
            if evidence:
                evidence_list = [item for item in evidence.split("_") if len(item) >= 5]
                evidence_responses_list = []
                for evidence_item in evidence_list:
                    extracts_prompt, extracts = self.semantic_search(
                        evidence_item, k=k, filters={"project": str(self.project.id)}
                    )
                    evidence_response = api_call_with_retry(
                        self.llm.chat.completions.create,
                        temperature=self.temp,
                        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                        messages=[
                            {
                                "role": "system",
                                "content": SYSTEM_EVIDENCE_POINTS_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": USER_EVIDENCE_POINTS_PROMPT.format(
                                    question=question, extracts=extracts_prompt
                                ),
                            },
                        ],
                    )
                    evidence_responses_list.append(evidence_response.choices[0].message.content)
                evidence_answer_pairs = [
                    f"question: {q} answer: {a}" for q, a in zip(evidence_list, evidence_responses_list)
                ]
            else:
                evidence_answer_pairs = "None"

            # get an overall final answer using the answers to the earlier points
            extracts_prompt, extracts = self.semantic_search(question, k=k, filters={"project": str(self.project.id)})
            chunks = [self.storage_handler.read_item(UUID(extract.metadata["uuid"]), Chunk) for extract in extracts]

            question_response = api_call_with_retry(
                self.llm.chat.completions.create,
                temperature=self.temp,
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": SYSTEM_QUESTION_PROMPT},
                    {
                        "role": "system",
                        "content": SYSTEM_HYPOTHESIS_PROMPT.format(hypotheses=self.hypotheses),
                    },
                    {
                        "role": "user",
                        "content": USER_QUESTION_PROMPT.format(
                            question=question,
                            extracts=extracts,
                            evidence_point_answers=evidence_answer_pairs,
                        ),
                    },
                ],
            )

            answer = question_response.choices[0].message.content

            hypotheses_response = api_call_with_retry(
                self.llm.chat.completions.create,
                temperature=0.5,
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": CORE_SCOUT_PERSONA},
                    {
                        "role": "system",
                        "content": USER_REGENERATE_HYPOTHESIS_PROMPT.format(
                            hypotheses=self.hypotheses,
                            questions_and_answers=question + answer,
                        ),
                    },
                    {
                        "role": "user",
                        "content": USER_QUESTION_PROMPT.format(
                            question=question,
                            extracts=extracts,
                            evidence_point_answers=evidence_answer_pairs,
                        ),
                    },
                ],
            )
            self.hypotheses = hypotheses_response.choices[0].message.content

            return (answer, chunks)

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise


class MainEvaluator(BaseEvaluator):
    def __init__(
        self,
        project: ProjectCreate,
        vector_store: VectorStore,
        llm: OpenAI,
        storage_handler: BaseStorageHandler,
    ):
        """Initialise the evaluator"""
        super().__init__()
        self.vector_store = vector_store
        self.llm = llm
        self.storage_handler = storage_handler
        self.project = project

        self._define_model()

    def evaluate_question(self, criterion: CriterionCreate, k: int = 3, save: bool = False) -> ResultCreate:
        """Get answers to a single question"""
        model_output = self.model(criterion=criterion)
        result = ResultCreate(
            criterion=criterion,
            project=self.project,
            answer=model_output[0],
            full_text=model_output[1],
            chunks=model_output[2],
        )

        if save:
            result = self.storage_handler.write_item(result)

        return result

    def evaluate_questions(self, criteria: List[CriterionCreate], k: int = 3, save: bool = True) -> List[ResultCreate]:
        """Get answers to a list of questions"""
        results = []
        question_answer_pairs = []
        logger.info("Evaluating questions...")
        for idx, criterion in enumerate(criteria):
            result = self.evaluate_question(criterion, k, save)
            results.append(result)
            question_answer_pairs.append((criterion.question, result.full_text))
            if idx % 5 == 0:
                logger.info(f"{idx} criteria complete")
        logger.info("Generating summary of answers...")
        # Generate summary of answers
        summary = self.generate_summary(question_answer_pairs)
        project_update=ProjectUpdate(id=self.project.id,name=self.project.name, results_summary=summary)
        self.storage_handler.update_item(project_update)
        return results

    def generate_summary(self, question_answer_pairs: List[tuple]) -> str:
        """Generate a summary of the answers using an LLM, with an input prompt containing instructions."""

     
        formatted_input = ", ".join([f"Question: {qa[0]}\nAnswer: {qa[1]}" for qa in question_answer_pairs])
        response = api_call_with_retry(
            self.llm.chat.completions.create,
            temperature=self.temp,
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "user",
                    "content": SUMMARIZE_RESPONSES_PROMPT.format(qa_pairs=formatted_input,hypotheses=self.hypotheses),
                },
            ],
        )

        return response.choices[0].message.content

    def _define_model(self):
        """Define the model that is the evaluator"""

        def model(criterion: CriterionCreate, k: int = 3):
            full_text, chunks = self.answer_question(
                question=criterion.question,
                evidence=criterion.evidence,
                k=k,
            )

            # find any sentiment words that might be in square brackets
            extracted_words = re.findall(r'\[?(positive|neutral|negative)\]?', full_text, re.IGNORECASE)

            if extracted_words:
                answer = extracted_words[-1].title()
                # Remove the key words and brackets from full_text
                full_text = re.sub(
                    r'\[?(positive|neutral|negative)\]?',
                    "",
                    full_text,
                    flags=re.IGNORECASE,
                ).strip()
            else:
                answer = "None"

            return (answer, full_text, chunks)

        self.model = model
        return model
