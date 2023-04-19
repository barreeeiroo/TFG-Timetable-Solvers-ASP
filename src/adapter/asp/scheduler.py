from clyngor import solve

from adapter.asp.rules import Rules
from adapter.asp.constants import ClingoNaming as ClN
from adapter.time.week import Week
from models.dto.output import Output
from models.schedule import ScheduleUnit
from models.solver import Solver
from sdk.aws_s3 import save_txt_file


class AspSolver(Solver):
    def solve(self) -> Output:
        week = Week(self._settings)
        rules = Rules(week, self._sessions, self._rooms)
        asp_problem = rules.generate_asp_problem()

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_problem", asp_problem)
        else:
            print(asp_problem)

        solution = None
        for answer, optimization, optimality, answer_number in solve(inline=asp_problem,
                                                                     use_clingo_module=False).with_answer_number:
            solution = answer
            break

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned")

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_solution", solution)
        else:
            print("---")
            print(solution)

        output = Output()
        for _, (timeslot, clingo_session, clingo_room) in solution:
            session_hex, room_hex = ClN.get_id_from_clingo(clingo_session), ClN.get_id_from_clingo(clingo_room)
            output.timetable.append(ScheduleUnit(
                slot=week.get_slot_by_number(timeslot - 1),
                session=self._find_session_by_hex(session_hex),
                room=self._find_room_by_hex(room_hex),
            ))

        return output
