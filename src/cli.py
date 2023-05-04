import argparse
import json
from pathlib import Path

from adapter.asp.scheduler import AspSolver
from models.dto.input import SolverInput
from sdk.aws_s3 import get_input_object, save_output_object


def aws_execution(execution_arn: str):
    execution_uuid = execution_arn.split(":")[-1]
    print(f"Execution UUID: {execution_uuid}")

    input_data = get_input_object(execution_uuid)

    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    solver.with_execution_uuid(execution_uuid)
    output = solver.solve()

    object_key = save_output_object(execution_uuid, output)


def local_execution(input_file_path_raw: str):
    input_file_path = Path(input_file_path_raw)
    with open(input_file_path) as f:
        data = json.loads(f.read())
    input_data = SolverInput.parse_obj(data)

    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    output = solver.solve()

    with open(input_file_path.parent / 'output.json', 'w') as f:
        f.write(output.json(by_alias=True, exclude_none=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ASP Solver',
        description='Schedule timetables using Clingo ASP')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--executionArn', type=str, help="AWS State Machine Execution ARN")
    group.add_argument('-f', '--inputFile', type=str, help="input.json file path")
    args = parser.parse_args()

    if args.executionArn:
        aws_execution(args.executionArn)
    elif args.inputFile:
        local_execution(args.inputFile)
    else:
        raise NotImplementedError("Unknown Invocation")
