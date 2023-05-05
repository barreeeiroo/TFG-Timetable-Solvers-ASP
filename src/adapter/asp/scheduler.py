from aws_lambda_powertools import Logger
from clyngor import solve

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP
from adapter.asp.rules import Rules
from adapter.time.week import Week
from models.dto.output import Output
from models.schedule import ScheduleUnit
from models.solver import Solver
from sdk.aws_s3 import save_txt_file
from utils.env_utils import is_short_execution_environment

logger = Logger()


class AspSolver(Solver):
    def solve(self) -> Output:
        week = Week(self._settings)
        rules = Rules(week, self._sessions, self._rooms)
        asp_problem = rules.generate_asp_problem()

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_problem", asp_problem)
        else:
            print(asp_problem)

        models = solve(
            inline=asp_problem,
            use_clingo_module=False,
            stats=True,
            time_limit=int(60 * (15.5 if is_short_execution_environment() else 58)),
        )
        solution = None
        for answer, optimization, optimality, answer_number in models.with_answer_number:
            # Keep retrieving answers till timeout
            solution = answer
            if not optimality:
                if self._execution_uuid is not None:
                    logger.info(f"Found solution #{answer_number} with {optimization} penalty")
                else:
                    print(f"Found solution #{answer_number} with {optimization} penalty")

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned")

        if self._execution_uuid is not None:
            assigned_slot_lines = [f"{variables[0]}\t{variables[1]}\t{variables[2]}\n"
                                   for predicate, variables in solution
                                   if predicate == ClP.ASSIGNED_SLOT]
            save_txt_file(self._execution_uuid, "asp_solution", "".join(assigned_slot_lines))

            optimization_lines = [f"{predicate}\t\t{variables[0]}\t{variables[1]}\t{variables[2]}\t{variables[3]}\n"
                                  for predicate, variables in solution
                                  if predicate in (ClP.PENALTY, ClP.BONUS,)]
            save_txt_file(self._execution_uuid, "asp_optimization", "".join(optimization_lines))

            statistics_lines = [f"{key}\t{value}\n"
                                for key, value in models.statistics.items()]
            save_txt_file(self._execution_uuid, "asp_statistics", "".join(statistics_lines))
        else:
            print("---")
            print(solution)

        output = Output()
        for predicate, variables in solution:
            if predicate != ClP.ASSIGNED_SLOT:
                continue

            timeslot, clingo_session, clingo_room = variables
            session_hex, room_hex = ClN.get_id_from_clingo(clingo_session), ClN.get_id_from_clingo(clingo_room)
            output.timetable.append(ScheduleUnit(
                slot=week.get_slot_by_number(timeslot - 1),
                session=self._find_session_by_hex(session_hex),
                room=self._find_room_by_hex(room_hex),
            ))

        return output
