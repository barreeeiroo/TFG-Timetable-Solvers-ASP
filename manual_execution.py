import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


def get_api_url(path: str) -> str:
    api_url = os.environ.get("TFG_API_URL", None)
    if not api_url:
        raise RuntimeError("Missing API URL")

    return f"{api_url}/{path}"


def get_api_key() -> str:
    api_key = os.environ.get("TFG_API_KEY", None)
    if not api_key:
        raise RuntimeError("Missing API Key")

    return api_key


def upload_s3_file(file: Path, url: str, fields: Dict):
    with open(file, 'rb') as f:
        files = {'file': (file.name, f)}
        response = requests.post(url, data=fields, files=files)

    if response.status_code != 204:
        raise RuntimeError(f"Failed to upload {file.name}")

    print(f"Uploaded {file.name}")


def api_create_manual_scheduler_execution(source_execution_id: str, alias: Optional[str] = None) -> Tuple[str, str]:
    url = get_api_url("create-manual-scheduler-execution")
    body = {
        'sourceExecutionId': source_execution_id,
    }
    if alias:
        body['alias'] = alias

    response = requests.post(url, headers={'X-API-Key': get_api_key()}, json=body)
    data = response.json()
    if response.status_code // 200 > 2:
        raise RuntimeError(f"API Error: {data['message']}")
    return data["executionId"], data["inputFileUrl"]


def api_retarget_manual_scheduler_execution(source_execution_id: str) -> Tuple[str, str]:
    url = get_api_url("retarget-manual-scheduler-execution")
    body = {
        'sourceExecutionId': source_execution_id,
    }

    response = requests.post(url, headers={'X-API-Key': get_api_key()}, json=body)
    data = response.json()
    if response.status_code // 200 > 2:
        raise RuntimeError(f"API Error: {data['message']}")
    return data["executionId"], data["inputFileUrl"]


def api_generate_manual_scheduler_execution_upload(execution_id: str,
                                                   additional_files: Optional[List[str]] = None) -> Tuple[
    Tuple[str, Dict],
    Dict[str, Tuple[str, Dict]],
]:
    url = get_api_url("generate-manual-scheduler-execution-upload")
    body = {
        'executionId': execution_id,
    }
    if additional_files:
        body['additionalFiles'] = additional_files

    response = requests.post(url, headers={'X-API-Key': get_api_key()}, json=body)
    data = response.json()
    if response.status_code // 200 > 2:
        raise RuntimeError(f"API Error: {data['message']}")

    output_file_url = (data["outputFileUploadUrl"]["url"], data["outputFileUploadUrl"]["fields"],)
    additional_files_urls = dict()
    if additional_files:
        for additional_file in additional_files:
            additional_files_urls[additional_file] = (
                data["additionalFilesUploadUrls"][additional_file]["url"],
                data["additionalFilesUploadUrls"][additional_file]["fields"],
            )
    return output_file_url, additional_files_urls


def api_process_manual_scheduler_execution(execution_id: str) -> None:
    url = get_api_url("process-manual-scheduler-execution")
    body = {
        'executionId': execution_id,
    }

    response = requests.post(url, headers={'X-API-Key': get_api_key()}, json=body)
    if response.status_code // 200 > 2:
        data = response.json()
        raise RuntimeError(f"API Error: {data['message']}")


def create_manual_execution(source_execution_id: str, alias: Optional[str] = None):
    invocation_dir = Path().absolute()

    execution_id_file = invocation_dir / '.asp_execution_id'
    if execution_id_file.exists():
        raise RuntimeError("There is an invocation here already")

    execution_id, input_file_url = api_create_manual_scheduler_execution(source_execution_id, alias)

    input_data = requests.get(input_file_url).text
    with open(invocation_dir / 'input.json', 'w') as f:
        f.write(input_data)

    with open(execution_id_file, 'w') as f:
        f.write(execution_id)

    print(f"Manual Scheduler Execution {execution_id} is now ready and waiting to receive the processed files")


