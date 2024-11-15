import csv
import os
from typing import List

from scout.DataIngest.models.schemas import CriterionCreate as Criterion
from scout.utils.storage.storage_handler import BaseStorageHandler
from scout.utils.utils import logger


def load_criteria_csv_to_storage(
    storage_handler: BaseStorageHandler,
    file_path: str,
) -> int:
    """
    Uploads criteria from a single csv to the database.

    Args:
        folder_path (str): Path to the folder containing criteria CSVs.
            CSV files should be named after their gate and have the headings:
            "Category", "Question", "Evidence", "Gate".
        Storage Handler: Session state object.

    Returns:
        int: Number of records uploaded.

    Raises:
        FileNotFoundError: If the folder_path doesn't exist.
        ValueError: If a CSV file is empty or has incorrect headers.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The folder '{file_path}' does not exist.")

    header_mapping = {
        "Category": "category",
        "Question": "question",
        "Evidence": "evidence",
        "Gate": "gate",
    }

    records_uploaded = 0

    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if not reader.fieldnames:
                raise ValueError(f"The CSV file '{file_path}' is empty or has no headers.")
            for row in reader:
                mapped_row = {header_mapping.get(k, k): v.strip() for k, v in row.items()}
                try:
                    model_instance = Criterion(**mapped_row)
                    storage_handler.write_item(model_instance)
                    records_uploaded += 1
                except Exception as e:
                    logger.error(f"Error processing row in '{file_path}': {e}")
                    continue

    except Exception as e:
        logger.error(f"Error reading from file '{file_path}': {e}")

    logger.info(f"Successfully uploaded {records_uploaded} criteria to db.")
    return records_uploaded


def ingest_criteria_from_local_dir(
    gate_filepaths: List[str],
    storage_handler: BaseStorageHandler,
) -> None:
    """
    Ingest criteria from CSV files into the database.
    """
    [
        load_criteria_csv_to_storage(storage_handler=storage_handler, file_path=gate_filepath)
        for gate_filepath in gate_filepaths
    ]
    logger.info("Successfully ingested criteria")
