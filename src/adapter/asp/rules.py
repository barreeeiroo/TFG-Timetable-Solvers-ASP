from typing import List

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP, ClingoVariables as ClV
from adapter.asp.optimizations import BonusCosts, BonusNames, OptimizationPriorities, PenaltyCosts, PenaltyNames
from adapter.time.week import Week
from models.dto.input import Room, Session
from models.slot import Slot, SlotType
from utils.slot_utils import generate_sub_slots


class FactRules:
    @staticmethod
    def generate_timeslot(total_slot_count: int) -> str:
        return f"{ClP.timeslot(f'1..{total_slot_count}')}."

    @staticmethod
    def contiguous_timeslots() -> str:
        return f"{ClP.contiguous_timeslot('1;-1')}."

    @staticmethod
    def generate_blocked_timeslots(week: Week) -> str:
        ids = [str(slot) for slot in week.get_slot_ids_per_type(SlotType.BLOCKED)]
        blocked_timeslot = ClP.blocked_timeslot(";".join(ids))
        return f"{blocked_timeslot}."

    @staticmethod
    def generate_undesirable_timeslots(week: Week) -> List[str]:
        undesirable_penalties = {
            SlotType.UNDESIRABLE_1: PenaltyCosts.UNDESIRABLE_TIMESLOT_1,
            SlotType.UNDESIRABLE_2: PenaltyCosts.UNDESIRABLE_TIMESLOT_2,
            SlotType.UNDESIRABLE_5: PenaltyCosts.UNDESIRABLE_TIMESLOT_5,
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

    @staticmethod
    def generate_avoid_overlapping_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.avoid_conflict_in_time:
                session1, session2 = sorted((
                    ClN.session_to_clingo(session),
                    ClN.session_to_clingo(no_overlapping_session_uuid),
                ))
                statement = f"{ClP.avoid_timeslot_overlap_in_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_room_preferences_for_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)

            for disallowed_room_uuid in session.constraints.rooms_preferences.disallowed_rooms:
                clingo_room = ClN.room_to_clingo(disallowed_room_uuid)
                statements.append(f"{ClP.disallowed_room_for_session(clingo_session, clingo_room)}.")
            for penalized_room_uuid in session.constraints.rooms_preferences.penalized_rooms:
                clingo_room = ClN.room_to_clingo(penalized_room_uuid)
                statements.append(f"{ClP.penalized_room_for_session(clingo_session, clingo_room)}.")
            for preferred_room_uuid in session.constraints.rooms_preferences.preferred_rooms:
                clingo_room = ClN.room_to_clingo(preferred_room_uuid)
                statements.append(f"{ClP.preferred_room_for_session(clingo_session, clingo_room)}.")

        return statements

    @staticmethod
    def generate_timeslot_preferences_for_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []

        def find_subslot_ids(slot: Slot) -> List[int]:
            return [week.get_slot_id(subslot) for subslot in generate_sub_slots(slot, week.slot_duration)]

        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)

            for disallowed_slots in session.constraints.timeslots_preferences.disallowed_slots:
                for subslot_id in find_subslot_ids(disallowed_slots):
                    statements.append(f"{ClP.disallowed_timeslot_for_session(clingo_session, subslot_id)}.")
            for penalized_slots in session.constraints.timeslots_preferences.penalized_slots:
                for subslot_id in find_subslot_ids(penalized_slots):
                    statements.append(f"{ClP.penalized_timeslot_for_session(clingo_session, subslot_id)}.")
            for preferred_slots in session.constraints.timeslots_preferences.preferred_slots:
                for subslot_id in find_subslot_ids(preferred_slots):
                    statements.append(f"{ClP.preferred_timeslot_for_session(clingo_session, subslot_id)}.")

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
    def exclude_blocked_timeslots() -> str:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.ANY)
        blocked_timeslot = ClP.blocked_timeslot(ClV.TIMESLOT)
        return f":- {blocked_timeslot}, {scheduled_session}."

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
        return f":- {no_overlap}, {scheduled_session_one}, {scheduled_session_two}."

    @staticmethod
    def exclude_sessions_scheduled_in_different_days() -> str:
        scheduled_session_one = ClP.scheduled_session(f"{ClV.TIMESLOT}1", ClV.SESSION)
        scheduled_session_two = ClP.scheduled_session(f"{ClV.TIMESLOT}2", ClV.SESSION)
        break_session = ClP.break_session_timeslot(f"{ClV.TIMESLOT}1", f"{ClV.TIMESLOT}2")
        return f":- {break_session}, {scheduled_session_one}, {scheduled_session_two}."

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

    @staticmethod
    def exclude_rooms_which_are_not_allowed_for_session() -> str:
        assigned_slot = ClP.assigned_slot(ClV.ANY, ClV.SESSION, ClV.ROOM)
        disallowed_room = ClP.disallowed_room_for_session(ClV.SESSION, ClV.ROOM)
        return f":- {disallowed_room}, {assigned_slot}."

    @staticmethod
    def exclude_timeslots_which_are_not_allowed_for_session() -> str:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
        disallowed_timeslot = ClP.disallowed_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)
        return f":- {disallowed_timeslot}, {scheduled_session}."


