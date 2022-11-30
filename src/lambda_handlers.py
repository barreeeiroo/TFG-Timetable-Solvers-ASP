from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from adapter.asp.scheduler import AspSolver
from sdk.aws_s3 import get_input_object, save_output_object
from utils.settings import generate_settings

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

    input_data = get_input_object(execution_uuid)
    logger.info("Received INPUT")
    logger.info(input_data)

    logger.info("Generating settings...")
    settings = generate_settings()
    logger.info("Creating ASP Solver")
    solver = AspSolver(input_data.sessions, input_data.rooms, settings)
    logger.info("Invoking ASP Solver")
    output = solver.solve()

    logger.info("Storing OUTPUT")
    object_key = save_output_object(execution_uuid, output)
    return {
        "result": object_key
    }
