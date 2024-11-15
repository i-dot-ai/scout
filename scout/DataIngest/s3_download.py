import os
from typing import Union
from urllib.parse import ParseResult, unquote, urlparse

import requests


def convert_to_pdf_from_s3(s3_file_keys: list[str]) -> list[str]:
    # keys of converted files in s3.
    s3_converted_file_keys = []

    # send files to libreoffice service
    for s3_file_key in s3_file_keys:
        response = requests.post(f"{os.getenv('LIBREOFFICE_SERVICE_URL')}/convert", json={"input_key": s3_file_key})
        assert response.status_code == 200, f"Failed to convert file {s3_file_key}"
        s3_converted_file_keys.append(response.json()["output_key"])

    return s3_converted_file_keys


def extract_bucket_key(url: Union[str, ParseResult]) -> str:
    """
    Extract the bucket key from a presigned S3 URL (local or MinIO).

    Args:
        url (Union[str, ParseResult]): The presigned URL, either as a string or ParseResult object

    Returns:
        str: The bucket key (path to the object without bucket name)

    Example:
        >>> url = "http://localhost:9000/test-bucket/test-data/processed/document.pdf?X-Amz-Algorithm=..."
        >>> extract_bucket_key(url)
        'test-data/processed/document.pdf'
    """
    # Parse URL if string is provided
    if isinstance(url, str):
        parsed_url = urlparse(url)
    else:
        parsed_url = url

    # Split the path into components
    # Remove empty strings and decode URL-encoded characters
    path_parts = [unquote(p) for p in parsed_url.path.split("/") if p]

    # The first component after the host is the bucket name
    # Everything after that is the key
    if len(path_parts) < 2:
        raise ValueError("URL does not contain a valid bucket and key path")

    # Join all parts after the bucket name to form the key
    bucket_key = "/".join(path_parts[1:])

    return bucket_key


def s3_key_from_presigned_url(url):
    key = extract_bucket_key(url)
    return key
