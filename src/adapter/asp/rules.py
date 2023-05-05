from typing import List

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP, ClingoVariables as ClV
from adapter.asp.penalties import PenaltyNames, PenaltyPriorities, SlotPenalties
from adapter.time.week import Week
from models.dto.input import Room, Session
from models.slot import SlotType


class FactRules:
    @staticmethod
    def generate_timeslot(total_slot_count: int) -> str:
        return f"{ClP.timeslot(f'1..{total_slot_count}')}."

    @staticmethod
    def contiguous_timeslots() -> str:
        return f"{ClP.contiguous_timeslot('1;-1')}."

    @staticmethod
    def generate_undesirable_timeslots(week: Week) -> List[str]:
        undesirable_penalties = {
            SlotType.UNDESIRABLE_1: SlotPenalties.UNDESIRABLE_1,
            SlotType.UNDESIRABLE_2: SlotPenalties.UNDESIRABLE_2,
            SlotType.UNDESIRABLE_5: SlotPenalties.UNDESIRABLE_5,
        }

        statements = []
        for slot_type, penalty_amount in undesirable_penalties.items():
            for slot in week.get_slot_ids_per_type(slot_type):
                undesirable_timeslot = ClP.undesirable_timeslot(slot, penalty_amount)
                statements.append(f"{undesirable_timeslot}.")
        return statements

    @staticmethod
    def generate_day_breaks(week: Week) -> List[str]:
        total_slots = week.get_total_slot_count()
        slots_per_day = week.get_slots_per_day_count()
        num_days = int(total_slots / slots_per_day)

        statements: List[str] = []
        for i in range(1, num_days):
            day_end = slots_per_day * i
            next_day_start = day_end + 1
            statement = ClP.break_session_timeslot(day_end, next_day_start)
            statements.append(f"{statement}.")
        return statements

    @staticmethod
    def generate_rooms(rooms: List[Room]) -> List[str]:
        statements: List[str] = []
        for room in rooms:
            clingo_room = ClP.room(ClN.room_to_clingo(room), room.constraints.capacity)
            statements.append(f"{clingo_room}.")
        return statements

    @staticmethod
    def generate_room_types(rooms: List[Room]) -> List[str]:
        statements: List[str] = []
        for room in rooms:
            for session_type in room.constraints.session_types:
                clingo_room_type = ClP.room_type(ClN.room_to_clingo(room), ClN.session_type_to_clingo(session_type))
                statements.append(f"{clingo_room_type}.")
        return statements

    @staticmethod
    def generate_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            clingo_session = ClP.session(
                ClN.session_to_clingo(session), ClN.session_type_to_clingo(session.constraints.session_type),
                week.get_slots_count_for_timedelta(session.constraints.duration)
            )
            statements.append(f"{clingo_session}.")
        return statements

    @staticmethod
    def generate_no_overlapping_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.cannot_conflict_in_time:
                session1, session2 = sorted((
                    ClN.session_to_clingo(session),
                    ClN.session_to_clingo(no_overlapping_session_uuid),
                ))
                statement = f"{ClP.no_timeslot_overlap_in_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements


class ChoiceRules:
    @staticmethod
    def generate_scheduled_sessions() -> str:
        assigned_slot = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
        timeslot = ClP.timeslot(ClV.TIMESLOT)
        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.SESSION_DURATION)

        head = f"{ClV.SESSION_DURATION} {{ {assigned_slot} : {timeslot} }} {ClV.SESSION_DURATION}"
        return f"{head} :- {session}."

    @staticmethod
    def generate_assigned_slots() -> str:
        assigned_slot = ClP.assigned_slot(ClV.TIMESLOT, ClV.SESSION, ClV.ROOM)
        room_type = ClP.room_type(ClV.ROOM, ClV.SESSION_TYPE)
        head = f"1 {{ {assigned_slot} : {room_type} }} 1"

        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
        session = ClP.session(ClV.SESSION, ClV.SESSION_TYPE, ClV.ANY)
        body = f"{scheduled_session}, {session}"
        return f"{head} :- {body}."


