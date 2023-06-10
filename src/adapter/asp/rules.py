from datetime import timedelta
from typing import List

from pydantic import UUID4

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
        joined_timeslots = ";".join([f"{a}..{b}" for a, b in generate_slot_groups(slots)])
        return f"{ClP.timeslot(joined_timeslots)}."

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
                statements.append(f"{undesirable_timeslot}. % {ClN.get_timeslot_for_comment(real_slot)}")
        return statements

    @staticmethod
    def generate_rooms(rooms: List[Room]) -> List[str]:
        statements: List[str] = []
        for room in rooms:
            clingo_room = ClP.room(ClN.room_to_clingo(room), room.constraints.capacity)
            statements.append(f"{clingo_room}.{ClN.get_room_for_comment(room)}")
        return statements

    @staticmethod
    def __generate_pair_of_rooms(rooms: List[Room], room: Room, other_room_uuid: UUID4):
        other_room = next(room for room in rooms if room.id == other_room_uuid)
        room1, room2 = sorted((
            ClN.room_to_clingo(room),
            ClN.room_to_clingo(other_room),
        ))
        return room1, room2

    @staticmethod
    def generate_room_distances(rooms: List[Room], week: Week) -> List[str]:
        statements: List[str] = []

        for room in rooms:
            for other_room_uuid, distance in room.constraints.distances_in_minutes.items():
                if distance <= 0:
                    continue
                room1, room2 = FactRules.__generate_pair_of_rooms(rooms, room, UUID4(other_room_uuid))

                delta = timedelta(minutes=distance)
                timeslots = week.get_slots_count_for_timedelta_ceil(delta)

                statement = f"{ClP.room_distance(room1, room2, timeslots)}."
                if statement not in statements:
                    statements.append(statement)

        return statements

    @staticmethod
    def generate_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            clingo_session = ClP.session(
                ClN.session_to_clingo(session), ClN.session_type_to_clingo(session.constraints.session_type),
                week.get_slots_count_for_timedelta(session.constraints.duration)
            )
            statements.append(f"{clingo_session}.% {ClN.get_session_for_comment(session)}")
        return statements

    @staticmethod
    def __find_subslot_ids(slot: Slot, week: Week) -> List[int]:
        return [week.get_slot_id(subslot) for subslot in generate_sub_slots(slot, week.slot_duration)]

    @staticmethod
    def generate_eligible_timeslots_for_sessions(sessions: List[Session], week: Week) -> List[str]:
        statements: List[str] = []

        blocked_slots = week.get_slot_ids_per_type(SlotType.BLOCKED)
        common_eligible_slots = [i for i in range(1, week.get_total_slot_count() + 1) if i not in blocked_slots]
        day_breaks = [first for first, _ in week.get_day_breaks()]

        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)
            session_eligible_slots = common_eligible_slots.copy()
            session_slots = week.get_slots_count_for_timedelta(session.constraints.duration)

            for disallowed_slots in session.constraints.timeslots_preferences.disallowed_slots:
                for subslot_id in FactRules.__find_subslot_ids(disallowed_slots, week):
                    if subslot_id in session_eligible_slots:
                        session_eligible_slots.remove(subslot_id)

            slot_ranges = [(a, b - session_slots + 1,)
                           for a, b
                           in generate_slot_groups(session_eligible_slots, day_breaks)
                           if (abs(a - b) + 1) >= session_slots]

            for a, b in slot_ranges:
                eligible_timeslot = ClP.eligible_timeslot_for_session(clingo_session, f"{a}..{b}")
                slot_a, slot_b = week.get_slot_by_number(a - 1), week.get_slot_by_number(b - 1)

                comment_timeslot = ClN.get_timeslot_range_for_comment(slot_a, slot_b)
                comment_session = ClN.get_session_for_comment(session, simple=True)
                statements.append(f"{eligible_timeslot}. % {comment_session} | {comment_timeslot}")

        return statements

    @staticmethod
    def generate_eligible_rooms_for_sessions(sessions: List[Session], rooms: List[Room]) -> List[str]:
        statements: List[str] = []

        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)
            for room in rooms:
                clingo_room = ClN.room_to_clingo(room)
                if session.constraints.session_type not in room.constraints.session_types:
                    continue

                if room.id in session.constraints.rooms_preferences.disallowed_rooms:
                    continue

                eligible_room = ClP.eligible_room_for_session(clingo_session, clingo_room)
                statements.append(f"{eligible_room}.")

        return statements

    @staticmethod
    def __generate_conflicting_pair_of_sessions(sessions: List[Session],
                                                session: Session, no_overlapping_session_uuid: UUID4):
        other_session = next(session for session in sessions if session.id == no_overlapping_session_uuid)
        session1, session2 = sorted((
            ClN.session_to_clingo(session),
            ClN.session_to_clingo(other_session),
        ))
        return session1, session2

    @staticmethod
    def generate_no_overlapping_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.cannot_conflict_in_time:
                session1, session2 = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.no_timeslot_overlap_in_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_avoid_overlapping_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.avoid_conflict_in_time:
                session1, session2 = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.avoid_timeslot_overlap_in_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_same_room_if_sessions_contiguous_in_time(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.same_room_if_contiguous_in_time:
                session1, session2 = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.same_room_if_contiguous_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_apply_room_distances_to_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []
        for session in sessions:
            for no_overlapping_session_uuid in session.constraints.apply_room_distances:
                session1, session2 = FactRules.__generate_conflicting_pair_of_sessions(
                    sessions, session, no_overlapping_session_uuid,
                )
                statement = f"{ClP.apply_room_distances_to_sessions(session1, session2)}."
                if statement not in statements:
                    statements.append(statement)
        return statements

    @staticmethod
    def generate_room_preferences_for_sessions(sessions: List[Session]) -> List[str]:
        statements: List[str] = []

        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)

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

        for session in sessions:
            clingo_session = ClN.session_to_clingo(session)

            all_penalized_slots: List[int] = []
            for penalized_slots in session.constraints.timeslots_preferences.penalized_slots:
                all_penalized_slots.extend(FactRules.__find_subslot_ids(penalized_slots, week))
            for a, b in generate_slot_groups(all_penalized_slots):
                slot_a, slot_b = week.get_slot_by_number(a - 1), week.get_slot_by_number(b - 1)

                comment_timeslot = ClN.get_timeslot_range_for_comment(slot_a, slot_b)
                comment_session = ClN.get_session_for_comment(session, simple=True)
                comment = f"{comment_session} {comment_timeslot}"
                statements.append(f"{ClP.penalized_timeslot_for_session(clingo_session, f'{a}..{b}')}. % {comment}")

            all_preferred_slots: List[int] = []
            for preferred_slots in session.constraints.timeslots_preferences.preferred_slots:
                all_preferred_slots.extend(FactRules.__find_subslot_ids(preferred_slots, week))
            for a, b in generate_slot_groups(all_preferred_slots):
                slot_a, slot_b = week.get_slot_by_number(a - 1), week.get_slot_by_number(b - 1)

                comment_timeslot = ClN.get_timeslot_range_for_comment(slot_a, slot_b)
                comment_session = ClN.get_session_for_comment(session, simple=True)
                comment = f"{comment_session} {comment_timeslot}"
                statements.append(f"{ClP.preferred_timeslot_for_session(clingo_session, f'{a}..{b}')}. % {comment}")

        return statements


