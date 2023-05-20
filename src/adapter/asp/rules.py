from typing import List

from pydantic import UUID4

from adapter.asp.constants import ClingoNaming as ClN, ClingoPredicates as ClP, ClingoVariables as ClV
from adapter.asp.optimizations import BonusCosts, BonusNames, OptimizationPriorities, PenaltyCosts, PenaltyNames
from adapter.time.week import Week
from models.dto.input import Room, Session
from models.slot import Slot, SlotType
from utils.slot_utils import generate_slot_groups, generate_slot_groups_raw, generate_sub_slots


class FactRules:
    @staticmethod
    def generate_timeslot(week: Week) -> str:
        total_slot_count = week.get_total_slot_count()
        blocked_slots = week.get_slot_ids_per_type(SlotType.BLOCKED)
        slots = [i for i in range(1, total_slot_count + 1) if i not in blocked_slots]
        return f"{ClP.timeslot(generate_slot_groups(slots))}."

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
                real_slot = week.get_slot_by_number(slot - 1)
                statements.append(f"{undesirable_timeslot}.{ClN.get_timeslot_for_comment(real_slot)}")
        return statements

    @staticmethod
    def generate_rooms(rooms: List[Room]) -> List[str]:
        statements: List[str] = []
        for room in rooms:
            clingo_room = ClP.room(ClN.room_to_clingo(room), room.constraints.capacity)
            statements.append(f"{clingo_room}.{ClN.get_room_for_comment(room)}")
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
            statements.append(f"{clingo_session}.{ClN.get_session_for_comment(session)}")
        return statements

    @staticmethod
    def __generate_conflicting_pair_of_sessions(sessions: List[Session], week: Week,
                                                session: Session, no_overlapping_session_uuid: UUID4):
        other_session = next(session for session in sessions if session.id == no_overlapping_session_uuid)
        session1, session2 = sorted((
            ClN.session_to_clingo(session),
            ClN.session_to_clingo(other_session),
        ))
        duration_slots = max(
            week.get_slots_count_for_timedelta(session.constraints.duration),
            week.get_slots_count_for_timedelta(other_session.constraints.duration),
        )
        return session1, session2, duration_slots

    @staticmethod
    def generate_no_overlapping_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.cannot_conflict_in_time:
                session1, session2, duration_slots = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, week, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.no_timeslot_overlap_in_sessions(session1, session2, duration_slots)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_avoid_overlapping_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.avoid_conflict_in_time:
                session1, session2, duration_slots = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, week, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.avoid_timeslot_overlap_in_sessions(session1, session2, duration_slots)}."
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
        blocked_slots = week.get_slot_ids_per_type(SlotType.BLOCKED)
        slots = [i for i in range(1, week.get_total_slot_count() + 1) if i not in blocked_slots]
        slot_ranges = generate_slot_groups_raw(slots, [first for first, _ in week.get_day_breaks()])
        formulas = [f'{slot_range}-{ClV.SESSION_DURATION}+1' for slot_range in slot_ranges]
        timeslot_generator = f"T = ({';'.join(formulas)})"
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
        assigned_timeslot_one = ClP.assigned_timeslot(f"{ClV.TIMESLOT}1", f"{ClV.SESSION}1")
        assigned_timeslot_two = ClP.assigned_timeslot(f"{ClV.TIMESLOT}2", f"{ClV.SESSION}2")
        no_overlap = ClP.no_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2", ClV.SESSION_DURATION)
        diff = f"|{ClV.TIMESLOT}1-{ClV.TIMESLOT}2| < {ClV.SESSION_DURATION}"
        return f":- {no_overlap}, {assigned_timeslot_one}, {assigned_timeslot_two}, {diff}."

    @staticmethod
    def exclude_timeslots_which_are_not_allowed_for_session() -> str:
        scheduled_session = ClP.scheduled_session(ClV.TIMESLOT, ClV.SESSION, ClV.ANY)
        disallowed_timeslot = ClP.disallowed_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)
        return f":- {disallowed_timeslot}, {scheduled_session}."

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

        assigned_timeslot_one = ClP.assigned_timeslot(f"{ClV.TIMESLOT}1", f"{ClV.SESSION}1")
        assigned_timeslot_two = ClP.assigned_timeslot(f"{ClV.TIMESLOT}2", f"{ClV.SESSION}2")
        avoid_overlap = ClP.avoid_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2",
                                                               ClV.SESSION_DURATION)
        diff = f"|{ClV.TIMESLOT}1-{ClV.TIMESLOT}2| < {ClV.SESSION_DURATION}"

        return f"{penalty} :- {avoid_overlap}, {assigned_timeslot_one}, {assigned_timeslot_two}, {diff}."

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
        return "\n".join([
            FactRules.generate_timeslot(self.week),
            *FactRules.generate_undesirable_timeslots(self.week),

            *FactRules.generate_rooms(self.rooms),
            *FactRules.generate_room_types(self.rooms),

            *FactRules.generate_sessions(self.sessions, self.week),
            *FactRules.generate_no_overlapping_sessions(self.sessions, self.week),
            *FactRules.generate_avoid_overlapping_sessions(self.sessions, self.week),
            *FactRules.generate_room_preferences_for_sessions(self.sessions),
            *FactRules.generate_timeslot_preferences_for_sessions(self.sessions, self.week),
        ])

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
            ConstraintRules.exclude_timeslots_which_are_not_allowed_for_session(),
            ConstraintRules.exclude_rooms_which_are_not_allowed_for_session(),
            ConstraintRules.exclude_sessions_assigned_in_same_overlapping_timeslot(),
        ])

    @staticmethod
    def __generate_optimizations() -> str:
        return "\n".join([
            *OptimizationRules.penalize_undesirable_timeslots(),
            *OptimizationRules.apply_room_preferences_in_sessions(),
            OptimizationRules.penalize_overlapping_sessions(),
            *OptimizationRules.apply_timeslot_preferences_in_sessions(),
        ])

    @staticmethod
    def __generate_directives() -> str:
        return "\n".join([
            Directives.generate_penalty_definition(),
            Directives.generate_bonus_definition(),
            *Directives.generate_show(),
        ])

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