class NormalRules:
    @staticmethod
    def generate_scheduled_session_chains() -> List[str]:
        def first_normal_rule() -> str:
            scheduled_chain = ClP.scheduled_session_chain(ClV.SESSION, ClV.TIMESLOT, ClV.CONTIGUOUS_TIMESLOT)
            scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
            timeslot = ClP.timeslot(f"{ClV.TIMESLOT}+{ClV.CONTIGUOUS_TIMESLOT}")
            contiguous_timeslot = ClP.contiguous_timeslot(ClV.CONTIGUOUS_TIMESLOT)
            return f"{scheduled_chain} :- {scheduled_session}, {timeslot}, {contiguous_timeslot}."

        def second_normal_rule() -> str:
            scheduled_chain_left = ClP.scheduled_session_chain(ClV.SESSION, f"{ClV.TIMESLOT}+{ClV.CONTIGUOUS_TIMESLOT}",
                                                               ClV.CONTIGUOUS_TIMESLOT)
            scheduled_chain_right = ClP.scheduled_session_chain(ClV.SESSION, ClV.TIMESLOT, ClV.CONTIGUOUS_TIMESLOT)
            timeslot = ClP.timeslot(f"{ClV.TIMESLOT}+{ClV.CONTIGUOUS_TIMESLOT}")
            return f"{scheduled_chain_left} :- {scheduled_chain_right}, {timeslot}."

        return [
            first_normal_rule(),
            second_normal_rule(),
        ]


