import json
import os
from pathlib import Path

import boto3
from mypy_boto3_s3.client import S3Client

from models.dto.input import SolverInput
from models.dto.output import Output

__SOLVERS_BUCKET = os.environ.get('S3__SOLVERS_FILES__BUCKET_NAME')

s3: S3Client = boto3.client('s3')


def get_local_input_object(working_directory_path: Path) -> SolverInput:
    with open(working_directory_path / 'input.json') as f:
        data = json.loads(f.read())

    return SolverInput.parse_obj(data)


def save_local_output_object(working_directory_path: Path, output: Output) -> None:
    with open(working_directory_path / 'output.json', 'w') as f:
        f.write(output.json(by_alias=True, exclude_none=True) + "\n")


def save_local_txt_file(working_directory_path: Path, file_name: str, content: str) -> None:
    with open(working_directory_path / f"{file_name}.txt", 'w') as f:
        f.write(content)
