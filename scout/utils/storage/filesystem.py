import base64
import logging
import os
from typing import List

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import PartialCredentialsError
from dotenv import load_dotenv
from pydantic import ValidationError
from yarl import URL

from scout.DataIngest.models.schemas import FileCreate as File
from scout.utils.storage.storage_handler import BaseStorageHandler

logger = logging.getLogger(__name__)


load_dotenv()

class S3StorageHandler(BaseStorageHandler):
    def __init__(
        self,
    ):
        self.bucket_name = os.environ.get("BUCKET_NAME")
        logger.info(f"Bucket name: {self.bucket_name}")

        self.prefix = ""
        self.dev = False if os.environ.get("DEV").lower() == "false" else True

        # Initialize S3 client
        self.region_name = os.environ.get("AWS_REGION", "eu-west-2")
        self.endpoint_url = os.environ.get("S3_URL")

        # Initialize S3 client
        if self.dev:
            # Use environment variables for authentication in dev mode
            logger.info("Connecting to minio...")
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                region_name=self.region_name,
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
                config=boto3.session.Config(signature_version="s3v4"),
            )
            # Create the bucket if it doesn't exist
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Successfully created bucket: {self.bucket_name}")
            except self.s3_client.exceptions.BucketAlreadyOwnedByYou:
                logger.info(f"Bucket {self.bucket_name} already exists and is owned by you.")
            except Exception as e:
                logger.error(f"Error creating bucket: {e}")
        else:
            # Use no authentication for production mode
            logger.info("Connecting to S3...")
            self.s3_client = boto3.client("s3", config=Config(region_name=self.region_name))

    def _add_prefix(self, key: str) -> str:
        """Add the app-data/ prefix to the given key."""
        if self.dev:
            return key
        else:
            return key

    def get_pre_signed_url(self, key: str):
        return URL(
            self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
            )
        )

    def write_item(self, file_path: str, key: str = None):
        """Write a file from a given path to the data store, overwriting if the file is 'latest.db'"""
        try:
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=key,
            )
            print(f"Successfully uploaded {file_path} to {key} in bucket {self.bucket_name}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credentials error: {e}")
        except Exception as e:
            print(f"Error writing item: {e}")

    def write_items(self, file_paths: List[str], project_name: str):
        """Write a list of files from given paths to the data store"""
        for file_path in file_paths:
            self.write_item(file_path, project_name)

    def read_item(self, item_key: str):
        """Read an object from a data store"""
        try:
            prefixed_key = self._add_prefix(item_key)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=prefixed_key)
            content = response["Body"].read()
            encoded_content = base64.b64encode(content).decode("utf-8")

            return encoded_content
        except self.s3_client.exceptions.NoSuchKey:
            print(f"Item with key {prefixed_key} not found.")
            raise self.s3_client.exceptions.NoSuchKey
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credentials error: {e}")
            raise e
        except Exception as e:
            print(f"Error reading item: {e}")
            raise e

    def read_items(self, item_uuids: List[str], project_name: str):
        """Read a list of objects from a data store"""
        return [self.read_item(item_uuid, project_name) for item_uuid in item_uuids]

    def update_item(self, item_uuid: str, item: File, project_name: str):
        """Update an object in a data store"""
        self.write_item(item_uuid, project_name)

    def update_items(self, item_uuids: List[str], items: List[File], project_name: str):
        """Update a list of objects in a data store"""
        for item in items:
            self.update_item(item.uuid, item, project_name)

    def delete_item(self, item_uuid: str, project_name: str):
        """Delete an object from a data store"""
        try:
            item_key = self._add_prefix(f"{project_name}/File/{item_uuid}.json")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=item_key)
        except self.s3_client.exceptions.NoSuchKey:
            print(f"Item with key {item_key} not found.")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credentials error: {e}")
        except Exception as e:
            print(f"Error deleting item: {e}")

    def delete_items(self, item_uuids: List[str], project_name: str):
        """Delete a list of objects from a data store"""
        for item_uuid in item_uuids:
            self.delete_item(item_uuid, project_name)

    def list_all_items(self, project_name: str, keep_file_extension: bool = False):
        """List all objects of a given type from a data store"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self._add_prefix(f"{project_name}"),
                # Bucket=self.bucket_name, Prefix=self.prefix
            )
            if "Contents" in response:
                if keep_file_extension:
                    return [item["Key"].split("/")[-1] for item in response["Contents"]]
                else:
                    return [item["Key"].split("/")[-1].split(".")[0] for item in response["Contents"]]
            else:
                return []
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credentials error: {e}")
        except Exception as e:
            print(f"Error listing items: {e}")

    def list_all_items_with_full_path(self, project_name: str = "test-data/raw/"):
        """lists all items in a given dir with full path appended"""
        return [project_name + item for item in self.list_all_items(project_name, keep_file_extension=True)]

    def presigned_url_list(self, project_name: str):
        """List all presigned urls for a given project"""

        return [
            self.get_pre_signed_url(project_name + key)
            for key in self.list_all_items(project_name, keep_file_extension=True)
        ]

    def read_all_items(self, project_name: str):
        """Read all objects of a given type from a data store"""
        item_uuids = self.list_all_items(project_name)
        return self.read_items(item_uuids, project_name)

    def write_log(self, key: str, body: str):
        """Write a file from a given path to the data store"""
        if self.bucket_name != "logs":
            raise ValueError("Logs can only be written in a log bucket!")
        prefixed_key = self._add_prefix(key)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=prefixed_key,
            Body=body,
            ContentType="application/json",
        )

    def verify_connection(self):
        try:
            # Try to list objects in the bucket (limited to 1 to minimize data transfer)
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            print(f"Successfully connected to bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchBucket":
                print(f"Bucket {self.bucket_name} does not exist.")
            elif error_code == "AccessDenied":
                print(f"Access denied to bucket {self.bucket_name}. Check your permissions.")
            else:
                print(f"Error connecting to bucket {self.bucket_name}: {e}")
            raise  # Re-raise the exception after logging

    def get_item_by_attribute(self):
        raise NotImplementedError

    def upload_folder_contents(
        self,
        folder_path: str,
        recursive: bool = False,
        prefix: str = "test-data/raw/",
        allowed_extensions: List[str] = ["pdf", "docx", "doc", "txt", "pptx", "ppt"],
    ) -> List[str]:
        # This assumes no duplicate file names in the folder
        output_keys = []
        for file_path in os.listdir(folder_path):
            if file_path.split(".")[-1] in allowed_extensions:
                self.write_item(folder_path + "/" + file_path, key=prefix + file_path)
                output_keys.append(prefix + file_path)
        if recursive:
            for subfolder in os.listdir(folder_path):
                output_keys.extend(
                    self.upload_folder_contents(os.path.join(folder_path, subfolder), recursive=True, prefix=prefix)
                )
        return output_keys