class ConstraintRules:
    @staticmethod
    def exclude_blocked_timeslots(week: Week) -> List[str]:
        blocked_slots: List[int] = week.get_slot_ids_per_type(SlotType.BLOCKED)
        if not blocked_slots:
            return []

        statements = []
        for blocked_slot in blocked_slots:
            stmt = f":- {ClP.assigned_slot(str(blocked_slot), ClV.ANY, ClV.ANY)}."
            statements.append(stmt)
        return statements

    @staticmethod
    def exclude_more_than_one_session_in_same_room_and_timeslot() -> str:
        assigned_slot = ClP.assigned_slot(ClV.TIMESLOT, ClV.SESSION, ClV.ROOM)
        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.ANY)
        choice = f"not {{ {assigned_slot} : {session} }} 1"
        return f":- {choice}, {ClP.room(ClV.ROOM, ClV.ANY)}, {ClP.timeslot(ClV.TIMESLOT)}."

    @staticmethod
    def exclude_same_session_in_different_room() -> str:
        assigned_slot_one = ClP.assigned_slot(ClV.ANY, ClV.SESSION, f'{ClV.ROOM}1')
        assigned_slot_two = ClP.assigned_slot(ClV.ANY, ClV.SESSION, f'{ClV.ROOM}2')
        condition = f"{ClV.ROOM}1 != {ClV.ROOM}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."

    @staticmethod
    def exclude_sessions_scheduled_in_same_overlapping_timeslot() -> str:
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1")
        scheduled_session_two = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}2")
        no_overlap = ClP.no_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        return f":- {scheduled_session_one}, {scheduled_session_two}, {no_overlap}."

    @staticmethod
    def exclude_sessions_scheduled_in_different_days() -> str:
        scheduled_session_one = ClP.scheduled_session(f"{ClV.TIMESLOT}1", ClV.SESSION)
        scheduled_session_two = ClP.scheduled_session(f"{ClV.TIMESLOT}2", ClV.SESSION)
        no_overlap = ClP.break_session_timeslot(f"{ClV.TIMESLOT}1", f"{ClV.TIMESLOT}2")
        return f":- {scheduled_session_one}, {scheduled_session_two}, {no_overlap}."

    @staticmethod
    def exclude_sessions_scheduled_in_non_contiguous_timeslots() -> str:
        scheduled_session_one = ClP.scheduled_session(f"{ClV.TIMESLOT}1", ClV.SESSION)
        scheduled_session_two = ClP.scheduled_session(f"{ClV.TIMESLOT}2", ClV.SESSION)
        scheduled_sessions = f"{scheduled_session_one}, {scheduled_session_two}"

        comparison = f"{ClV.TIMESLOT}1 + 1 < {ClV.TIMESLOT}2"

        contiguousness_rule = f"{ClV.TIMESLOT}1+1..{ClV.TIMESLOT}2-1"
        contiguous_sessions = f"{ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)} : T = {contiguousness_rule}"

        # Too costly, avoid...
        return f"% :- {scheduled_sessions}, {comparison}, not {contiguous_sessions}."

    @staticmethod
    def exclude_sessions_scheduled_in_non_contiguous_timeslots_alt() -> str:
        scheduled_chain_one = ClP.scheduled_session_chain(ClV.SESSION, ClV.TIMESLOT, -1)
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
        scheduled_chain_two = ClP.scheduled_session_chain(ClV.SESSION, ClV.TIMESLOT, 1)

        return f":- {scheduled_chain_one}, not {scheduled_session}, {scheduled_chain_two}."

    @staticmethod
    def exclude_sessions_which_are_isolated_from_other() -> str:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)

        scheduled_session_one = ClP.scheduled_session(f"{ClV.TIMESLOT}-1", ClV.SESSION)
        scheduled_session_two = ClP.scheduled_session(f"{ClV.TIMESLOT}+1", ClV.SESSION)
        excluded_sessions = f"not {scheduled_session_one}, not {scheduled_session_two}"

        single_slot_session = f"{ClP.session(ClV.SESSION, ClV.ANY, ClV.SESSION_DURATION)}, {ClV.SESSION_DURATION} > 1"

        return f":- {scheduled_session}, {excluded_sessions}, {single_slot_session}."

    @staticmethod
    def exclude_sessions_which_are_isolated_from_other_alt(sessions: List[Session], week: Week) -> List[str]:
        max_slots = max([week.get_slots_count_for_timedelta(session.constraints.duration) for session in sessions])

        statements = []
        for i in range(1, max_slots):
            scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)

            excluded_session_one = ClP.scheduled_session(f"{ClV.TIMESLOT}+{i}", ClV.SESSION)
            excluded_session_two = ClP.scheduled_session(f"{ClV.TIMESLOT}-{i}", ClV.SESSION)

            base_statement = f"{scheduled_session}, not {excluded_session_one}, not {excluded_session_two}"
            session_slot = f"{ClP.session(ClV.SESSION, ClV.ANY, ClV.SESSION_DURATION)}, {ClV.SESSION_DURATION} > {i}"
            # See exclude_sessions_which_are_isolated_from_other
            statements.append(f"% :- {base_statement}, {session_slot}.")

        return statements


class PenaltyRules:
    @staticmethod
    def avoid_undesirable_timeslots() -> List[str]:
        priorities = {
            PenaltyNames.UNDESIRABLE_TIMESLOT_1: (
                PenaltyPriorities.UNDESIRABLE_TIMESLOT_1, SlotPenalties.UNDESIRABLE_1
            ),
            PenaltyNames.UNDESIRABLE_TIMESLOT_2: (
                PenaltyPriorities.UNDESIRABLE_TIMESLOT_2, SlotPenalties.UNDESIRABLE_2
            ),
            PenaltyNames.UNDESIRABLE_TIMESLOT_5: (
                PenaltyPriorities.UNDESIRABLE_TIMESLOT_5, SlotPenalties.UNDESIRABLE_5
            ),
        }

        statements = []
        for name, (prio, cost) in priorities.items():
            penalty = ClP.penalty(name, ClV.PENALTY_COST, ClV.TIMESLOT, prio)
            undesirable_timeslot = ClP.undesirable_timeslot(ClV.TIMESLOT, ClV.PENALTY_COST)
            assigned_slot = ClP.assigned_slot(ClV.TIMESLOT, ClV.ANY, ClV.ANY)
            statements.append(f"{penalty} :- {assigned_slot}, {undesirable_timeslot}, {ClV.PENALTY_COST} == {cost}.")
        return statements


