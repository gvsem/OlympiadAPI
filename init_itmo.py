import difflib
import glob
import os
import re

import numpy as np
import pandas as pd

from models.scheduledOlympiad import Schedule
from models.universityPrivileges import University, Faculty, Programme, Privilege
from util import *

import json
from pydantic import BaseModel

class PrivilegeJSON(BaseModel):

    code: str = ''
    programme_name: str = ''
    programme_spec: str = ''
    olympiads: list = []
    grades: list = []
    levels: list = []
    profile: str = ''
    subjects: list = []
    ege_subject: str = ''
    diplomas: list = []
    bvi: bool = False

    # def __init__(self):
    #     self.code = ''
    #     self.programme_name = ''
    #     self.olympiads = []
    #     self.grades = []
    #     self.levels = []
    #     self.profile = []
    #     self.subjects = []
    #     self.ege_subject = []
    #     self.diplomas = []
    #     self.bvi = False

    @staticmethod
    def load(data):
        return PrivilegeJSON(**data)

    def print(self):
        print("БВИ" if self.bvi else "100")
        print(self.code, " ", self.programme_name)
        print(self.grades, " ", self.levels, " ", self.diplomas)
        print(self.profile, " | ", self.subjects, " | ", self.ege_subject)
        print(self.olympiads)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


def get_programmes(fn):

    with open('resources/programmes.json', encoding='UTF-8') as f:
        data = np.array(json.load(f), dtype=object)

    d = dict()
    for i in data:
        for j in i[1]:
            # print(i[0])
            # print(j)
            d[j] = i[0]
    #data = dict(zip(data[:, 1], data[:, 0]))
    return d

tokens_no_olympiads = ['Все из перечня олимпад школьников',
                      '*']