def retarget_manual_execution(source_execution_id: str):
    invocation_dir = Path().absolute()

    execution_id_file = invocation_dir / '.asp_execution_id'
    if execution_id_file.exists():
        raise RuntimeError("There is an invocation here already")

    print("Retargeting and generating input.json; this may take a while...")
    execution_id, input_file_url = api_retarget_manual_scheduler_execution(source_execution_id)

    input_data = requests.get(input_file_url).text
    with open(invocation_dir / 'input.json', 'w') as f:
        f.write(input_data)

    with open(execution_id_file, 'w') as f:
        f.write(execution_id)

    print(f"Manual Scheduler Execution {execution_id} is now ready and waiting to receive the processed files")


def upload_manual_execution():
    invocation_dir = Path().absolute()

    execution_id_file = invocation_dir / '.asp_execution_id'
    if not execution_id_file.exists():
        raise RuntimeError("There is no invocation here")

    with open(execution_id_file) as f:
        execution_id = f.read().strip()

    asp_files = [f.replace(".txt", "") for f in os.listdir(invocation_dir)
                 if (invocation_dir / f).is_file() and f.startswith("asp_") and f.endswith(".txt")]

    output_file_url, additional_files_urls = api_generate_manual_scheduler_execution_upload(execution_id, asp_files)

    output_file = invocation_dir / 'output.json'
    if output_file.exists():
        upload_s3_file(output_file, output_file_url[0], output_file_url[1])

    for asp_filename in asp_files:
        asp_file_name = invocation_dir / f"{asp_filename}.txt"
        additional_file_url = additional_files_urls[asp_filename]
        upload_s3_file(asp_file_name, additional_file_url[0], additional_file_url[1])


def finalize_manual_execution():
    invocation_dir = Path().absolute()

    execution_id_file = invocation_dir / '.asp_execution_id'
    if not execution_id_file.exists():
        raise RuntimeError("There is no invocation here")

    with open(execution_id_file) as f:
        execution_id = f.read().strip()

    api_process_manual_scheduler_execution(execution_id)

    print(f"Manual Scheduler Execution {execution_id} is now flagged as completed")


def main():
    parser = argparse.ArgumentParser(
        prog="TFG Timetable Manual Scheduler Executions Helper",
        description="Command-line tool to interact with the Internal API and manage manual scheduler executions."
    )

    sub_parsers = parser.add_subparsers(title="mode", dest="mode", required=True)

    parser_start = sub_parsers.add_parser('start', help='Create a Manual Scheduler Execution and retrieve input.json')
    parser_start.add_argument('-s', '--source-execution-id',
                              help='Source Scheduler Execution ID from which to retrieve the input files',
                              type=str, required=True)
    parser_start.add_argument('-a', '--alias',
                              help='Alias for this Scheduler Execution',
                              type=str)

    parser_retarget = sub_parsers.add_parser('retarget', help='Retarget a normal Scheduler Execution to a Manual one '
                                                              'and retrieve input.json')
    parser_retarget.add_argument('-s', '--source-execution-id',
                                 help='Source Scheduler Execution ID to retarget and retrieve the input files',
                                 type=str, required=True)

    parser_upload = sub_parsers.add_parser('upload',
                                           help='Upload the generated files (output.json if present and asp.txt ones)')

    parser_finish = sub_parsers.add_parser('finish',
                                           help='Upload the generated files and mark Scheduler Execution as finished')

    args = parser.parse_args()
    if args.mode == "start":
        create_manual_execution(args.source_execution_id, args.alias)
    if args.mode == "retarget":
        retarget_manual_execution(args.source_execution_id)
    elif args.mode == "upload":
        upload_manual_execution()
    elif args.mode == "finish":
        upload_manual_execution()
        finalize_manual_execution()
    else:
        raise NotImplementedError(f"How's {args.mode} even possible?")


if __name__ == "__main__":
    main()
