import os
import re

import fileManagement
import tools

headerFilePath = 'header_files/'


def getHeaderFileList(path=None):
    global headerFilePath
    if path is not None and os.path.isdir(path):
        headerFilePath = path
    return os.listdir(headerFilePath)


def openHeaderFile(name):
    header = open(headerFilePath + name, 'r')
    return header.readlines()


def searchDefineStatement(contents):
    defineStatementRE = '#[\s]*(?:define|DEFINE)[\s]*'
    result = []
    for line in contents:
        if len(re.findall(defineStatementRE, line)):
            result.append(line)
    return result


def getFormalDS(line):
    defineStatementRE = '#[\s]*(?:define|DEFINE)[\s]*'
    formalDefineStatementRE = '#DEFINE '
    return re.sub(defineStatementRE, formalDefineStatementRE, line)


def getSymbolicConstantsList(name):
    symbolicConstantRE = '[A-Z]+[A-Z_0-9]+'
    result = []
    headerFileContents = openHeaderFile(name)
    defineStatements = searchDefineStatement(headerFileContents)
    for statement in defineStatements:
        statement = getFormalDS(statement)
        symbolicConstant = re.findall(symbolicConstantRE, statement.replace('#DEFINE ', ''))
        if len(symbolicConstant) != 0:
            result.append(symbolicConstant[0])
    return result


def getStructureList(name):
    structureRE = '(?:\ntypedef |\n)struct[^{;]*(?:\{[^}]*\}|)[^;]*;'
    headerFileContents = openHeaderFile(name)
    fullText = ''
    for content in headerFileContents:
        fullText += content
    return re.findall(structureRE, tools.removeComments(fullText))


def getStructureName(struct):
    if struct.replace('\n', '').startswith('typedef'):
        return struct.split('}')[-1].replace(';', '').strip()
    else:
        return struct.split('{')[0].replace('\n', '').replace(';', '').strip()


def getTypeNameTupleList(struct):
    structureContentRE = '{[\S\s]+}'
    fieldRE = '[a-zA-Z0-9][^;]+;'
    if len(re.findall(structureContentRE, struct)) == 0:
        return []
    content = re.findall(structureContentRE, struct)[0]
    fields = re.findall(fieldRE, content)
    typeNameTupleList = [(field[:field.rfind(' ')], field.split(' ')[-1].replace(';', '')) for field in fields]
    # 변수 이름에 붙은 asterisk를 떼어 데이터 타입에 붙인다.
    for fieldType, fieldName in typeNameTupleList:
        index = typeNameTupleList.index((fieldType, fieldName))
        for i in range(fieldName.count('*')):
            fieldType += '*'
        fieldName = fieldName.replace('*', '')
        typeNameTupleList[index] = (fieldType, fieldName)
    return typeNameTupleList


for name in getHeaderFileList():
    print(name)
    structList = getStructureList(name)
    for struct in structList:
        print(getStructureName(struct))
        fileManagement.saveData(getTypeNameTupleList(struct),
                                'structure_list/' + getStructureName(struct).replace(' ', '_') + '.list')
