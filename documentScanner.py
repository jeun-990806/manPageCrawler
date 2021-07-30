import pprint
import re
import requests
from bs4 import BeautifulSoup

import fileManagement as fm
import textAnalyzer as ta

wrongCase = '~!@#$%^&+=|\\\?\[\]{}():;\'"`<>.'
returnTypeRE = '(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ']+)'
functionNameRE = '(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ']+)[\s]?'
argumentsRE = '[(](?:[(][^0-9' + wrongCase + '][^;]+[)]|[^' + wrongCase + '])*[)]'


def getURLList(sectionURL, targets, start, end):
    result = []
    url_pre = 'https://man7.org/linux/man-pages'
    response = requests.get(sectionURL)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        if start == end:
            data = soup.select('td a')
        else:
            data = soup.select('td a')[start:end]
        if len(targets) == 0:
            for i in data:
                url = url_pre + i['href'][1:]
                result.append(url)
        else:
            for i in data:
                if i.string.split('(')[0] in targets:
                    url = url_pre + i['href'][1:]
                    result.append(url)
    return result


def getTitleList(sectionURL):
    titles = []
    response = requests.get(sectionURL)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.select('td a')
        for title in data:
            titles.append(title.string.split('(')[0])
    return titles


def trimWhiteSpace(text):
    if str(type(text)) == '<class \'str\'>':
        text = text.strip()
        text = re.sub('[\s][\s]+', ' ', text)
        return text


def removeComment(text):
    if str(type(text)) == '<class \'str\'>':
        while True:
            if text == str(re.sub('/\*[\S\s]*\*/', '', text)):
                break
            text = re.sub('/\*[\S\s]*\*/', '', text)
        return text


def convertToStr(raw):
    text = ''

    for data in raw:
        if type(data) is not str:
            if data.string is None:
                if len(data.contents) != 0:
                    data = data.contents[0].string
                else:
                    data = ''
            else:
                data = data.string
        text += data

    return trimWhiteSpace(text)


def getWordsList(text):
    return removeComment(text).split(' ')


def getAParagraph(url, headName):
    response = requests.get(url)
    result = ''
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        if len(soup.select('#' + headName)) == 0:
            return result
        raw = soup.select('#' + headName)[0].findNext('pre').contents
        result = convertToStr(raw)
    return result


def overlapVerification(data, new):
    result = False

    for i in range(0, len(data)):
        if data[i]['POSIX api'] == new['POSIX api'] and data[i]['use _GNU_SOURCE'] == new['use _GNU_SOURCE']:
            result = True
            break
    return result


def getHeaderFiles(text):
    result = []
    headers = re.findall('<[^' + wrongCase + ']+\.h>', text)
    for header in headers:
        result.append(header.replace('<', '').replace('>', ''))
    return result


def getFunctionName(text):
    argumentStartIndex = text.rfind(')')  # j는 function name과 arguments 사이의 경계이다.
    level = 0
    while True:
        if argumentStartIndex == 0:
            break
        if text[argumentStartIndex] == ')':
            level += 1
        if text[argumentStartIndex] == '(':
            level -= 1
        if level == 0:
            break
        argumentStartIndex -= 1
    if '(' in text[:argumentStartIndex]:
        returnType = text[:argumentStartIndex].split('(')[0].strip()
        functionName = '(' + text[:argumentStartIndex].split('(')[1].strip()
    else:
        functionName = text[:argumentStartIndex].strip().split(' ')[-1]
        returnType = text[:text[:argumentStartIndex].rfind(functionName)].lstrip()
        returnType = re.sub('[^\w\s]+[\S]+[\s]', '', returnType)
        while functionName.startswith('*'):
            functionName = functionName[1:]
            returnType += '*'

    return returnType, functionName, argumentStartIndex


def checkPOSIXapi(url):
    if url.endswith('p.html'):
        return True
    return False


def makeOneDict(keys, values):
    result = {}
    for key, value in keys, values:
        result[key] = value
    return result


def checkValidHeaderList(headerFileList):
    if len(headerFileList) == 0:
        return 'header'
    return ''


