import pprint
import fileManagement as fm
import documentScanner as ds


def sortResult(fileName):
    libFunctionData = fm.openData(fileName)
    entire = list(libFunctionData.keys())
    founded = {}
    unfounded = []
    absence = []

    titles = ds.getTitleList('https://man7.org/linux/man-pages/dir_section_3.html')
    f = open('crawled/glibcABI.txt', 'r')
    glibcList = f.read().splitlines()

    for function in glibcList:
        if function in entire:
            founded[function] = libFunctionData[function]
        else:
            if function in titles:
                unfounded.append(function)
            else:
                absence.append(function)
    print('founded glibc(%d)' % len(founded))
    print(list(founded.keys()))
    print('unfounded glibc(%d)' % len(unfounded))
    print(unfounded)
    print('absent glibc(%d)' % len(absence))
    print(absence)

    fm.saveData(founded, 'crawled/glibc.dict')
    fm.saveData(unfounded, 'crawled/unfounded.list')
    fm.saveData(absence, 'crawled/absence.list')
    f.close()

    return unfounded


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
