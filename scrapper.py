import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import List

import requests
from bs4 import BeautifulSoup


def generate_url(d: date) -> str:
    faculty_code = 409  # etse
    academic_year = 73  # 2022-2023

    return "https://matricula.usc.es/ServizosXML/Plantillas/actividades/Xsrm_Ocupacion_Dias.xml" \
           f"?Num_Organizacion_Nodo={faculty_code}" \
           f"&Num_Sistema_Ano_Academico={academic_year}" \
           "&Num_Sistema_Idioma=9" \
           f"&Cod_Mes={d.year}-{d.month}" \
           f"&Fecha={d.day}/{d.month}/{d.year}" \
           "&Contenttype=text/html"


def generate_academic_year_dates() -> List[date]:
    start_date, end_date = date(2022, 9, 5), date(2023, 5, 14)
    all_dates = []
    for d in [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]:
        if d.weekday() == 5 or d.weekday() == 6:
            continue
        all_dates.append(d)
    return all_dates


def get_schedule_content(d: date):
    url = generate_url(d)
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, 'html.parser')


def parse_content(content: BeautifulSoup):
    output = {}

    table = content.find("table", attrs={"summary": "Ocupación"})
    for row in table.find_all("tr"):
        for cell in row.find_all("td", class_=lambda c: "hora" not in c):
            classes = cell["class"]
            if len(classes) != 1:
                raise RuntimeError(classes)
            cls = classes[0]
            if cls == "oc0" or cls == "oc1" or cls == "oc":
                # Desocupado
                continue
            elif cls == "oc":
                #  Solapamiento
                continue
            elif cls == "oc4":
                # Examen
                continue
            elif cls == "oc3":
                # Clase
                pass
            else:
                raise RuntimeError(cls)

            raw_data = cell.div["onmouseover"].split("\n")[2].strip()[1:-1][12:].strip()
            class_type, rest = raw_data.split(": ")
            class_name, group = rest.split(" - ")
            if class_type == "Clase":
                pass
            else:
                raise RuntimeError(class_type)

            class_name, class_code = class_name.rsplit(" ", 1)
            class_code = class_code.replace("[", "").replace("]", "").strip()
            group = group.replace("Grupo /", "").strip().replace("_inglés", "")
            session_type, group_number = group.split("_")
            group_number = int(group_number)

            if class_code not in output:
                output[class_code] = {}
            if session_type not in output[class_code]:
                output[class_code][session_type] = {}
            if group_number not in output[class_code][session_type]:
                output[class_code][session_type][group_number] = 0
            output[class_code][session_type][group_number] += 30

    return output


def scrape():
    dates = generate_academic_year_dates()
    content = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_content = {executor.submit(get_schedule_content, d): i for i, d in enumerate(dates)}

        for future in as_completed(future_to_content):
            i = future_to_content[future]
            week_number = i // 5
            print(f"Parsing Week#{week_number} Date#{(i % 5) + 1}")

            partial = parse_content(future.result())

            for course_code, course_data in partial.items():
                if course_code not in content:
                    content[course_code] = {}

                for session_type, session_data in course_data.items():
                    if session_type not in content[course_code]:
                        content[course_code][session_type] = {}

                    for group_number, duration in session_data.items():
                        if group_number not in content[course_code][session_type]:
                            content[course_code][session_type][group_number] = []

                        if week_number not in [0, 21] and duration in content[course_code][session_type][group_number]:
                            continue
                        content[course_code][session_type][group_number].append(duration)

    with open("data/scrape.json", "w") as f:
        f.write(json.dumps(content))


def write_csv():
    with open("data/scrape.json") as f:
        data = json.loads(f.read())

    rows = [["Course", "Session Type", "Duration", "Num Per Week", "Num Groups"]]
    for course_code, course_data in data.items():
        for session_type, session_data in course_data.items():
            durations = []
            num_groups = 0
            for group_number, group_durations in session_data.items():
                num_groups = max(num_groups, int(group_number))
                if len(durations) == 0:
                    durations = group_durations
                    continue

                if sorted(durations) != sorted(group_durations):
                    if len(group_durations) < len(durations):
                        if len(group_durations) == 0:
                            raise RuntimeError("WTF")
                        durations = group_durations

            actual_durations = {}
            for duration in durations:
                if duration not in actual_durations:
                    actual_durations[duration] = 0
                actual_durations[duration] += 1

            for duration, num_per_week in actual_durations.items():
                rows.append([course_code, session_type, duration, num_per_week, num_groups])

    with open("data/session_groups.csv", "w", newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def validate():
    course_codes = []
    with open("data/courses.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            course_codes.append(row[1])

    with open("data/session_groups_without_info.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[0] not in course_codes:
                raise RuntimeError(row[0])


if __name__ == "__main__":
    # scrape()
    # write_csv()
    # validate()
    pass
