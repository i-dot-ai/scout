# utils.py
import json
import logging.config
import os
import pathlib
from typing import Dict
from sqlalchemy import create_engine, text
from typing import List, Tuple
import dotenv
from langchain_community.llms.sagemaker_endpoint import LLMContentHandler
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from openai import APIConnectionError
from openai import AzureOpenAI
from openai import RateLimitError
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from scout.utils.storage.filesystem import S3StorageHandler
from scout.utils.storage.sqlite_storage_handler import SQLiteStorageHandler


def setup_logging(persistency_folder_path):
    log_file_path = os.path.join(persistency_folder_path, "app.log")
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.FileHandler",
                "filename": str(log_file_path),
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": True,
            },
            "scout": {
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


logger = logging.getLogger(__name__)


def api_call_with_retry(max_attempts=10, min_wait=4, max_wait=10):
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        before_sleep=lambda retry_state: logger.info(f"Retrying in {retry_state.next_action.sleep} seconds..."),
    )


class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps({"inputs": prompt, "parameters": model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


class SessionState:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionState, cls).__new__(cls)
            cls._instance.state = {}
        return cls._instance

    def set(self, key, value):
        self.state[key] = value

    def get(self, key, default=None):
        return self.state.get(key, default)


def init_session_state(
    persistency_folder_path: str = None,
    deploy_mode: bool = False,
) -> dict:
    """Initialise the session state for the app"""

    session_state = SessionState()

    # Load environment variables
    dotenv.load_dotenv(".env")
    ENV = dotenv.dotenv_values(".env")

    if "persistency_folder_path" not in dir(session_state) and not deploy_mode:
        if persistency_folder_path is not None:
            session_state.persistency_folder_path = pathlib.Path(".data/db" + "_" + persistency_folder_path)
        else:
            session_state.persistency_folder_path = pathlib.Path(".data/db")
        if not os.path.exists(session_state.persistency_folder_path):
            os.makedirs(session_state.persistency_folder_path)

    setup_logging(
        persistency_folder_path=session_state.persistency_folder_path
    )  # Set up logging as part of initialization
    logger.info("Initializing session state")

    if "storage_handler" not in dir(session_state):
        session_state.storage_handler = SQLiteStorageHandler(session_state.persistency_folder_path / "main.db")
        logger.info("SQLite storage handler initialized")

    if "s3_storage_handler" not in dir(session_state):
        s3_url = os.environ.get("S3_URL", None)
        if not s3_url:
            session_state.s3_storage_handler = S3StorageHandler(
                bucket_name=os.environ.get("BUCKET_NAME"),
                region_name=os.environ.get("S3_REGION"),
            )
            logger.info("AWS S3 storage handler initialized")
        else:
            logger.info("Connecting to minio...")
            session_state.s3_storage_handler = S3StorageHandler(
                os.environ.get("BUCKET_NAME"),
                endpoint_url=s3_url,
            )
            logger.info("Minio S3 storage handler initialized")

    if "llm" not in dir(session_state) and not deploy_mode:
        session_state.llm = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        )
        logger.info("Azure OpenAI LLM initialized")

    if "llm_summarizer" not in dir(session_state) and not deploy_mode:
        session_state.llm_summarizer = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment="gpt-35-turbo-16k",
        )
        logger.info("Azure OpenAI summarizer initialized")

    if "embedding_function" not in dir(session_state) and not deploy_mode:
        try:
            session_state.embedding_function = AzureOpenAIEmbeddings(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_deployment="text-embedding-3-large",
            )
            logger.info("Azure OpenAI embeddings initialized")
        except Exception as e:
            logger.error(f"Error initializing AzureOpenAIEmbeddings: {e}")
            raise

    if "topic_embedding_function" not in dir(session_state) and not deploy_mode:
        try:
            session_state.topic_embedding_function = AzureOpenAIEmbeddings(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_deployment="text-embedding-ada-002",
            )
        except Exception as e:
            print(f"Error initializing AzureOpenAIEmbeddings: {e}")
            raise

    if "vector_store" not in dir(session_state) and not deploy_mode:
        persist_directory = os.path.join(session_state.persistency_folder_path, "VectorStore")

        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        session_state.vector_store = Chroma(
            embedding_function=session_state.embedding_function,
            persist_directory=persist_directory,
        )
        logger.info("Vector store initialized")

    logger.info("Session state initialization completed")

    return ENV, session_state


def check_table_rows(connection_string: str, expected_counts: Dict[str, int]) -> List[Tuple[str, bool, int, int]]:
    """
    Check if tables have the expected number of rows within a threshold.

    Args:
        connection_string: Database connection string
        expected_counts: Dictionary mapping table names to their expected row counts

    Returns:
        List of tuples: (table_name, passed_check, actual_count, expected_count)
    """
    engine = create_engine(connection_string)
    results = []

    with engine.connect() as conn:
        for table_name, expected_count in expected_counts.items():
            try:
                # Get actual row count
                actual_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

                # Check if count is correct
                passed = actual_count == expected_count

                results.append((table_name, passed, actual_count, expected_count))

                # Print result
                status = "PASSED" if passed else "FAILED"
                print(f"{table_name}: {status} (Expected: {expected_count}, Actual: {actual_count})")

            except Exception as e:
                print(f"Error checking {table_name}: {str(e)}")
                results.append((table_name, False, -1, expected_count))

    # Print summary
    passed_count = sum(1 for r in results if r[1])
    print(f"\nTotal passed: {passed_count}/{len(results)} checks")

    return results
