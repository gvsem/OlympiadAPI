


import json
from difflib import get_close_matches

import numpy as np
import os
import glob

#from models.privilegejson import PrivilegeJSON
from models.scheduledOlympiad import Schedule
from parse_rsr import parse_schedule, extract_profiles_subjects, find_similar_olympiads, find_similar
from parse_specialities import parse_specialities
from util import dataToFile, loadJson, jsonToFile, nextBool, nextStr

if __name__ == '__main__':
    print("*** Olympiad API Initialization Toolkit ***")
    print("Вас приветствует мастер инициализации данных для Olympiad API.")
    print("Инициализация состоит из следующих шагов:")
    print(" > 1: Определить профили и предметы олимпиад")
    print(" > 2: Добавить олимпиады из перечней за четыре года")
    #print(" > 3: Импортировать свой университет из файла")

    print('===== Подготовка данных =====')
    year = 2022
    if nextBool('Скачать перечни РСОШ в data/schedules/?', True):
        year = int(nextStr("Укажите текущий год приема", year))
        for y in [year, year - 1, year - 2, year - 3]:
            try:
                print("Скачиваем год " + str(y) + "...")
                if y == year:
                    dataToFile(parse_schedule("https://rsr-olymp.ru", y), 'data/schedules/' + str(y) + '.json')
                else:
                    dataToFile(parse_schedule("https://rsr-olymp.ru/archive/" + str(y), y), 'data/schedules/' + str(y) + '.json')
            except Exception as e:
                print("Не получилось скачать данные для " + str(y) + "года")

    if nextBool('Извлечь профили и предметы из перечней в data/schedules/?', True):
        path = 'data/schedules/'
        profiles = []
        subjects = []
        for fn in glob.glob(os.path.join(path, '*.json')):
            p, s = extract_profiles_subjects(loadJson(fn))
            profiles = np.concatenate((profiles, p), axis=None)
            subjects = np.concatenate((subjects, s), axis=None)
        profiles = np.unique(profiles)
        subjects = np.unique(subjects)
        dataToFile(list(profiles), 'data/profiles.json')
        dataToFile(list(subjects), 'data/subjects.json')

    if nextBool('Найти похожие олимпиады и опечатки в перечнях РСОШ?', True):
        path = 'data/schedules/'
        fns = list(glob.glob(os.path.join(path, '*.json')))
        fns.sort(reverse=True)

        yall = False
        nall = False

        for i in range(len(fns) - 1):
            s1 = Schedule(**loadJson(fns[i]))
            s2 = Schedule(**loadJson(fns[i + 1]))

            sim = find_similar_olympiads(s2, s1)

            if len(sim) != 0:
                print("     Совпадения: " + fns[i] + " vs. " + fns[i + 1])
            for j in sim:
                print("     >>> " + j[0] + " ||| " + j[1])
                answer = ""
                if not yall:
                    answer = nextStr('     >>> Заменить на ' + j[1] + ' [y, n, yall, nall] ?', 'n')
                    if answer == 'yall':
                        yall = True
                    if answer == 'nall':
                        nall = True
                if ((answer == 'y') or (yall)) and not nall:
                    s1.replaceName(j[0], j[1])
                    s2.replaceName(j[0], j[1])

            dataToFile(json.loads(s1.json()), fns[i])
            dataToFile(json.loads(s2.json()), fns[i+1])

    if nextBool('Найти похожие профили/предметы в опечатках РСОШ?', True):
        path = 'data/schedules/'

        profiles = loadJson('data/profiles.json')
        subjects = loadJson('data/subjects.json')

        p_sim = find_similar(profiles)
        s_sim = find_similar(subjects)

        print("    >>> Похожие профили: ", p_sim)
        print("    >>> Похожие предметы: ", s_sim)

        if nextBool('    >>> Принять эти правки (левые)?', True):
            for i in p_sim:
                if i[1] in profiles:
                    profiles.remove(i[1])
            for i in s_sim:
                if i[1] in subjects:
                    subjects.remove(i[1])

            fns = list(glob.glob(os.path.join(path, '*.json')))
            for i in range(len(fns)):
                s = Schedule(**loadJson(fns[i]))
                for j in p_sim:
                    s.replaceProfile(j[1], j[0])
                for j in s_sim:
                    s.replaceSubject(j[1], j[0])
                dataToFile(json.loads(s.json()), fns[i])

    print("===== Подготовка к запуску вашего университета =====")
    if nextBool('Скачать перечень специальностей ОКСО 3?', True):
        # Направления подготовки бакалавриата
        specialities = parse_specialities('https://base.garant.ru/70480868/53f89421bbdaf741eb2d1ecc4ddb4c33/')
        # Направления подготовки специалитета
        specialities2 = parse_specialities('https://base.garant.ru/70480868/3e22e51c74db8e0b182fad67b502e640/')
        #specialities3 += parse_specialities('https://base.garant.ru/70480868/f7ee959fd36b5699076b35abf4f52c5c/')
        specialities = np.concatenate((specialities, specialities2), axis=0)

        dataToFile({ i[0] : i[1] for i in specialities.tolist() }, 'data/specialities.json')

        sql_cmd = "INSERT INTO programme_specialities (code, name) VALUES\n"
        for i in range(len(specialities)):
            sql_cmd += "('" + specialities[i][0] + "', '" + specialities[i][1] + "')"
            if i + 1 != len(specialities):
                sql_cmd += ",\n"

        jsonToFile(sql_cmd + ";", 'data/specialities.sql')

    print("===== Проверка данных =====")

    print(" $$$$ Проверим данные $$$$ ")

    profiles = loadJson('data/profiles.json')
    subjects = loadJson('data/subjects.json')

    p_sim = find_similar(profiles)
    s_sim = find_similar(subjects)

    print("Всего профилей и предметов: ", len(profiles), len(subjects))
    print("Похожих профилей и предметов: ", len(p_sim), len(s_sim))

    specs = loadJson('data/specialities.json')
    print("Всего специальностей: ", len(specs))
    print("Перечени олимпиад РСОШ: ")
    fns = list(glob.glob(os.path.join('data/schedules/', '*.json')))
    for i in range(len(fns)):
        s = Schedule(**loadJson(fns[i]))
        print("  >>> ", fns[i], " содержит ", len(s.olympiads), " олимпиад с ", s.countTracks(), "направлениями")