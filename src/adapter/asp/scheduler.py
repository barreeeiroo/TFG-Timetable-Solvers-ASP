from datetime import timedelta

from aws_lambda_powertools import Logger
from clyngor import solve

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP
from adapter.asp.rules import Rules
from adapter.time.week import Week
from models.dto.output import Output
from models.schedule import ScheduleUnit
from models.solver import Solver
from sdk.aws_s3 import save_txt_file
from sdk.local_fs import save_local_txt_file
from utils.env_utils import is_short_execution_environment

logger = Logger()


class AspSolver(Solver):
    def solve(self) -> Output:
        week = Week(self._settings)
        rules = Rules(week, self._sessions, self._rooms)
        asp_problem = rules.generate_asp_problem()

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_problem", asp_problem)
        elif self._local_dir is not None:
            save_local_txt_file(self._local_dir, "asp_problem", asp_problem)
        else:
            print(asp_problem)

        # 1 hour
        time_limit = 60 * 60
        if is_short_execution_environment():
            # 15 minutes
            time_limit = 60 * 15
        elif self._timeout is not None:
            time_limit = self._timeout
        time_limit = timedelta(seconds=time_limit)

        # Add a 2.5% of buffer time for output file processing, between 30 seconds and 5 minutes
        out_buffer_time = time_limit.total_seconds() * 0.025
        if out_buffer_time < (60 * 0.5):
            out_buffer_time = 60 * 0.5
        elif out_buffer_time > (60 * 5.):
            out_buffer_time = 60 * 5.
        out_buffer_time = timedelta(seconds=out_buffer_time)

        actual_timeout = time_limit - out_buffer_time

        if self._execution_uuid is not None:
            logger.info({
                "originalTimeout": str(time_limit),
                "outBufferTime": str(out_buffer_time),
                "actualTimeout": str(actual_timeout),
            }, extra={"execution": self._execution_uuid})
        else:
            print("Original Timeout", time_limit, "|",
                  "Out Buffer Time", out_buffer_time, "|",
                  "Actual Timeout", actual_timeout)

        models = solve(
            inline=asp_problem,
            use_clingo_module=False,
            stats=True,
            time_limit=int(actual_timeout.total_seconds()),
        )
        solution, found_optimal = None, False
        for answer, optimization, optimality, answer_number in models.with_answer_number:
            # Keep retrieving answers till timeout
            solution = answer
            if not optimality:
                text = f"Found solution #{answer_number} with {optimization} penalty"
                if self._execution_uuid is not None:
                    logger.info(text, extra={"execution": self._execution_uuid})
                else:
                    print(text)
            else:
                found_optimal = True

        status = "UNKNOWN"
        if solution is not None and not found_optimal:
            status = "SATISFIABLE"
        elif solution is not None and found_optimal:
            status = "SATISFIABLE_BEST"
        elif solution is None and models.is_unknown:
            status = "TIMEOUT"
        elif solution is None and models.is_unsatisfiable:
            status = "UNSATISFIABLE"

        statistics_lines = [f"{key}\t{value}\n" for key, value in models.statistics.items()]
        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_statistics", "".join(statistics_lines))
            save_txt_file(self._execution_uuid, "asp_status", f"{status}\n")
        elif self._local_dir is not None:
            save_local_txt_file(self._local_dir, "asp_statistics", "".join(statistics_lines))
            save_local_txt_file(self._local_dir, "asp_status", f"{status}\n")

        if solution is None:
            raise RuntimeError("Could not generate schedule; a valid solution could not be returned.")

        scheduled_sessions = [f"{variables[0]}\t{variables[1]}\t{variables[2]}\n"
                              for predicate, variables in solution if predicate == ClP.SCHEDULED_SESSION]
        optimization_lines = [f"{predicate}\t\t{variables[0]}\t{variables[1]}\t{variables[2]}\n"
                              for predicate, variables in solution if predicate in (ClP.PENALTY, ClP.BONUS,)]

        if self._execution_uuid is not None:
            save_txt_file(self._execution_uuid, "asp_solution", "".join(scheduled_sessions))
            save_txt_file(self._execution_uuid, "asp_optimization", "".join(optimization_lines))

        elif self._local_dir is not None:
            save_local_txt_file(self._local_dir, "asp_solution", "".join(scheduled_sessions))
            save_local_txt_file(self._local_dir, "asp_optimization", "".join(optimization_lines))

        else:
            print("---")
            print(solution)

        output = Output()
        for predicate, variables in solution:
            if predicate != ClP.SCHEDULED_SESSION:
                continue

            timeslot, clingo_session, clingo_room = variables
            session_hex, room_hex = ClN.get_id_from_clingo(clingo_session), ClN.get_id_from_clingo(clingo_room)
            output.timetable.append(ScheduleUnit(
                slot=week.get_slot_by_number(timeslot - 1),
                session=self._find_session_by_hex(session_hex),
                room=self._find_room_by_hex(room_hex),
            ))

        return output
