from typing import List

from clyngor import ASP

from models.schedule import Schedule
from models.solver import Solver
from solvers.asp.constants import ClingoConstants as ClC
from solvers.asp.rules import Statements


class AspSolver(Solver):
    @staticmethod
    def __generate_asp_generator(statement_generator: Statements) -> str:
        statements = [
            statement_generator.generate_scheduled_units_store(),
            statement_generator.generate_scheduled_room_type_with_session_type_store(),
        ]
        return "\n".join(statements)

    @staticmethod
    def __generate_asp_definition(statement_generator: Statements) -> str:
        statements: List[str] = []

        statements.extend(statement_generator.generate_constraints())
        statements.append(statement_generator.generate_penalized_room_types())
        statements.extend(statement_generator.generate_undesirable_slots())
        statements.extend(statement_generator.generate_blocked_slots())

        return "\n".join(statements)

    @staticmethod
    def __generate_asp_data(statement_generator: Statements) -> str:
        statements: List[str] = [statement_generator.generate_timeslots()]

        statements.extend(statement_generator.generate_rooms())
        statements.extend(statement_generator.generate_sessions())

        return "\n".join(statements)

    def __generate_asp_problem(self) -> str:
        statements = Statements(self._settings, self._courses, self._rooms)

        generator = self.__generate_asp_generator(statements)
        definition = self.__generate_asp_definition(statements)
        data = AspSolver.__generate_asp_data(statements)

        return "\n\n".join([generator, definition, data, f"#show {ClC.ASSIGNED_SLOT}/4."])

    def solve(self) -> Schedule:
        asp_problem = self.__generate_asp_problem()
        print(asp_problem)

        solution = None
        for answer, optimization, optimality, answer_number in ASP(asp_problem).with_answer_number:
            solution = answer
            break

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned")

        print("---")
        print(solution)

        schedule = Schedule()
        return schedule