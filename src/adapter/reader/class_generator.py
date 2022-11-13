from adapter.reader.csv_reader import read_csv_file
from models.course import Course
from models.room import Room


def generate_courses():
    source_courses = read_csv_file("courses")
    courses = [
        Course(year, code, name, short_name, semester) for year, code, name, short_name, semester in source_courses
    ]
    print(courses)


def generate_rooms():
    source_rooms = read_csv_file("rooms")
    rooms = [
        Room(name, building, capacity) for name, building, capacity in source_rooms
    ]
    print(rooms)
