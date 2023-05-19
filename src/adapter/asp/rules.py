from typing import List

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP, ClingoVariables as ClV
from adapter.asp.optimizations import BonusCosts, BonusNames, OptimizationPriorities, PenaltyCosts, PenaltyNames
from adapter.time.week import Week
from models.dto.input import Room, Session
from models.slot import Slot, SlotType
from utils.slot_utils import generate_slot_groups, generate_sub_slots


class FactRules:
    @staticmethod
    def generate_timeslot(week: Week) -> str:
        total_slot_count = week.get_total_slot_count()
        blocked_slots = week.get_slot_ids_per_type(SlotType.BLOCKED)
        slots = [i for i in range(1, total_slot_count + 1) if i not in blocked_slots]
        return f"{ClP.timeslot(generate_slot_groups(slots))}."

    @staticmethod
    def contiguous_timeslots() -> str:
        return f"{ClP.contiguous_timeslot('1;-1')}."

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
    def generate_assigned_timeslots(week: Week) -> str:
        assigned_timeslot = ClP.assigned_timeslot(ClV.TIMESLOT, ClV.SESSION)
        timeslot_generator = f"T = 1..{week.get_total_slot_count()}-{ClV.SESSION_DURATION}+1"
        head = f"1 {{ {assigned_timeslot} : {timeslot_generator} }} 1"

        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.SESSION_DURATION)

        return f"{head} :- {session}."

    @staticmethod
    def generate_assigned_rooms() -> str:
        assigned_room = ClP.assigned_room(ClV.ROOM, ClV.SESSION)
        room_type = ClP.room_type(ClV.ROOM, ClV.SESSION_TYPE)
        head = f"1 {{ {assigned_room} : {room_type} }} 1"

        session = ClP.session(ClV.SESSION, ClV.SESSION_TYPE, ClV.ANY)

        return f"{head} :- {session}."


class NormalRules:
    @staticmethod
    def generate_scheduled_sessions() -> str:
        scheduled_session = ClP.scheduled_session(
            f"{ClV.TIMESLOT}..{ClV.TIMESLOT}+{ClV.SESSION_DURATION}-1",
            ClV.SESSION,
            ClV.ROOM
        )

        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.SESSION_DURATION)
        assigned_timeslot = ClP.assigned_timeslot(ClV.TIMESLOT, ClV.SESSION)
        assigned_room = ClP.assigned_room(ClV.ROOM, ClV.SESSION)
        body = f"{session}, {assigned_timeslot}, {assigned_room}"

        return f"{scheduled_session} :- {body}."


