from clyngor import ASP

from models.schedule import Schedule
from models.solver import Solver


class AspSolver(Solver):
    def __generate_asp_definition(self) -> str:
        pass

    def solve(self) -> Schedule:
        asp_problem = self.__generate_asp_definition()

        solution = None
        for answer, optimization, optimality, answer_number in ASP(asp_problem).with_answer_number:
            solution = answer
            break

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned")

        schedule = Schedule()
        return schedule
