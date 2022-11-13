import csv

from utils.paths import DATA_FOLDER


def read_csv_file(file_name: str):
    with open(DATA_FOLDER / f"{file_name}.csv", newline='', encoding="utf8") as file:
        file_reader = csv.reader(file, delimiter=',', quotechar='"')
        next(file_reader)
        data = list(file_reader)

    return data