def scmp(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.7

def scmp_in(a, b):
    max_r = 0.0
    for i in b:
        max_r = max(max_r, difflib.SequenceMatcher(None, a, i).ratio())
    return max_r > 0.9


programmeCode = re.compile(r'\d\d\.\d\d\.\d\d')
olympiadLevels = re.compile(r'(I|II|III)')

def containsPrivileges(table):
    t = table.to_string()
    if programmeCode.findall(t) != []:
        return True
    if olympiadLevels.findall(t) != []:
        return True
    return False

def getPrivilegeTable(tables):
    r = []
    for i in range(len(tables)):
        t = tables[i].df
        if containsPrivileges(t):
            if len(r) == 0:
                r = t
            else:
                r = pd.concat([r, t])
    return r

def itmoSchedule(t, bvi=False, grades=[]):
    t = t.replace(r'\n', '', regex=True)

    privileges = []

    current = []
    for i, row in t.iterrows():
        if len(current) == 0:
            current = row
            continue
        for j, v in row.iteritems():
            if v != '':
                current[j] = v
        #print(current)

        #print(current.values[0])
        programmes = re.split(', ', current.values[0])
        programmes = re.findall(r'\d\d\.\d\d\.\d\d[^\d]+', current.values[0])
        #print(programmes)
        for programme in programmes:
            programme = re.sub(r'[, ]*$', '', programme)
            n = re.split(' ', programme, maxsplit=1)
            #print(n)
            p = PrivilegeJSON()
            p.code = n[0]
            p.programme_spec = n[1]
            if not scmp_in(current[1], tokens_no_olympiads):
                p.olympiads = re.split(', ', current[1])
            else:
                p.olympiads = []
            p.profile = current[2]
            p.ege_subject = current[3]

            p.levels = re.findall(r'(1|2|3|I|II|III)', current[4])
            if 'I' in p.levels:
                p.levels.remove('I')
                p.levels.append(1)
            if 'II' in p.levels:
                p.levels.remove('II')
                p.levels.append(2)
            if 'III' in p.levels:
                p.levels.remove('III')
                p.levels.append(3)

            if scmp(current[5], 'Победитель'):
                p.diplomas = [1]
            elif scmp(current[5], 'Призер'):
                p.diplomas = [2, 3]
            elif scmp(current[5], 'Победитель или призер'):
                p.diplomas = [1, 2, 3]

            if grades == []:
                p.grades = re.split(', ', current[6])
            else:
                p.grades = grades

            p.bvi = bvi
            privileges.append(p)

    return privileges

import ctypes
from ctypes.util import find_library
find_library("".join(("gsdll", str(ctypes.sizeof(ctypes.c_voidp) * 8), ".dll")))
from camelot import read_pdf


# programmes = re.findall(r'\d\d\.\d\d\.\d\d[^\d\,]+', '27.03.05 Инноватика, 38.03.05 Бизнес-информатика')
# print(programmes)
# exit()

# levels = re.sub(r'^([\d, ])', '', '1, 2 или 3')
# levels = re.findall(r'(1|2|3|I|II|III)', '1, 2 или 3')
# levels = re.findall(r'(I|II|III)', '1, 2 или 3')
# print(levels)
# exit()

# tables = read_pdf("rsosh_2022_bvi.pdf", pages='all')
# t = getPrivilegeTable(tables)
# privileges = itmoSchedule(t, bvi=True, grades=[10, 11])

def replaceWithAppropriate(s, c):
    if s in c:
        return s
    else:
        m = difflib.get_close_matches(s, c, cutoff=0.6)
        if len(m) != 0:
            return m[0]
        else:
            print("Нет такой буквы...", s)
            assert False

def replaceWithAppropriates(s, c):
    if len(s) == 0:
        return s
    return [replaceWithAppropriate(i, c) for i in s]

if __name__ == '__main__':

    path_bvi = "resources/rsosh_2022_bvi.pdf"
    path_100 = "resources/100ballov_2022.pdf"

    print("*** Мастер инициализации особых прав Университета ИТМО ***")
    print("Это специальная утилита для автоматической загрузки данных из приказов.")
    print("Пути к файлам можно задать в скрипте.")
    print("приказ о 100 баллах: ", path_100)
    print("приказ о бви: ", path_bvi)

    if nextBool('Нажмите enter, чтобы начать с нуля', True):

        print("Читаем pdf о 100 баллах...")
        tables = read_pdf(path_100, pages='all')
        t = getPrivilegeTable(tables)
        t.to_html('data/html/itmo_100.html')
        privileges = itmoSchedule(t, bvi=False, grades=[10, 11])

        print("Читаем pdf о БВИ...")
        tables = read_pdf(path_bvi, pages='all')
        t = getPrivilegeTable(tables)
        t.to_html('data/html/itmo_bvi.html')
        privileges += itmoSchedule(t, bvi=True, grades=[10, 11])

        json_text = '[' + ',\n'.join([p.toJSON() for p in privileges]) + ']'


        jsonToFile(json_text, "data/temp/itmo.json")

    data = loadJson('data/temp/itmo.json')

# # Отсортировать некорректные названия программ
#
# def findSimilarProgrammeNames(json):
#
#     result = []
#     programmes = []
#     for p_json in json:
#         privilege = Privilege.load(p_json)
#         programmes.append([privilege.code, privilege.programme_spec])
#     programmes = np.unique(programmes, axis=0)
#
#     for x in programmes:
#         m = difflib.get_close_matches(x[1], list(programmes[:, 1]), cutoff=0.8)
#         m += [i for i in list(programmes[:, 1]) if i.startswith(x[1])]
#         m = np.unique(m)
#
#         if len(m) > 1:
#             result.append((x[1], [i for i in m if i != x[1]][0]))
#
#     return result
#
# similarProgrammes = findSimilarProgrammeNames(data)
# #print(similarProgrammes)
#
# for p in similarProgrammes:
#     print(p[0], " is really similar to ", p[1])
#     print("gotta choose: ", p[1])
#     for i in data:
#         if i['programme_spec'] == p[0]:
#             i['programme_spec'] = p[1]

    print("Дело за малым: обновим информацию о специальностях")

    pnames = get_programmes("resources/programmes.json")
    specs = loadJson('data/specialities.json')
    for i in data:
        i['programme_name'] = pnames[i['code']]
        i['programme_spec'] = specs[i['code']]

    profiles = loadJson('data/profiles.json')
    subjects = loadJson('data/subjects.json')

    olympiad_names = []
    fns = list(glob.glob(os.path.join('data/schedules/', '*.json')))
    for i in range(len(fns)):
        names = Schedule(**loadJson(fns[i])).extractNames()
        for j in names:
            olympiad_names.append(j)
    olympiad_names = list(np.unique(np.array(olympiad_names)))

    u = University()
    u.name = 'Университет ИТМО'

    programmes = dict()

    for row in data:
        if row['programme_name'] not in programmes:
            programmes[row['programme_name']] = Programme()
            programmes[row['programme_name']].name = row['programme_name']
            programmes[row['programme_name']].speciality = row['programme_spec']
            programmes[row['programme_name']].code = row['code']
        p = Privilege()
        p.levels = [int(i) for i in row['levels']]
        p.grades = [int(i) for i in row['grades']]
        p.diplomas = [int(i) for i in row['diplomas']]
        p.profile = replaceWithAppropriate(row['profile'], profiles)
        if len(row['subjects']) == 0:
            p.subjects.append(replaceWithAppropriate(row['ege_subject'], subjects))
        else:
            p.subjects = replaceWithAppropriates(row['subjects'], subjects)
        # print(row)
        # break
        p.bvi = row['bvi']
        p.olympiads = replaceWithAppropriates(row['olympiads'], olympiad_names)
        p.ege_subject = replaceWithAppropriate(row['ege_subject'], subjects)

        programmes[row['programme_name']].privileges.append(p)

    u.faculties.append(Faculty())
    u.faculties[0].name = 'Факультет информационных технологий и программирования'
    u.faculties[0].programmes = list(programmes.values())[0:2]
    u.faculties.append(Faculty())
    u.faculties[1].name = 'другие факультеты Университета ИТМО'
    u.faculties[1].programmes = list(programmes.values())[2:]

    jsonToFile(u.json(), "data/privileges/itmo.json")
    pd.read_json("data/privileges/itmo.json").to_html('data/html/itmo.html')

