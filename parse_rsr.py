import difflib
import json
from difflib import get_close_matches
from urllib import request
import bs4 as bs
import pandas as pd
import numpy as np
import re

from models.scheduledOlympiad import ScheduledOlympiad, Track, Schedule
from util import *


def canonical_str(s):
    s = list(s)
    hasOpened = False
    for i in range(len(s)):
        if s[i] == '"' and not hasOpened:
            s[i] = '«'
            hasOpened = True
        elif s[i] == '"' and hasOpened:
            s[i] = '»'
            hasOpened = False
    s = "".join(s)
    s = re.sub(' +', ' ', s)
    return s

def parse_schedule_table(table):
    records = []
    columns = []

    count_span = 0
    pre_record = []

    for tr in table.findAll("tr"):
        ths = tr.findAll("th")
        if ths != []:
            for each in ths:
                columns.append(each.text)
        else:
            trs = tr.findAll("td")
            record = []

            if count_span > 0:
                #record += pre_record
                count_span -= 1
            else:
                pre_record = []

            for each in trs:

                link = None
                isRowSpan = False
                try:
                    link = each.find('a')['href']
                except:
                    pass
                try:
                    if int(each['rowspan']) >= 2:
                        isRowSpan = True
                except:
                    pass

                # if link is not None:
                #     pre_record.append(link)

                if isRowSpan:
                    count_span = int(each['rowspan']) - 1
                    if link is not None:
                        pre_record.append(link)
                    pre_record.append(each.text)
                else:
                    if link is not None:
                        record.append(link)
                    record.append(each.text)

        #print(pre_record + record)
        records.append(pre_record + record)
        if len(records[-1]) != 6:
            records[-1].insert(1, None)
        #print(records[-1])

    columns = records[0]
    columns[1] = 'Ссылка'
    columns[0] = '№'
    records = records[1:]

    t = pd.DataFrame(records, columns=columns)
    t['Название'] = t['Название'].apply(lambda x: canonical_str(x.strip()))
    t['Профиль'] = t['Профиль'].apply(lambda x: x.strip())
    t['Предметы'] = t['Предметы'].apply(lambda x: [i.strip() for i in x.split(', ')])
    t['Ссылка'] = t['Ссылка'].apply(lambda x: x.strip('\n').strip('\t') if x is not None else None)

    return t

def get_schedule_table(url):

    s = request.urlopen(url).read()
    soup = bs.BeautifulSoup(s, 'lxml')
    table = soup.find('table', attrs={'class': 'mainTableInfo'})
    t = parse_schedule_table(table)

    pd.set_option('display.max_columns', 500)
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.width', 1000)

    profiles = t['Профиль'].values.flatten()
    subjects = []
    for p in t['Предметы'].values:
        subjects += p

    profiles = np.unique(np.array(profiles))
    subjects = np.unique(np.array(subjects))
    # print(len(profiles))
    # print(len(subjects))
    #print(t)

    return t

def parse_schedule(url, year):
    t = get_schedule_table(url)


    olympiads = dict()
    olympiads_names = np.unique(t['Название'])
    for name in olympiads_names:
        olympiads[name] = ScheduledOlympiad()

    for index, row in t.iterrows():
        olympiads[row['Название']].name = row['Название']
        olympiads[row['Название']].site = row['Ссылка']
        olympiads[row['Название']].tracks.append(Track.load({'name': '', 'profile': row['Профиль'], 'subjects' : row['Предметы'], 'level' : row['Уровень']}))
        olympiads[row['Название']].year = year
        olympiads[row['Название']].no = int(row['№'])

    s = Schedule()
    for o in olympiads.values():
        s.olympiads.append(o)

    return json.loads(s.json())


def extract_profiles_subjects(data):
    s = Schedule(**data)

    profiles = []
    subjects = []
    for o in s.olympiads:
        for t in o.tracks:
            profiles.append(t.profile)
            for subj in t.subjects:
                subjects.append(subj)

    return np.unique(np.array(profiles)), np.unique(np.array(subjects))

def find_similar_olympiads(s1, s2):
    result = []
    for x in s1.extractNames():
        m = get_close_matches(x, s2.extractNames(), n=3, cutoff=0.9)
        if len(m) != 0 and x not in m:
            result.append((x, m[0]))
        #print(x, " is really similar to ", m)
    return result

def find_similar(s, cut=0.9, include_prefix=False):
    result = []
    for x in s:
        m = difflib.get_close_matches(x, list(s), cutoff=cut)
        if include_prefix:
            m += [i for i in list(s) if i.startswith(x)]
        m = np.unique(m)

        if len(m) > 1:
            result.append((x, [i for i in m if i != x][0]))
    return result

if __name__ == '__main__':


    extract_profiles_subjects(loadJson('data/schedules/2022.json'))

    exit(0)

    url = "https://rsr-olymp.ru/archive/2018"

    # a = parse_schedule("https://rsr-olymp.ru/archive/2019", 2019)
    # b = parse_schedule("https://rsr-olymp.ru/archive/2020", 2020)

    dataToFile(parse_schedule("https://rsr-olymp.ru/archive/2019", 2019), 'data/schedules/2019.json')

    a = get_schedule_table("https://rsr-olymp.ru/archive/2019")
    b = get_schedule_table("https://rsr-olymp.ru/archive/2020")

    #print(a)
    #c = parse_schedule("https://rsr-olymp.ru")
    a = np.unique(a['Название'].values)
    b = np.unique(b['Название'].values)
    #c = np.unique(b['Название'].values)

    for x in b:
        m = get_close_matches(x, a, n=3, cutoff=0.8)
        if len(m) != 0 and x not in m:
            print(x, " is really similar to ", m)

    # for x in c:
    #     m = get_close_matches(x, b, n=3, cutoff=0.8)
    #     if len(m) != 0 and x not in m:
    #         print(x, " is really similar to ", m)
    #
