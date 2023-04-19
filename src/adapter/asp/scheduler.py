from clyngor import solve

from adapter.asp.rules import Rules
from adapter.time.week import Week
from models.dto.output import Output
from models.solver import Solver
from sdk.aws_s3 import save_txt_file


class AspSolver(Solver):
    def solve(self) -> Output:
        rules = Rules(Week(self._settings), self._sessions, self._rooms)
        asp_problem = rules.generate_asp_problem()

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_problem", asp_problem)
        else:
            print(asp_problem)

        solution = None
        for answer, optimization, optimality, answer_number in solve(inline=asp_problem,
                                                                     use_clingo_module=False,
                                                                     subproc_shell=True).with_answer_number:
            solution = answer
            break

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned")

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_solution", solution)
        else:
            print("---")
            print(solution)

        timetable = Output()
        return timetable