class OptimizationRules:
    @staticmethod
    def penalize_undesirable_timeslots() -> List[str]:
        priorities = [
            (OptimizationPriorities.PENALTY__UNDESIRABLE_TIMESLOT_1, PenaltyCosts.UNDESIRABLE_TIMESLOT_1,),
            (OptimizationPriorities.PENALTY__UNDESIRABLE_TIMESLOT_2, PenaltyCosts.UNDESIRABLE_TIMESLOT_2,),
            (OptimizationPriorities.PENALTY__UNDESIRABLE_TIMESLOT_5, PenaltyCosts.UNDESIRABLE_TIMESLOT_5,),
        ]

        statements = []
        for prio, cost in priorities:
            scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)
            penalty = ClP.penalty(PenaltyNames.UNDESIRABLE_TIMESLOT, ClV.PENALTY_COST, ClV.SESSION, prio)
            undesirable_timeslot = ClP.undesirable_timeslot(ClV.TIMESLOT, ClV.PENALTY_COST)
            penalty_cost = f"{ClV.PENALTY_COST} == {cost}"
            statements.append(f"{penalty} :- {undesirable_timeslot}, {scheduled_session}, {penalty_cost}.")
        return statements

    @staticmethod
    def apply_room_preferences_in_sessions() -> List[str]:
        assigned_slot = ClP.assigned_slot(ClV.ANY, ClV.SESSION, ClV.ROOM)

        penalty = ClP.penalty(PenaltyNames.AVOID_ROOM_FOR_SESSION,
                              PenaltyCosts.AVOID_ROOM_FOR_SESSION,
                              ClV.SESSION,
                              OptimizationPriorities.PENALTY__AVOID_ROOM_FOR_SESSION)
        penalized_room = ClP.penalized_room_for_session(ClV.SESSION, ClV.ROOM)
        avoid_statement = f"{penalty} :- {penalized_room}, {assigned_slot}."

        bonus = ClP.bonus(BonusNames.PREFER_ROOM_FOR_SESSION,
                          BonusCosts.PREFER_ROOM_FOR_SESSION,
                          ClV.SESSION,
                          OptimizationPriorities.BONUS__PREFER_ROOM_FOR_SESSION)
        preferred_room = ClP.preferred_room_for_session(ClV.SESSION, ClV.ROOM)
        prefer_statement = f"{bonus} :- {preferred_room}, {assigned_slot}."

        return [avoid_statement, prefer_statement]

    @staticmethod
    def penalize_overlapping_sessions() -> str:
        penalty = ClP.penalty(PenaltyNames.AVOID_SESSION_OVERLAP,
                              PenaltyCosts.AVOID_SESSION_OVERLAP,
                              f"{ClV.SESSION}1",
                              OptimizationPriorities.PENALTY__AVOID_SESSION_OVERLAP)
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1")
        scheduled_session_two = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}2")
        no_overlap = ClP.no_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        return f"{penalty} :- {no_overlap}, {scheduled_session_one}, {scheduled_session_two}."

    @staticmethod
    def apply_timeslot_preferences_in_sessions() -> List[str]:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION)

        penalty = ClP.penalty(PenaltyNames.AVOID_TIMESLOT_FOR_SESSION,
                              PenaltyCosts.AVOID_TIMESLOT_FOR_SESSION,
                              ClV.SESSION,
                              OptimizationPriorities.PENALTY__AVOID_TIMESLOT_FOR_SESSION)
        penalized_timeslot = ClP.penalized_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)
        avoid_statement = f"{penalty} :- {penalized_timeslot}, {scheduled_session}."

        bonus = ClP.bonus(BonusNames.PREFER_TIMESLOT_FOR_SESSION,
                          BonusCosts.PREFER_TIMESLOT_FOR_SESSION,
                          ClV.SESSION,
                          OptimizationPriorities.BONUS__PREFER_TIMESLOT_FOR_SESSION)
        preferred_timeslot = ClP.preferred_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)
        prefer_statement = f"{bonus} :- {preferred_timeslot}, {scheduled_session}."

        return [avoid_statement, prefer_statement]


