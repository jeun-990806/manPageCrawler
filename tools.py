import pprint
import fileManagement as fm
import documentScanner as ds


def sortResult(fileName):
    libFunctionData = fm.open_data(fileName)
    entire = list(libFunctionData.keys())
    founded = {}
    unfounded = []
    absence = []

    titles = ds.getTitleList('https://man7.org/linux/man-pages/dir_section_3.html')
    f = open('glibcABI.txt', 'r')
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

    fm.save_data(founded, 'glibc.dict')
    # fm.save_data(unfounded, 'unfounded.list')
    # fm.save_data(absence, 'absence.list')
    f.close()

    return unfounded


def deleteElement(fileName, target):
    targetDict = fm.open_data(fileName)
    del targetDict[target]
    fm.save_data(targetDict, fileName)


def printDictionary(fileName):
    targetDict = fm.open_data(fileName)
    pprint.pprint(targetDict)


def printList(fileName):
    targetList = fm.open_data(fileName)
    print(targetList)