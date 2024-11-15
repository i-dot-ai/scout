from typing import List

from langchain_community.vectorstores import Chroma
from langchain_core.vectorstores import VectorStore
from openai import AzureOpenAI

from scout.DataIngest.models.schemas import (
    Criterion,
    CriterionCreate,
    CriterionFilter,
    CriterionGate,
    ProjectCreate,
    ProjectFilter,
    ResultCreate,
)
from scout.LLMFlag.evaluation import MainEvaluator
from scout.utils.storage.postgres_storage_handler import PostgresStorageHandler
from scout.utils.utils import logger


def get_criteria_for_gate(gate_review: CriterionGate, storage_handler: PostgresStorageHandler) -> List[Criterion]:
    filter = CriterionFilter(gate=gate_review)
    criteria = storage_handler.get_item_by_attribute(filter)
    return criteria


def evaluate_questions_for_project(
    project: ProjectCreate,
    storage_handler: PostgresStorageHandler,
    criteria: List[CriterionCreate],
    llm: AzureOpenAI,
    vector_store: Chroma = None,
) -> List[ResultCreate]:
    evaluator = MainEvaluator(
        project=project,
        vector_store=vector_store,
        llm=llm,
        storage_handler=storage_handler,
    )
    results = evaluator.evaluate_questions(criteria=criteria, save=True)
    return results


def generate_llm_flags_for_project(
    project_name: str,
    storage_handler: PostgresStorageHandler,
    llm: AzureOpenAI,
    vector_store: VectorStore,
    gate_review: CriterionGate,
):
    """
    For a given project, use an LLM to determine if the project meets the criteria
    for the specified gate.
    The results of this evaluation are saved to the database in the `result` table.
    """
    filter = ProjectFilter(name=project_name)
    project = storage_handler.get_item_by_attribute(filter)[-1]

    criteria = get_criteria_for_gate(gate_review=gate_review, storage_handler=storage_handler)
    logger.info(f"{len(criteria)} criteria loaded")

    evaluate_questions_for_project(
        project=project, storage_handler=storage_handler, criteria=criteria, llm=llm, vector_store=vector_store
    )
