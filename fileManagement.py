import os
import pickle
import sys
sys.setrecursionlimit(10000)


def saveData(data, path):
    dirName = path[:path.rfind('/')]
    if len(dirName) != 0 and not os.path.isdir(dirName):
        os.mkdir(dirName, mode=0o777)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    f.close()