class Directives:
    @staticmethod
    def generate_penalty_definition() -> str:
        penalty_calc = f"{ClV.PENALTY_COST}@{ClV.PENALTY_PRIORITY},{ClV.PENALTY_NAME},{ClV.PENALTY_VALUE}"
        penalty = ClP.penalty(ClV.PENALTY_NAME, ClV.PENALTY_COST, ClV.PENALTY_VALUE, ClV.PENALTY_PRIORITY)
        return f"#minimize {{ {penalty_calc} : {penalty} }}."

    @staticmethod
    def generate_bonus_definition() -> str:
        bonus_calc = f"{ClV.BONUS_COST}@{ClV.BONUS_PRIORITY},{ClV.BONUS_NAME},{ClV.BONUS_VALUE}"
        bonus = ClP.bonus(ClV.BONUS_NAME, ClV.BONUS_COST, ClV.BONUS_VALUE, ClV.BONUS_PRIORITY)
        return f"#maximize {{ {bonus_calc} : {bonus} }}."

    @staticmethod
    def generate_show() -> List[str]:
        return [
            f"#show {ClP.ASSIGNED_SLOT}/3.",
            f"#show {ClP.PENALTY}/4.",
            f"#show {ClP.BONUS}/4.",
        ]


class Rules:
    def __init__(self, week: Week, sessions: List[Session], rooms: List[Room]):
        self.sessions = sessions
        self.rooms = rooms
        self.week = week

    def __generate_facts(self) -> str:
        statements: List[str] = [
            FactRules.generate_timeslot(self.week.get_total_slot_count()),
            FactRules.contiguous_timeslots(),
            FactRules.generate_blocked_timeslots(self.week),
        ]
        statements.extend(FactRules.generate_undesirable_timeslots(self.week))
        statements.extend(FactRules.generate_day_breaks(self.week))

        statements.extend(FactRules.generate_rooms(self.rooms))
        statements.extend(FactRules.generate_room_types(self.rooms))

        statements.extend(FactRules.generate_sessions(self.sessions, self.week))
        statements.extend(FactRules.generate_no_overlapping_sessions(self.sessions))
        statements.extend(FactRules.generate_avoid_overlapping_sessions(self.sessions))
        statements.extend(FactRules.generate_room_preferences_for_sessions(self.sessions))
        statements.extend(FactRules.generate_timeslot_preferences_for_sessions(self.sessions, self.week))

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

    @staticmethod
    def __generate_constraints() -> str:
        return "\n".join([
            ConstraintRules.exclude_blocked_timeslots(),
            ConstraintRules.exclude_more_than_one_session_in_same_room_and_timeslot(),
            ConstraintRules.exclude_same_session_in_different_room(),
            ConstraintRules.exclude_sessions_scheduled_in_same_overlapping_timeslot(),
            ConstraintRules.exclude_sessions_scheduled_in_different_days(),
            ConstraintRules.exclude_sessions_scheduled_in_non_contiguous_timeslots_alt(),
            ConstraintRules.exclude_sessions_which_are_isolated_from_other(),
            ConstraintRules.exclude_rooms_which_are_not_allowed_for_session(),
        ])

    @staticmethod
    def __generate_optimizations() -> str:
        statements = []

        statements.extend(OptimizationRules.penalize_undesirable_timeslots())
        statements.extend(OptimizationRules.apply_room_preferences_in_sessions())
        statements.append(OptimizationRules.penalize_overlapping_sessions())
        statements.extend(OptimizationRules.apply_timeslot_preferences_in_sessions())

        return "\n".join(statements)

    @staticmethod
    def __generate_directives() -> str:
        statements = [
            Directives.generate_penalty_definition(),
            Directives.generate_bonus_definition(),
        ]

        statements.extend(Directives.generate_show())

        return "\n".join(statements)

    def generate_asp_problem(self) -> str:
        facts = self.__generate_facts()
        choices = Rules.__generate_choices()
        normals = Rules.__generate_normals()
        constraints = Rules.__generate_constraints()
        optimizations = Rules.__generate_optimizations()
        directives = Rules.__generate_directives()

        return "\n\n".join([
            facts,
            choices,
            normals,
            constraints,
            optimizations,
            directives,
        ])
