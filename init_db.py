import glob
import os

import numpy as np
import pymysql

from models.scheduledOlympiad import Schedule
from models.universityPrivileges import University
from util import loadJson, nextBool

if __name__ == '__main__':

    con = pymysql.connect(host='localhost',
                            user='root',
                            password='',
                            database='mydb')

    specs = loadJson('data/specialities.json')
    profiles = loadJson('data/profiles.json')
    subjects = loadJson('data/subjects.json')


    ####### Создаем профили, предметы и специальности

    with con:
        cur = con.cursor()

        if nextBool('Заполнить перечнями РСОШ?', True):
            cur.execute("TRUNCATE TABLE `profiles`")
            for i in np.unique(profiles):
                try:
                    cur.execute("INSERT INTO `profiles` (`id`, `text`) VALUES (NULL, '" + i + "')")
                except Exception as e:
                    pass

            cur.execute("TRUNCATE TABLE `subjects`")
            for i in subjects:
                    cur.execute("INSERT INTO `subjects` (`id`, `text`) VALUES (NULL, '" + i + "')")

            cur.execute("TRUNCATE TABLE `programme_specialities`")
            for i in specs.keys():
                    cur.execute("INSERT INTO `programme_specialities` (`code`, `name`, `id`) VALUES ('" + i + "', '" + specs[i] + "', NULL)")

            # cur.execute("TRUNCATE TABLE `universities`")

            #
            # exit(0)
            #


            fns = list(glob.glob(os.path.join('data/schedules/', '*.json')))
            schedules = []
            for i in range(len(fns)):
                schedules.append(Schedule(**loadJson(fns[i])))

            print(len(schedules))

            cur = con.cursor()
            cur.execute("TRUNCATE TABLE `schedules`")
            cur.execute("TRUNCATE TABLE `olympiads`")
            cur.execute("TRUNCATE TABLE `olympiad_tracks`")

            inserted_olympiads = []
            for i in schedules:
                year = i.olympiads[0].year
                cur = con.cursor()
                cur.execute("INSERT INTO `schedules` (`id`, `decree_no`, `year`) VALUES (NULL, 'xd', '" + str(year) + "')")
                print('x')

                for o in i.olympiads:
                    if o.name not in inserted_olympiads:
                        cur.execute("INSERT INTO `olympiads` (`id`, `name_ru`, `site`) VALUES (NULL, %s, %s)", (o.name, o.site if o.site is not None else ''))
                        inserted_olympiads.append(o.name)

                    con.commit()

                    for track in o.tracks:
                        try:
                            #print(o.name, track.profile)
                            cur.execute("INSERT INTO `olympiad_tracks` (`id`, `olympiad`, `name`, `profile_id`) VALUES (NULL, (SELECT id from olympiads WHERE name_ru=%s), NULL, (SELECT id from profiles WHERE text=%s))", (o.name, track.profile))
                        except Exception as e:
                            pass

                        for subj in track.subjects:
                            try:
                                cur.execute("INSERT INTO `olympiad_track_subjects` (`track_id`, `subject_id`) VALUES ( (SELECT id from olympiad_tracks where olympiad=(SELECT id from olympiads WHERE name_ru=%s) and profile_id=(select id from profiles where text=%s) ), (SELECT id from subjects WHERE text=%s) ) ", (o.name, track.profile, subj))
                            except Exception as e:
                                pass

                        try:
                            #print(o.name, track.profile)
                            cur.execute("INSERT INTO `track_levels` (`schedule_id`, `track_id`, `level`) VALUES ((SELECT id from schedules WHERE year=%s),  (SELECT id from olympiad_tracks where olympiad=(SELECT id from olympiads WHERE name_ru=%s) and profile_id=(select id from profiles where text=%s) ), %s )", (year, o.name, track.profile, track.level))
                        except Exception as e:
                            pass

            con.commit()

        if nextBool('Заполнить информацией для Университета ИТМО?', True):
            university = University(**loadJson('data/privileges/itmo.json'))

            cur.execute("TRUNCATE TABLE `universities`")
            cur.execute("TRUNCATE TABLE `faculties`")
            cur.execute("TRUNCATE TABLE `programmes`")
            cur.execute("INSERT INTO `universities` (`id`, `name_ru`) VALUES (NULL, %s)", (university.name))

            for f in university.faculties:
                cur.execute("INSERT INTO `faculties` (`id`, `university_id`, `name_full_ru`, `name_short_ru`) VALUES (NULL, (SELECT id from universities where name_ru=%s), %s, NULL)", (university.name, f.name))

                for p in f.programmes:
                    cur.execute("INSERT INTO `programmes` (`id`, `name_ru`, `code`, `faculty_id`) VALUES (NULL, %s, %s, (SELECT id from faculties where name_full_ru=%s and university_id=(SELECT id from universities where name_ru=%s) ))", (p.name, p.code, f.name, university.name))

            con.commit()

            year = 2022
            cur.execute("TRUNCATE TABLE `privileges`")
            cur.execute("TRUNCATE TABLE `privilege_grades`")
            cur.execute("TRUNCATE TABLE `privilege_olympiads`")
            cur.execute("TRUNCATE TABLE `privilege_subjects`")

            for f in university.faculties:
                for p in f.programmes:
                    print(">>>>>> ", p.name)
                    for priv in p.privileges:
                        for level in priv.levels:
                            plh = (p.name, f.name, university.name, level, 1 in priv.diplomas, 2 in priv.diplomas, 3 in priv.diplomas, priv.profile, 1 if priv.bvi else 0)
                            cur.execute("INSERT INTO `privileges` (`id`, `programme_id`, `level`, `scope_diploma_1`, `scope_diploma_2`, `scope_diploma_3`, `scope_profile_id`, `is_bvi`) VALUES (NULL,  (select id from programmes where name_ru=%s and faculty_id=(SELECT id from faculties where name_full_ru=%s and university_id=(SELECT id from universities where name_ru=%s) )), %s, %s, %s, %s, (select id from profiles where text=%s), %s)", plh)
                            con.commit()
                            priv_id = cur.lastrowid
                            for grade in priv.grades:
                                cur.execute("INSERT INTO `privilege_grades` (`privilege_id`, `grade`) VALUES (%s, %s)", (priv_id, grade))
                            for olymp in priv.olympiads:
                                try:
                                    cur.execute("INSERT INTO `privilege_olympiads` (`privilege_id`, `track_id`) VALUES (%s, (select id from olympiad_tracks where profile_id=(select id from profiles where text=%s) and olympiad=(select id from olympiads where name_ru=%s)))", (priv_id, priv.profile, olymp))
                                except Exception as e:
                                    print("Не получилось импортировать такую льготу:", olymp, priv.profile)
                                    print("Откатываемся...")
                                    cur.execute("DELETE FROM `privileges` WHERE `privileges`.`id` = %s", (priv_id))
                            for subj in priv.subjects:
                                cur.execute("INSERT INTO `privilege_subjects` (`privilege_id`, `subject_id`) VALUES (%s,(select id from subjects where text=%s))", (priv_id, subj))
        con.commit()