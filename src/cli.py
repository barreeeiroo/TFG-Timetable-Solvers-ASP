import json
from pathlib import Path

from adapter.asp.scheduler import AspSolver
from models.dto.input import Input


def main():
    with open(Path(__file__).parent / ".." / "data" / "example_input.json") as f:
        data = json.loads(f.read())
    input_data = Input.parse_obj(data)

    solver = AspSolver(input_data.sessions, input_data.rooms, input_data.settings)
    output = solver.solve()
    print(output.json())


if __name__ == "__main__":
    main()