class ChoiceRules:
    @staticmethod
    def generate_assigned_timeslots() -> str:
        assigned_timeslot = ClP.assigned_timeslot(ClV.TIMESLOT, ClV.SESSION)
        eligible_timeslot = ClP.eligible_timeslot_for_session(ClV.SESSION, ClV.TIMESLOT)

        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.ANY)

        return f"1 {{ {assigned_timeslot} : {eligible_timeslot} }} 1 :- {session}."

    @staticmethod
    def generate_assigned_rooms() -> str:
        assigned_room = ClP.assigned_room(ClV.ROOM, ClV.SESSION)
        eligible_room = ClP.eligible_room_for_session(ClV.SESSION, ClV.ROOM)

        session = ClP.session(ClV.SESSION, ClV.ANY, ClV.ANY)

        return f"1 {{ {assigned_room} : {eligible_room} }} 1 :- {session}."


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
        t = ClP.timeslot(ClV.TIMESLOT)
        return f":- not {{ {scheduled_session_one}; {scheduled_session_two} }} 1, {no_overlap}, {t}."

    @staticmethod
    def exclude_sessions_scheduled_in_contiguous_timeslots_but_different_rooms() -> str:
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1", f"{ClV.ROOM}1")
        scheduled_session_two_a = ClP.scheduled_session(f"{ClV.TIMESLOT}-1", f"{ClV.SESSION}2", f"{ClV.ROOM}2")
        scheduled_session_two_b = ClP.scheduled_session(f"{ClV.TIMESLOT}+1", f"{ClV.SESSION}2", f"{ClV.ROOM}2")

        same_room = ClP.same_room_if_contiguous_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        assigned_room_one = ClP.assigned_room(f"{ClV.ROOM}1", f"{ClV.SESSION}1")
        assigned_room_two = ClP.assigned_room(f"{ClV.ROOM}2", f"{ClV.SESSION}2")
        not_equal = f"{ClV.ROOM}1 != {ClV.ROOM}2"

        choice = f"{{ {scheduled_session_two_a}; {scheduled_session_one}; {scheduled_session_two_b} }} 1"
        return f":- not {choice}, {same_room}, {assigned_room_one}, {assigned_room_two}, {not_equal}."


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

        avoid_overlap = ClP.avoid_timeslot_overlap_in_sessions(f"{ClV.SESSION}1", f"{ClV.SESSION}2")
        scheduled_session_one = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}1", ClV.ANY)
        scheduled_session_two = ClP.scheduled_session(ClV.TIMESLOT, f"{ClV.SESSION}2", ClV.ANY)
        t = ClP.timeslot(ClV.TIMESLOT)

        return f"{penalty} :- not {{ {scheduled_session_one}; {scheduled_session_two} }} 1, {avoid_overlap}, {t}."

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
            *FactRules.generate_room_distances(self.rooms, self.week),

            *FactRules.generate_sessions(self.sessions, self.week),
            *FactRules.generate_eligible_timeslots_for_sessions(self.sessions, self.week),
            *FactRules.generate_eligible_rooms_for_sessions(self.sessions, self.rooms),
            *FactRules.generate_no_overlapping_sessions(self.sessions),
            *FactRules.generate_avoid_overlapping_sessions(self.sessions),
            *FactRules.generate_same_room_if_sessions_contiguous_in_time(self.sessions),
            # TODO: Pending ASP restriction...
            *FactRules.generate_apply_room_distances_to_sessions(self.sessions),
            *FactRules.generate_room_preferences_for_sessions(self.sessions),
            *FactRules.generate_timeslot_preferences_for_sessions(self.sessions, self.week),
        ])

    @staticmethod
    def __generate_choices() -> str:
        return "\n".join([
            ChoiceRules.generate_assigned_timeslots(),
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
            ConstraintRules.exclude_sessions_scheduled_in_contiguous_timeslots_but_different_rooms(),
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
        ]) + "\n"
