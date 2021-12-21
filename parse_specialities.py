from difflib import get_close_matches
from urllib import request
import bs4 as bs
import pandas as pd
import numpy as np
import re

from util import *

def parse_specialities(url):
    s = request.urlopen(url).read()
    p = pd.read_html(s)[0]

    r = []
    for i, row in p.iterrows():
        if len(str(row[0])) == 8 and not row[0].endswith('.00.00'):
            if row[0] != row[1]:
                r.append([row[0], row[1]])
            else:
                r.append([row[0], row[2]])

    r = np.unique(r, axis=0)
    return r