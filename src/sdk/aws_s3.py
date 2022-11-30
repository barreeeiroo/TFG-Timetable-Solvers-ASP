import json
import os

import boto3
from aws_lambda_powertools import Logger
from mypy_boto3_s3.client import S3Client

from models.dto.input import Input
from models.dto.output import Output

logger = Logger()


def get_input_object(execution_uuid: str) -> Input:
    s3: S3Client = boto3.client('s3')
    bucket = os.environ.get('S3_SOLVERS_FILES_BUCKET_NAME')
    object_key = f"{execution_uuid}/input.json"
    logger.info(f"Fetching object {object_key} from bucket {bucket}")

    content_object = s3.get_object(
        Bucket=bucket,
        Key=object_key
    )
    file_content = content_object["Body"].read().decode(encoding="utf-8")
    json_content = json.loads(file_content)
    logger.info(json_content)

    return Input(**json_content)


def save_output_object(execution_uuid: str, output: Output) -> str:
    s3: S3Client = boto3.client('s3')
    bucket = os.environ.get('S3_SOLVERS_FILES_BUCKET_NAME')
    object_key = f"{execution_uuid}/output.json"
    logger.info(f"Storing object {object_key} in bucket {bucket}")

    s3.put_object(
        Body=output.json(exclude_none=True),
        Bucket=bucket,
        Key=object_key
    )
    logger.info(f"Object stored")

    return object_key
