import pprint
import re

import fileManagement as fm


def deleteElement(fileName, target):
    targetDict = fm.openData(fileName)
    del targetDict[target]
    fm.saveData(targetDict, fileName)


def printDictionary(fileName):
    pp = pprint.PrettyPrinter(width=50)
    targetDict = fm.openData(fileName)
    pp.pprint(targetDict)


def printList(fileName):
    targetList = fm.openData(fileName)
    for target in targetList:
        print(target)


def compareDictToList(file1, file2):
    d = fm.openData(file1)
    li = fm.openData(file2)
    print(set(li) - set(d.keys()))


def updateDict(destination, source):
    dict1 = fm.openData(destination)
    dict2 = fm.openData(source)
    dict1.update(dict2)
    fm.saveData(dict1, destination)


def removeComments(text):
    if str(type(text)) == '<class \'str\'>':
        while True:
            if text == str(re.sub('/\*(?:[^*]|\*(?!/))*\*/', '', text)):
                break
            text = re.sub('/\*(?:[^*]|\*(?!/))*\*/', '', text)
        return text
