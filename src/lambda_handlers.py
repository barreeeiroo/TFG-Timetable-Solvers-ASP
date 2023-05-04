from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from adapter.asp.scheduler import AspSolver
from sdk.aws_s3 import get_input_object, save_output_object

logger = Logger()
metrics = Metrics()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
def event_handler(event: dict, context: LambdaContext):
    execution_id = str(event["execution"])
    execution_uuid = execution_id.split(":")[-1]
    logger.info(f"Execution UUID: {execution_uuid}")

    logger.info("Reading INPUT")
    input_data = get_input_object(execution_uuid)

    logger.info("Creating ASP Solver")
    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    solver.with_execution_uuid(execution_uuid)
    logger.info("Invoking ASP Solver")
    output = solver.solve()

    logger.info("Storing OUTPUT")
    object_key = save_output_object(execution_uuid, output)

    return {
        "result": object_key
    }