def checkValidReturnType(returnType):
    if returnType.strip().count(' ') > 3 or returnType == '':
        return 'return type'
    return ''


def checkValidArgument(arguments):
    if len(arguments) == 0 or (' ' not in arguments[0] and arguments[0] != 'void'):
        return 'arguments'
    return ''


def getFunctionAttr(urlList):
    result = {}
    errors = {}
    history = []

    for url in urlList:
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            title = soup.select('h1')[0].string.split(' ')[0]
            if title in history:
                continue
            history.append(title)

            # crawling synopsis
            # * header files
            # * function info
            #   - name
            #   - type of return value
            #   - arguments
            #   - number of arguments
            formatting = True
            text = ''

            for paragraph in ['SYNOPSIS', 'C_SYNOPSIS', 'SYNOPSIS_AND_DESCRIPTION']:
                if paragraph == 'SYNOPSIS_AND_DESCRIPTION':
                    formatting = False
                text = getAParagraph(url, paragraph)
                if text != '':
                    break
            words = getWordsList(text)

            index = 0
            functionList = []

            # 리팩토링!!=======================================================
            sectionList = []
            tmp = ''
            if formatting:  # #include에 의해 section 나누어질 수 있는 경우
                while index < len(words):
                    if '#' in words[index]:
                        index += 2
                        tmp += words[index - 1] + ' '
                        while index < len(words) - 2 and '#' in words[index]:
                            index += 2
                            tmp += words[index - 1] + ' '
                        while index < len(words) and '#' not in words[index]:
                            if ':' in words[index]:
                                break
                            tmp += words[index] + ' '
                            index += 1
                        sectionList.append(tmp)
                        tmp = ''
                    else:
                        index += 1
            else:
                sectionList.append(text)
            # 리팩토링!!=======================================================

            for i in range(0, len(sectionList)):

                if '_GNU_SOURCE' in sectionList[i]:
                    gnu = True
                else:
                    gnu = False

                headerFileList = getHeaderFiles(sectionList[i])
                if len(headerFileList) == 0:
                    reference = getAParagraph(url, 'SYNOPSIS')
                    reference += getAParagraph(url, 'C_SYNOPSIS')
                    headerFileList = getHeaderFiles(reference)

                functionData = re.findall(returnTypeRE + functionNameRE + argumentsRE, sectionList[i])
                for function in functionData:
                    returnType, functionName, argumentStart = getFunctionName(function)

                    arguments = []
                    tmp = re.findall('(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ',])+[,)]',
                                     function[argumentStart + 1:])
                    for data in tmp:
                        arguments.append(data.strip()[:-1])

                    # check header files list info
                    validCheckResult = checkValidHeaderList(headerFileList) + \
                                   checkValidReturnType(returnType) + checkValidArgument(arguments)
                    if validCheckResult != '':
                        errors[url] = [function, 'in ' + validCheckResult]
                    else:
                        info = makeOneDict(['header file', 'return type', 'arguments', 'number of arguments',
                                            'use _GNU_SOURCE', 'POSIX api'],
                                           [headerFileList, returnType.strip(), arguments, str(len(arguments)),
                                            gnu, checkPOSIXapi(url)])

                        if len(arguments) == 1 and arguments[0] == 'void':
                            info['number of arguments'] = '0'
                        if '...' in arguments:
                            info['number of arguments'] += ' or more'

                        if len(functionName) != 0:
                            if functionName not in result:
                                result[functionName] = [info]
                            else:
                                if not overlapVerification(result[functionName], info):
                                    result[functionName].append(info)
                            functionList.append(functionName)

            # crawling description
            # * format string info
            formatStr = False
            text = getAParagraph(url, 'DESCRIPTION')
            if 'format string' in text:
                formatStr = True

            for functionName in functionList:
                for i in range(0, len(result[functionName])):
                    result[functionName][i]['format string'] = formatStr

            # crawling return value
            # * meaning of return value

            text = getAParagraph(url, 'RETURN_VALUE')
            for name in functionList:
                for i in range(0, len(result[name])):
                    result[name][i]['return value'] = ta.searchTargetDescription(text, [[name], ['these']], False)

        fm.saveData(errors, 'error-log.dict')
    return result


