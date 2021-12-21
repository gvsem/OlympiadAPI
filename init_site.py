import math

import numpy as np
import pandas as pd
import pymysql

from util import jsonToFile

if __name__ == '__main__':
    con = pymysql.connect(host='localhost',
                          user='root',
                          password='',
                          database='mydb')


    ####### Создаем главную страницу

    with con:
        cur = con.cursor(pymysql.cursors.DictCursor)

        html = """
            <h2>Университеты</h2>
            
        """

        cur4 = con.cursor(pymysql.cursors.DictCursor)
        cur4.execute("select * from info_programme_privileges") # where programme_id = %s", (p['id']))
        all_privileges = pd.DataFrame(cur4.fetchall())

        cur.execute("select * from universities")
        for u in cur:
            html += '<li><a href="university/' + str(u['id']) + '.html">' + str(u['name_ru']) + '</a></li>'

            #continue

            cur2 = con.cursor(pymysql.cursors.DictCursor)
            cur2.execute("select * from faculties where university_id = %s", (u['id']))
            html2 = '<h2>' + str(u['name_ru']) + '</h2>' + "\n"
            for f in cur2:
                html2 += '<li><a href="../faculty/' + str(f['id']) + '.html">' + str(f['name_full_ru']) + '</a></li>'

                #html3 = '<h2><a href="../faculty/' + str(f['id']) + '.html">' + str(f['name_full_ru']) + '</a></h2>' + "\n"
                html3 = '<h2>' + str(f['name_full_ru']) + '</h2>' + "\n"
                html3 += '<h3><a href="../university/' + str(u['id']) + '.html">' + str(u['name_ru']) + '</a></h3>' + "\n"

                cur3 = con.cursor(pymysql.cursors.DictCursor)
                cur3.execute("select * from info_programmes where faculty_id = %s", (f['id']))

                programmes = pd.DataFrame(cur3.fetchall())
                #print(programmes)
                programmes['name_ru'] = programmes['name_ru'].apply(lambda x: '<a href="../programme/' + str(int(programmes[programmes['name_ru'] == x]['id'])) + '.html">' + x + '</a>') #= '<a href="../programme/' + str(programmes['id']) + '">' + programmes['name_ru'] + '</a>'

                html3 += programmes[['name_ru', 'code']].to_html(escape=False)
                jsonToFile(html3, 'data/site/faculty/' + str(f['id']) + '.html')

                for _, p in programmes.iterrows():

                    html4 = '<h2>' + str(p['name_ru']) + '</h2>' + "\n"
                    html4 += '<h3>' + str(p['code']) + ' ' + str(p['speciality']) + '</h3>' + "\n"

                    #html4 += '<h3>' + str(p['code]) + ' | ' + str(p['speciality']) + '</h3>' + "\n"

                    #SELECT * FROM `info_programme_privileges`
                    html4 += '<h3>' + '<a href="../faculty/' + str(f['id']) + '.html">' + str(f['name_full_ru']) + '</a>' + ' | ' + '<a href="../university/' + str(u['id']) + '.html">' + str(u['name_ru']) + '</a>' + '</a></h3>'

                    privileges = all_privileges[all_privileges['programme_id'] == p['id']]
                    #privileges = privileges[(privileges['track_id'] == pd.nan) ^ (privileges['closed_track_id'] == pd.nan)]
                    # print(list(privileges['olympiad_name'].notnull()))
                    # print(list(privileges['olympiad_name']))
                    # exit(0)
                    privileges = privileges[privileges['olympiad_name'].notnull()]
                    privileges['is_bvi'] = privileges['is_bvi'].map({1: 'БВИ', 0: '100 баллов'})
                    #privileges[privileges['is_bvi'] == 1, 'is_bvi'] = 'БВИ'
                    #privileges[privileges['is_bvi'] == 0, 'is_bvi'] = '100 баллов'
                    # print(privileges.to_html('lal.html'))
                    # exit(0)

                    #priv_olids = [p['track_id'] if p['track_id'] is not None else p['closed_track_id'] for _, p in privileges.iterrows()]
                    #privileges['track_id'].apply(lambda x: x[''])
                    privileges = privileges[privileges['programme_id'] == p['id']][['level', 'is_bvi', 'profile', 'olympiad_name', 'grades', 'years', 'track_id', 'closed_track_id', 'scope_diploma_1', 'scope_diploma_2', 'scope_diploma_3']]
                    for priv_i, priv in privileges.iterrows():
                        #if (priv['olympiad_name'] is not None) and priv['olympiad_name'] != 'None':
                        try:
                            privileges.loc[priv_i, 'olympiad_name'] = '<a href="../olympiad/' + str(int(priv['track_id'] if (not math.isnan(priv['track_id']) ) else priv['closed_track_id'])) + '.html">' + priv['olympiad_name'] + '</a>'
                            if priv['scope_diploma_1'] == 1 and priv['scope_diploma_2'] == 1 and priv['scope_diploma_3'] == 1:
                                privileges.loc[priv_i, 'scope_diploma_1'] = "Любой диплом"
                            if priv['scope_diploma_1'] == 1 and priv['scope_diploma_2'] == 0 and priv['scope_diploma_3'] == 0:
                                privileges.loc[priv_i, 'scope_diploma_1'] = "Победитель"
                            if priv['scope_diploma_1'] == 0 and priv['scope_diploma_2'] == 1 and priv['scope_diploma_3'] == 1:
                                privileges.loc[priv_i, 'scope_diploma_1'] = "Призер"
                        except:
                        #else:
                            print(priv)
                    privileges = privileges[['grades', 'is_bvi', 'level', 'profile', 'olympiad_name', 'years', 'scope_diploma_1']]
                    privileges.set_index(['grades', 'is_bvi', 'level', 'profile', 'olympiad_name', 'years'], inplace=True)
                    html4 += privileges.to_html(escape=False)

                    jsonToFile(html4, 'data/site/programme/' + str(p['id']) + '.html')

            jsonToFile(html2, 'data/site/university/' + str(u['id']) + '.html')


        jsonToFile(html, 'data/site/index.html')

