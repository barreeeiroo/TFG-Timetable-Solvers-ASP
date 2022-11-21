from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext


logger = Logger()
metrics = Metrics()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
def event_handler(event: dict, context: LambdaContext):
    logger.info(event)
    logger.info(context)
