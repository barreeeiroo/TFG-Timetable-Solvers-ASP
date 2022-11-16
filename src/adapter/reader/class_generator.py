from typing import List

from adapter.reader.csv_reader import read_csv_file
from adapter.reader.json_reader import read_json_settings
from models.course import Course, SessionType
from models.room import Room
from models.settings import Settings
from utils.timeframe import Timeframe


def generate_courses() -> List[Course]:
    source_courses = read_csv_file("courses")
    courses = {}
    for year, code, name, short_name, semester in source_courses:
        courses[short_name] = Course(year, code, name, short_name, semester)

    source_sessions = read_csv_file("course_sessions")
    for course, session_type, duration, groups, count in source_sessions:
        if course not in courses:
            raise ValueError(f"Course {course} not found")
        courses[course].add_session(session_type, duration, int(groups), int(count))

    return list(courses.values())


def generate_rooms() -> List[Room]:
    source_rooms = read_csv_file("rooms")
    rooms = [
        Room(name, building, capacity, session_type) for name, building, capacity, session_type in source_rooms
    ]
    return rooms


def generate_settings() -> Settings:
    settings = Settings()

    source_settings = read_json_settings()
    settings.week.set_week_settings(
        days=source_settings['week'],
        start=source_settings['schedule'][0],
        end=source_settings['schedule'][1],
        slot_size=source_settings['slot']
    )

    source_teaching_types = read_csv_file("session_slots")
    for session_type, preferred_slot in source_teaching_types:
        settings.preferred_slots_per_session_type[
            SessionType.parse_from_string(session_type)
        ] = Timeframe(*preferred_slot.split("-"))

    source_week = read_csv_file("week_slots")
    for day, start, end, slot_type in source_week:
        settings.week.modify_slot(day, start, end, slot_type)

    return settings