class Directives:
    @staticmethod
    def generate_penalty_definition() -> str:
        penalty_calc = f"{ClV.PENALTY_COST}@{ClV.PENALTY_PRIORITY},{ClV.PENALTY_VALUE},{ClV.PENALTY_NAME}"
        penalty = ClP.penalty(ClV.PENALTY_NAME, ClV.PENALTY_COST, ClV.PENALTY_VALUE, ClV.PENALTY_PRIORITY)
        return f"#minimize {{ {penalty_calc} : {penalty} }}."

    @staticmethod
    def generate_show() -> str:
        return f"#show {ClP.ASSIGNED_SLOT}/3."


class Rules:
    def __init__(self, week: Week, sessions: List[Session], rooms: List[Room]):
        self.sessions = sessions
        self.rooms = rooms
        self.week = week

    def __generate_facts(self) -> str:
        statements: List[str] = [
            FactRules.generate_timeslot(self.week.get_total_slot_count()),
            FactRules.contiguous_timeslots(),
        ]
        statements.extend(FactRules.generate_undesirable_timeslots(self.week))
        statements.extend(FactRules.generate_day_breaks(self.week))

        statements.extend(FactRules.generate_rooms(self.rooms))
        statements.extend(FactRules.generate_room_types(self.rooms))

        statements.extend(FactRules.generate_sessions(self.sessions, self.week))
        statements.extend(FactRules.generate_no_overlapping_sessions(self.sessions))

        return "\n".join(statements)

    @staticmethod
    def __generate_choices() -> str:
        return "\n".join([
            ChoiceRules.generate_scheduled_sessions(),
            ChoiceRules.generate_assigned_slots(),
        ])

    @staticmethod
    def __generate_normals() -> str:
        statements = []

        statements.extend(NormalRules.generate_scheduled_session_chains())

        return "\n".join(statements)

    def __generate_constraints(self) -> str:
        statements = []

        statements.extend(ConstraintRules.exclude_blocked_timeslots(self.week))

        statements.extend([
            ConstraintRules.exclude_more_than_one_session_in_same_room_and_timeslot(),
            ConstraintRules.exclude_same_session_in_different_room(),
            ConstraintRules.exclude_sessions_scheduled_in_same_overlapping_timeslot(),
            ConstraintRules.exclude_sessions_scheduled_in_different_days(),
            ConstraintRules.exclude_sessions_scheduled_in_non_contiguous_timeslots(),
            ConstraintRules.exclude_sessions_scheduled_in_non_contiguous_timeslots_alt(),
            ConstraintRules.exclude_sessions_which_are_isolated_from_other(),
        ])

        statements.extend(ConstraintRules.exclude_sessions_which_are_isolated_from_other_alt(self.sessions, self.week))

        return "\n".join(statements)

    @staticmethod
    def __generate_penalties() -> str:
        statements = []

        statements.extend(PenaltyRules.avoid_undesirable_timeslots())

        return "\n".join(statements)

    @staticmethod
    def __generate_directives() -> str:
        return "\n".join([
            Directives.generate_penalty_definition(),
            Directives.generate_show(),
        ])

    def generate_asp_problem(self) -> str:
        facts = self.__generate_facts()
        choices = Rules.__generate_choices()
        normals = Rules.__generate_normals()
        constraints = self.__generate_constraints()
        penalties = Rules.__generate_penalties()
        directives = Rules.__generate_directives()

        return "\n\n".join([
            facts,
            choices,
            normals,
            constraints,
            penalties,
            directives,
        ])


class Rules2:
    def __init__(self, week: Week, sessions: List[Session], rooms: List[Room]):
        self.__week = week
        self.__sessions = sessions
        self.__rooms = rooms

    def generate_penalized_room_types(self, penality_amount: int = 45) -> str:
        assert self
        used_room = ClP.used_room(ClV.TIMESLOT, ClV.ROOM, ClV.ROOM_TYPE, ClV.SESSION_TYPE)
        condition = f"{ClV.ROOM_TYPE} != {ClV.SESSION_TYPE}"
        return f":~ {used_room}, {condition}.[{penality_amount},{ClV.TIMESLOT}]"
