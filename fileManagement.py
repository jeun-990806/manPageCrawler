import os
import pickle
import csv
import sys
sys.setrecursionlimit(10000)


def saveData(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    f.close()


def openData(path):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, 'rb') as f:
            result = pickle.load(f)
        f.close()
    else:
        if path.endswith('.dict'):
            result = {}
        if path.endswith('.list'):
            result = []
    return result


'''def saveDictToCsv(data, fileName):
    with open(fileName, 'w') as f:
        w = csv.writer(f)
        w.writerow(['function name', 'header files', 'return type', 'arguments', 'number of arguments', 'format string',
                    'POSIX api', 'use _GNU_SOURCE'])
        for name in data.keys():
            w.writerow([name, data[name][0]['header file'], data[name][0]['return type'],
                        data[name][0]['arguments'], data[name][0]['number of arguments'],
                        data[name][0]['format string'], data[name][0]['POSIX api'],
                        data[name][0]['use _GNU_SOURCE']])
            if len(data[name]) > 1:
                w.writerow([' ', data[name][1]['header file'], data[name][1]['return type'],
                            data[name][1]['arguments'], data[name][1]['number of arguments'],
                            data[name][1]['format string'], data[name][1]['POSIX api'],
                            data[name][1]['use _GNU_SOURCE']])'''
