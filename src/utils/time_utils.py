from datetime import date, datetime, time, timedelta


def add_time(time_obj: time, timedelta_obj: timedelta) -> time:
    return (time_to_datetime(time_obj) + timedelta_obj).time()


def time_to_datetime(time_obj: time) -> datetime:
    return datetime.combine(date(1, 1, 1), time_obj)
