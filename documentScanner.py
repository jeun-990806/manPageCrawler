import re
import requests
from bs4 import BeautifulSoup

import pprint
import fileManagement as fm
import textAnalyzer as ta


wrongCase = '~!@#$%^&+=|\\\?\[\]{}():;\'"`<>.'

re_returnType = '(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ']+)'
re_functionName = '(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ']+)[\s]?'
re_arguments = '[(](?:[(][^0-9' + wrongCase + '][^;]+[)]|[^' + wrongCase + '])*[)]'


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


def convertToText(raw):
    paragraph = ''
    for data in raw:
        if type(data) is not str:
            if data.string is None:
                if len(data.contents) >= 1:
                    data = data.contents[0].string
                else:
                    data = ''
            else:
                data = data.string
        paragraph += data
    paragraph = paragraph.strip()
    paragraph = re.sub('[\s][\s]+', ' ', paragraph)
    return paragraph


def getWordsList(text):
    while True:
        if text == str(re.sub('/\*[\S\s]*\*/', '', text)):
            break
        text = re.sub('/\*[\S\s]*\*/', '', text)

    words = text.split(' ')
    return words


def getFullParagraph(url, headName):
    response = requests.get(url)
    result = 'CANNOT DO CRAWLING'
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        raw = soup.select('#' + headName)[0].findNext('pre').contents
        result = convertToText(raw)
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
            print(url, end='')
            if title in history:
                print()
                continue
            print(', ' + title)
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

            if len(soup.select('#SYNOPSIS')) != 0:
                text = getFullParagraph(url, 'SYNOPSIS')
            if len(soup.select('#C_SYNOPSIS')) != 0:
                text = getFullParagraph(url, 'C_SYNOPSIS')
            if len(soup.select('#NOTES')) != 0:
                text = getFullParagraph(url, 'NOTES')
                formatting = False
            if len(soup.select('#SYNOPSIS_AND_DESCRIPTION')) != 0:
                text = getFullParagraph(url, 'SYNOPSIS_AND_DESCRIPTION')
                formatting = False
            words = getWordsList(text)

            index = 0
            functionList = []
            formatStr = False

            section = []
            tmp = ''
            if formatting:  # #include에 의해 section이 나누어질 수 있는 경우
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
                        section.append(tmp)
                        tmp = ''
                    else:
                        index += 1
            else:
                section.append(text)

            for i in range(0, len(section)):
                headerFileList = []
                gnu = False

                if '_GNU_SOURCE' in section[i]:
                    gnu = True

                headerFileList = getHeaderFiles(section[i])
                if len(headerFileList) == 0:
                    reference = ''
                    if len(soup.select('#SYNOPSIS')) != 0:
                        reference = getFullParagraph(url, 'SYNOPSIS')
                    if len(soup.select('#C_SYNOPSIS')) != 0:
                        reference = getFullParagraph(url, 'C_SYNOPSIS')
                    headerFileList = getHeaderFiles(reference)
                functionData = re.findall(re_returnType + re_functionName + re_arguments, section[i])
                for function in functionData:
                    info = {}
                    arguments = []
                    level = 0
                    j = function.rfind(')')  # j는 function name과 arguments 사이의 경계이다.
                    while True:
                        if j == 0:
                            break
                        if function[j] == ')':
                            level += 1
                        if function[j] == '(':
                            level -= 1
                        if level == 0:
                            break
                        j -= 1
                    if '(' in function[:j]:
                        returnType = function[:j].split('(')[0].strip()
                        functionName = '(' + function[:j].split('(')[1].strip()
                    else:
                        functionName = function[:j].strip().split(' ')[-1]
                        returnType = function[:function[:j].rfind(functionName)].lstrip()
                        returnType = re.sub('[^\w\s]+[\S]+[\s]', '', returnType)
                        while functionName.startswith('*'):
                            functionName = functionName[1:]
                            returnType += '*'
                    tmp = re.findall('(?:[(][^' + wrongCase + ']+[)]|[^' + wrongCase + ',])+[,)]', function[j + 1:])
                    for data in tmp:
                        arguments.append(data.strip()[:-1])

                    # check header files list info
                    if len(headerFileList) == 0:
                        errors[url] = [function, 'no header info']
                        continue
                    info['header file'] = headerFileList

                    # check return type info
                    if returnType.strip().count(' ') > 3 or returnType == '':
                        errors[url] = [function, 'malformed return type']
                        continue
                    info['return type'] = returnType.strip()

                    # check arguments list info
                    if len(arguments) == 0 or (' ' not in arguments[0] and arguments[0] != 'void') or \
                            (arguments[0].split(' ')[-1].endswith('*')):
                        errors[url] = [function, 'malformed arguments']
                        continue
                    info['arguments'] = arguments

                    info['number of arguments'] = str(len(arguments))
                    if len(arguments) == 1 and arguments[0] == 'void':
                        info['number of arguments'] = '0'
                    if '...' in arguments:
                        info['number of arguments'] += ' or more'

                    info['use _GNU_SOURCE'] = gnu

                    if url.endswith('p.html'):
                        info['POSIX api'] = True
                    else:
                        info['POSIX api'] = False
                    info['url'] = url

                    if len(functionName) != 0:
                        if functionName not in result:
                            result[functionName] = [info]
                        else:
                            if not overlapVerification(result[functionName], info):
                                result[functionName].append(info)
                        functionList.append(functionName)

            # crawling description
            # * format string info
            if len(soup.select('#DESCRIPTION')) != 0:
                text = getFullParagraph(url, 'DESCRIPTION')
                if 'format string' in text:
                    formatStr = True
                    break

            for functionName in functionList:
                for i in range(0, len(result[functionName])):
                    result[functionName][i]['format string'] = formatStr

            # crawling return value
            # * meaning of return value

            if len(soup.select('#RETURN_VALUE')) != 0:
                text = getFullParagraph(url, 'RETURN_VALUE')
                text = text.replace('\n', ' ')
                for name in functionList:
                    for i in range(0, len(result[name])):
                        result[name][i]['return value'] = ta.searchTargetDescription(text, [name])

        fm.save_data(errors, 'errorlogs.dict')
    return result


def getSyscallData(urlList, target):
    result = {}
    history = []

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
            entireText = ''
            for paragraph in raw:
                for data in paragraph.contents:
                    if type(data) is not str:
                        entireText += data.string + ' '
                    else:
                        entireText += data + ' '
            remove = []
            for name in target:
                if name in entireText and 'glibc' in entireText:
                    result[name] = url
                    remove.append(name)
            if len(remove) != 0:
                for name in remove:
                    target.remove(name)
    return result
