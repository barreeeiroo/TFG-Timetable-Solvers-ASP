import argparse
from pathlib import Path
from typing import Optional

from business.scheduler import AspSolver
from sdk.aws_s3 import get_input_object, save_output_object
from sdk.local_fs import get_local_input_object, save_local_output_object


def aws_execution(execution_arn: str):
    execution_uuid = execution_arn.split(":")[-1]
    print(f"Execution UUID: {execution_uuid}")

    input_data = get_input_object(execution_uuid)

    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    solver.with_execution_uuid(execution_uuid)
    output = solver.solve()

    object_key = save_output_object(execution_uuid, output)
    print(f"File saved in S3: {object_key}")


def local_execution(working_directory_path_raw: str, timeout: Optional[int]):
    working_directory_path = Path(working_directory_path_raw)
    input_data = get_local_input_object(working_directory_path)

    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    solver.with_local_working_directory(working_directory_path)
    if timeout is not None and timeout > 0:
        solver.with_timeout(timeout)
    output = solver.solve()

    save_local_output_object(working_directory_path, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ASP Solver',
        description='Schedule timetables using Clingo ASP')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--executionArn', type=str, help="AWS State Machine Execution ARN")
    group.add_argument('-f', '--workDir', type=str, help="Local working directory with input.json file")
    parser.add_argument('-t', '--timeout', type=float, help="Clingo will timeout after these minutes have passed")
    args = parser.parse_args()

    if args.executionArn:
        aws_execution(args.executionArn)
    elif args.workDir:
        local_execution(args.workDir, args.timeout)
    else:
        raise NotImplementedError("Unknown Invocation")