def getSyscallData(urlList, target):
    result = []
    history = []

    print('syscall(%d): ' % len(target))
    print(target)

    for url in urlList:
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            title = soup.select('h1')[0].string.split(' ')[0]
            print(url, end='')
            if title in history:
                print()
                continue
            print(', ' + title)
            history.append(title)

            # crawling entire document
            raw = soup.find_all('pre')[2:]
            text = ''
            name = url.split('/')[-1].split('.')[0]
            for paragraph in raw:
                text += convertToStr(paragraph)
            if len(ta.searchTargetDescription(text, [[name, 'glibc'], ['function', 'glibc']], True)) != 0:
                target.remove(name)
                result.append(name)
    print('no glibc(%d):' % len(target))
    print(target)
    print('glibc(%d): ' % len(result))
    print(result)
    return result


def getSymbolicConstants(urlList):
    simpleFunctionNameRE = '[a-zA-Z_]+\(\)'
    symbolicConstantRe = '(?:^|: )[A-Z]+[A-Z_0-9]+'
    result = {}
    noCoreSentence = []
    noSavedData = []
    for url in urlList:
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select('h1')[0].string.split('(')[0]
            text = getAParagraph(url, 'DESCRIPTION')

            sentList = ta.getSentTokenizedList(text)
            sectionStartSent = ta.searchTargetDescription(text,
                                                          [['symbolic', 'constant', 'argument'],
                                                           ['symbolic', 'constant', 'flag']], False)
            tmp = {}
            constants = []
            functionName = ''
            argumentName = []

            for sent in sentList:
                if sent in sectionStartSent:
                    if len(constants) != 0 and functionName != '':
                        functionName = functionName.strip()
                        if functionName not in tmp.keys():
                            tmp[functionName] = []
                        if len(argumentName) == 0:
                            argumentName = ['flag']
                        argumentAndConstants = (argumentName, constants)
                        tmp[functionName].append(argumentAndConstants)
                        result[functionName] = tmp[functionName]
                        constants = []
                        functionName = ''
                        argumentName = []
                    functionNameList = re.findall(simpleFunctionNameRE, sent[:sent.rfind(':')])
                    if len(functionNameList) == 0:
                        functionNameList = re.findall(simpleFunctionNameRE, text)
                    for name in functionNameList:
                        if name not in functionName:
                            functionName += name + ' '
                    argumentInfo = re.findall('[a-zA-Z_]+ (?:argument)', sent[:sent.rfind(':')])
                    for argument in argumentInfo:
                        argumentName.append(argument.replace(' argument', ''))

                if len(sectionStartSent) != 0:  # 핵심 sentence가 등장하지 않으면 아예 constant 수집을 하지 않음.
                    constant = re.findall(symbolicConstantRe, sent)
                    if len(constant) != 0:
                        constants.append(constant[0].replace(': ', ''))
                    if functionName == '':
                        functionNameList = re.findall(simpleFunctionNameRE, sent)
                        for name in functionNameList:
                            if name not in functionName:
                                functionName += name + ' '
            if len(constants) != 0 and functionName != '':
                functionName = functionName.strip()
                if functionName not in tmp.keys():
                    tmp[functionName] = []
                if len(argumentName) == 0:
                    argumentName = ['flag']
                argumentAndConstants = (argumentName, constants)
                tmp[functionName].append(argumentAndConstants)
                result[functionName] = tmp[functionName]

            print(title + ": " + url)
            print(re.findall('[A-Z]+[A-Z_0-9]+', text))
            print(sectionStartSent)
            if len(sectionStartSent) == 0:
                noCoreSentence.append(url)
            if len(sectionStartSent) != 0 and len(tmp) == 0:
                noSavedData.append(url)
            pprint.pprint(tmp)
    fm.saveData(noCoreSentence, 'crawled/section0-noCore.list')
    fm.saveData(noSavedData, 'crawled/section0-noData.list')
    return result
