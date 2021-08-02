import os
import re

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
