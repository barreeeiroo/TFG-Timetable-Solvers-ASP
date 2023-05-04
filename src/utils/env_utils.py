import os


def is_short_execution_environment() -> bool:
    return os.environ.get("SOLVERS_LAMBDA") is not None
