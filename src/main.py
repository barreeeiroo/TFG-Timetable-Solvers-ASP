from adapter.reader.class_generator import generate_courses, generate_rooms, generate_settings


def main():
    courses = generate_courses()
    rooms = generate_rooms()
    settings = generate_settings()


if __name__ == "__main__":
    main()