class ConstraintRules:
    @staticmethod
    def exclude_more_than_one_session_in_same_room_and_timeslot() -> str:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.ANY, ClV.ROOM)
        room = ClP.room(ClV.ROOM, ClV.ANY)
        timeslot = ClP.timeslot(ClV.TIMESLOT)
        return f":- not {{ {scheduled_session} }} 1, {room}, {timeslot}."

    @staticmethod
    def exclude_sessions_assigned_in_same_overlapping_timeslot() -> str:
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1", ClV.ANY)
        scheduled_session_two = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}2", ClV.ANY)
        no_overlap = ClP.no_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        return f":- {no_overlap}, {scheduled_session_one}, {scheduled_session_two}."

    @staticmethod
    def exclude_sessions_assigned_in_different_days() -> str:
        scheduled_session_one = ClP.assigned_timeslot(f"{ClV.TIMESLOT}1", ClV.SESSION)
        scheduled_session_two = ClP.assigned_timeslot(f"{ClV.TIMESLOT}2", ClV.SESSION)
        break_session = ClP.break_session_timeslot(f"{ClV.TIMESLOT}1", f"{ClV.TIMESLOT}2")
        return f":- {break_session}, {scheduled_session_one}, {scheduled_session_two}."

    @staticmethod
    def exclude_timeslots_which_are_not_allowed_for_session() -> str:
        assigned_timeslot = ClP.assigned_timeslot(ClV.TIMESLOT, ClV.SESSION)
        disallowed_timeslot = ClP.disallowed_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)
        return f":- {disallowed_timeslot}, {assigned_timeslot}."

    @staticmethod
    def exclude_rooms_which_are_not_allowed_for_session() -> str:
        assigned_room = ClP.assigned_room(ClV.ROOM, ClV.SESSION)
        disallowed_room = ClP.disallowed_room_for_session(ClV.SESSION, ClV.ROOM)
        return f":- {disallowed_room}, {assigned_room}."


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
            scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION, ClV.ANY)
            penalty = ClP.penalty(PenaltyNames.UNDESIRABLE_TIMESLOT, ClV.PENALTY_COST, ClV.SESSION, prio)
            undesirable_timeslot = ClP.undesirable_timeslot(ClV.TIMESLOT, ClV.PENALTY_COST)
            penalty_cost = f"{ClV.PENALTY_COST} == {cost}"
            statements.append(f"{penalty} :- {undesirable_timeslot}, {scheduled_session}, {penalty_cost}.")
        return statements

    @staticmethod
    def apply_room_preferences_in_sessions() -> List[str]:
        assigned_room = ClP.assigned_room(ClV.ROOM, ClV.SESSION)

        penalty = ClP.penalty(PenaltyNames.AVOID_ROOM_FOR_SESSION,
                              PenaltyCosts.AVOID_ROOM_FOR_SESSION,
                              ClV.SESSION,
                              OptimizationPriorities.PENALTY__AVOID_ROOM_FOR_SESSION)
        penalized_room = ClP.penalized_room_for_session(ClV.SESSION, ClV.ROOM)
        avoid_statement = f"{penalty} :- {penalized_room}, {assigned_room}."

        bonus = ClP.bonus(BonusNames.PREFER_ROOM_FOR_SESSION,
                          BonusCosts.PREFER_ROOM_FOR_SESSION,
                          ClV.SESSION,
                          OptimizationPriorities.BONUS__PREFER_ROOM_FOR_SESSION)
        preferred_room = ClP.preferred_room_for_session(ClV.SESSION, ClV.ROOM)
        prefer_statement = f"{bonus} :- {preferred_room}, {assigned_room}."

        return [avoid_statement, prefer_statement]

    @staticmethod
    def penalize_overlapping_sessions() -> str:
        penalty = ClP.penalty(PenaltyNames.AVOID_SESSION_OVERLAP,
                              PenaltyCosts.AVOID_SESSION_OVERLAP,
                              f"{ClV.SESSION}1",
                              OptimizationPriorities.PENALTY__AVOID_SESSION_OVERLAP)
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1", ClV.ANY)
        scheduled_session_two = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}2", ClV.ANY)
        avoid_overlap = ClP.avoid_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        return f"{penalty} :- {avoid_overlap}, {scheduled_session_one}, {scheduled_session_two}."

    @staticmethod
    def apply_timeslot_preferences_in_sessions() -> List[str]:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION, ClV.ANY)

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
            f"#show {ClP.SCHEDULED_SESSION}/3.",
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
            FactRules.generate_timeslot(self.week),
            FactRules.contiguous_timeslots(),
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
    def __generate_choices(week: Week) -> str:
        return "\n".join([
            ChoiceRules.generate_assigned_timeslots(week),
            ChoiceRules.generate_assigned_rooms(),
        ])

    @staticmethod
    def __generate_normals() -> str:
        return "\n".join([
            NormalRules.generate_scheduled_sessions(),
        ])

    @staticmethod
    def __generate_constraints() -> str:
        return "\n".join([
            ConstraintRules.exclude_more_than_one_session_in_same_room_and_timeslot(),
            ConstraintRules.exclude_sessions_assigned_in_same_overlapping_timeslot(),
            ConstraintRules.exclude_sessions_assigned_in_different_days(),
            ConstraintRules.exclude_timeslots_which_are_not_allowed_for_session(),
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
        choices = Rules.__generate_choices(self.week)
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
        ]) + "\n"
