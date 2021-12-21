import json

def loadJson(fn):
    with open(fn, encoding='UTF-8') as f:
        return json.load(f)

def jsonToFile(json, fn):
    f = open(fn, "w", encoding='UTF-8')
    f.write(json)
    f.close()

def dataToFile(data, fn):
    jsonToFile(json.dumps(data, indent=3), fn)


def nextBool(s, default):
    x = str(input(s + (' [Y]' if default else ' [n]'))).strip()
    if x in ['Y', 'y', 'yes']:
        return True
    if x in ['N', 'n', 'no']:
        return False
    return default

def nextStr(s, default):
    x = input(s + (' [' + str(default) + ']'))
    if x != '':
        return str(x)
    return default