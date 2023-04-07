import csv

import requests

headers = {
    'Authorization': 'Bearer ...'
}

maps = {
    '1SG': '1P',
    '2SG': '2P',
    'ANG': 'AP',
}


def create():
    with open('data/courses.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            url = 'https://api.horarios.barreiro.xyz/course/create/etse'
            course = {
                'code': row[1],
                'name': row[2],
                'period': maps[row[4]],
                'shortName': row[3],
            }
            x = requests.post(url, headers=headers, json=course)
            print(x.text)


def set_status():
    with open('data/courses.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            url = 'https://api.horarios.barreiro.xyz/course/set-status/etse'
            course = {
                'code': row[1],
                'status': 'A',
            }
            x = requests.post(url, headers=headers, json=course)
            print(x.text)


def include():
    with open('data/courses.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            url = 'https://api.horarios.barreiro.xyz/degree/include-course/G4012P01'
            course = {
                'course': row[1],
                'year': int(row[0]),
            }
            x = requests.post(url, headers=headers, json=course)
            print(x.text)


def create_areas():
    for floor in ["Enxeñaría Química", "Docencia"]:
        url = 'https://api.horarios.barreiro.xyz/building/add-sector/2ba481e6-8ddb-4842-b40d-e993024d3298'
        data = {
            'sector': floor,
        }
        x = requests.post(url, headers=headers, json=data)
        print(x.text)


def create_rooms():
    with open('data/zonificacion.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            url = f'https://api.horarios.barreiro.xyz/building/create-room/{row[4]}'
            tmp = row[1].split("/")
            code = tmp[len(tmp) - 1].replace(".", "")
            data = {
                'code': code,
                'name': row[2],
            }

            if row[3]:
                data['capacity'] = int(row[3])
            if row[5]:
                data['floor'] = int(row[5])
            if row[6]:
                data['sector'] = row[6]

            x = requests.post(url, headers=headers, json=data)
            print(x.text)


if __name__ == "__main__":
    # create()
    # set_status()
    # include()
    # create_areas()
    # create_rooms()
    pass
