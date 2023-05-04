import json
import os

import boto3
from mypy_boto3_s3.client import S3Client

from models.dto.input import SolverInput
from models.dto.output import Output

__SOLVERS_BUCKET = os.environ.get('S3__SOLVERS_FILES__BUCKET_NAME')

s3: S3Client = boto3.client('s3')


def get_input_object(execution_uuid: str) -> SolverInput:
    object_key = f"{execution_uuid}/input.json"
    print(f"Fetching object {object_key} from bucket {__SOLVERS_BUCKET}")

    content_object = s3.get_object(
        Bucket=__SOLVERS_BUCKET,
        Key=object_key
    )
    file_content = content_object["Body"].read().decode(encoding="utf-8")
    json_content = json.loads(file_content)

    return SolverInput(**json_content)


def save_output_object(execution_uuid: str, output: Output) -> str:
    object_key = f"{execution_uuid}/output.json"
    print(f"Storing object {object_key} in bucket {__SOLVERS_BUCKET}")

    s3.put_object(
        Body=output.json(by_alias=True, exclude_none=True),
        Bucket=__SOLVERS_BUCKET,
        Key=object_key
    )

    return object_key


def save_txt_file(execution_uuid: str, file_name: str, content: str) -> str:
    object_key = f"{execution_uuid}/{file_name}.txt"
    print(f"Storing object {object_key} in bucket {__SOLVERS_BUCKET}")

    s3.put_object(
        Body=content,
        Bucket=__SOLVERS_BUCKET,
        Key=object_key
    )

    return object_key
