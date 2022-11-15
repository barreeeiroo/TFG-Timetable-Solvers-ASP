import json

from utils.paths import DATA_FOLDER


def read_json_settings():
    with open(DATA_FOLDER / "settings.json", encoding="utf8") as file:
        return json.loads(file.read())
