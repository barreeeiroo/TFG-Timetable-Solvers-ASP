class Building:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Building({self.name})"

    def __eq__(self, other):
        return isinstance(other, Building) and other.name == self.name


class Room:
    def __init__(self, name: str, building: str, capacity: int):
        self.name: str = str(name)
        self.building: Building = Building(building)
        self.capacity: int = int(capacity)

    def __repr__(self):
        return f"Room({self.name})"

    def __eq__(self, other):
        return isinstance(other, Room) and other.building == self.building and other.name == self.name
