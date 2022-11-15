from adapter.reader.class_generator import generate_courses, generate_rooms, generate_settings
from solvers.asp.scheduler import AspSolver


def main():
    courses = generate_courses()
    rooms = generate_rooms()
    settings = generate_settings()

    solver = AspSolver(courses, rooms, settings)
    solver.solve()


if __name__ == "__main__":
    main()
