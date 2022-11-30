from models.settings import Settings
from utils.timeframe import generate_timeframe


def generate_settings() -> Settings:
    settings = Settings()

    source_settings = {
        "schedule": ["09:00", "20:30"],
        "week": [0, 1, 2, 3, 4],
        "slot": "30m"
    }

    settings.week.set_week_settings(
        days=source_settings['week'],
        start=source_settings['schedule'][0],
        end=source_settings['schedule'][1],
        slot_size=source_settings['slot']
    )

    source_teaching_types = [
        ("CLE", "09:00-14:00"),
        ("CLIS", "09:00-14:00"),
        ("CLIL", "15:30-20:00"),
    ]
    for session_type, preferred_slot in source_teaching_types:
        settings.preferred_slots_per_session_type[session_type] = generate_timeframe(*preferred_slot.split("-"))

    source_week = [
        "Monday", "14:00", "15:30", "Undesirable",
        "Monday", "20:00", "20:30", "Undesirable",
        "Tuesday", "14:00", "15:30", "Undesirable",
        "Tuesday", "20:00", "20:30", "Undesirable",
        "Wednesday", "14:00", "15:30", "Undesirable",
        "Wednesday", "20:00", "20:30", "Undesirable",
        "Thursday", "12:00", "14:00", "Blocked",
        "Thursday", "14:00", "15:30", "Undesirable",
        "Thursday", "20:00", "20:30", "Undesirable",
        "Friday", "14:00", "15:30", "Undesirable",
        "Friday", "20:00", "20:30", "Undesirable",
    ]
    for day, start, end, slot_type in source_week:
        settings.week.modify_slot(day, start, end, slot_type)

    return settings
