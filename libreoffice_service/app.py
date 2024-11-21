import logging
import os
import subprocess
import tempfile

import boto3
from botocore.client import Config
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

BUCKET_NAME = os.environ["BUCKET_NAME"]


class ConversionRequest(BaseModel):
    input_key: str


class ConversionResponse(BaseModel):
    success: bool
    output_key: str


class HealthResponse(BaseModel):
    status: bool


def transform_file_path(input_path):
    """
    Transform a file path by replacing 'raw' directory with 'processed' and changing extension to .pdf
    while maintaining the rest of the directory structure.
    
    Args:
        input_path (str): Original file path (e.g., 'project/raw/subfolder/file.docx')
        
    Returns:
        str: Transformed file path (e.g., 'project/processed/subfolder/file.pdf')
        
    Example:
        >>> transform_file_path('example_project/raw/test_folder/document.docx')
        'example_project/processed/test_folder/document.pdf'
    """
    # Normalize path separators for the current OS
    input_path = os.path.normpath(input_path)
    
    # Split the path into parts
    parts = input_path.split(os.sep)
    
    # Find the 'raw' directory index
    try:
        raw_index = parts.index('raw')
    except ValueError:
        raise ValueError("Input path must contain a 'raw' directory")
    
    # Replace 'raw' with 'processed'
    parts[raw_index] = 'processed'
    
    # Get the filename and change extension to .pdf
    filename = os.path.splitext(parts[-1])[0] + '.pdf'
    parts[-1] = filename
    
    # Join all parts back together
    return os.sep.join(parts)


@app.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status=True)


@app.post("/convert")
async def convert_file(request: ConversionRequest) -> ConversionResponse:
    input_key = request.input_key
    logger.info(f"Received request for conversion: {request}")
    output_key = transform_file_path(input_key)

    try:
        logger.info(f"Downloading file from S3: {input_key}")
        response = s3.get_object(Bucket=BUCKET_NAME, Key=input_key)
        file_content = response["Body"].read()
    except Exception as e:
        logger.error(f"Failed to download file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info(f"Using temporary directory: {tmpdir}")
        input_path = os.path.join(tmpdir, os.path.basename(input_key))
        output_path = os.path.join(tmpdir, f"{os.path.splitext(os.path.basename(input_key))[0]}.pdf")

        with open(input_path, "wb") as f:
            f.write(file_content)

        # Convert file
        try:
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, input_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

        with open(output_path, "rb") as f:
            output_content = f.read()

    # Upload converted file to S3 from memory
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=output_key, Body=output_content)
    except Exception as e:
        logger.error(f"Failed to upload converted file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload converted file: {str(e)}")

    logger.info(f"Successfully converted file: {output_key}")
    return ConversionResponse(success=True, output_key=output_key)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
