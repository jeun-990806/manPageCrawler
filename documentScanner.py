import re
import requests
from bs4 import BeautifulSoup

import pprint
import fileManagement as fm
import textAnalyzer as ta

'''
getURLList
sectionURL page에 존재하는 url(td 안의 a 태그로 감쌈)을 list로 반환한다.
    [option]
     * targets: 문서들의 제목이 저장된 list로 특정 문서들만 크롤링하는 데 사용한다. 비어있는 경우 전체 url을 반환한다.
     * start, end: 전체 list에서 원하는 범위를 슬라이싱하는 데 사용한다.
'''


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


'''
getTitleList
sectionURL page에 존재하는 문서들의 제목을 list로 반환한다.
'''


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


'''
getWordsList
raw(html tag와 string으로 이루어짐)를 string으로 변환한 뒤 공백을 기준으로 나눈 word list를 반환한다.
(주석은 자동으로 제거된다.)
'''


def getWordsList(raw):
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

    paragraph = paragraph.replace('â\x88\x97', '*')
    paragraph = paragraph.strip()
    words = paragraph.split(' ')
    for i in range(0, words.count('')):
        words.remove('')

    i = 0
    while True:
        if '/*' in words[i]:
            if '*/' in words[i]:
                words[i] = words[i].split('/*')[0] + words[i].split('*/')[-1]
            else:
                words[i] = words[i].split('/*')[0]
                i += 1
                while '*/' not in words[i]:
                    words[i] = ''
                    i += 1
                words[i] = words[i].split('*/')[-1]
        else:
            i += 1
        if i >= len(words):
            break
    for i in range(0, words.count('')):
        words.remove('')
    return words


def overlapVerification(data, new):
    result = False

    for i in range(0, len(data)):
        if data[i]['POSIX api'] == new['POSIX api'] and data[i]['use _GNU_SOURCE'] == new['use _GNU_SOURCE']:
            result = True
            break
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
            if len(soup.select('#SYNOPSIS')) == 0:
                if len(soup.select('#C_SYNOPSIS')) == 0:
                    if len(soup.select('#SYNOPSIS_AND_DESCRIPTION')) == 0:
                        errors[url] = 'There is no SYNOPSIS paragraph.'
                        continue
                    else:
                        raw = soup.select('#SYNOPSIS_AND_DESCRIPTION')[0].findNext('pre').contents
                        formatting = False
                else:
                    raw = soup.select('#C_SYNOPSIS')[0].findNext('pre').contents
            else:
                raw = soup.select('#SYNOPSIS')[0].findNext('pre').contents
            words = getWordsList(raw)

            index = 0
            functionList = []
            formatStr = False

            section = []
            tmp = ''
            if words.count('\n') != 0:
                for i in range(0, words.count('\n')):
                    words.remove('\n')
            if formatting:
                while index < len(words):
                    if '#' in words[index]:
                        index += 2
                        tmp += words[index - 1].replace('\n', '') + ' '
                        while index < len(words) - 2 and '#' in words[index]:
                            index += 2
                            tmp += words[index - 1].replace('\n', '') + ' '
                        while index < len(words) and '#' not in words[index]:
                            if ':' in words[index]:
                                break
                            tmp += words[index].replace('\n', '') + ' '
                            index += 1
                        section.append(tmp)
                        tmp = ''
                    else:
                        index += 1
            else:
                section.append('')
                for word in words:
                    section[0] += word.replace('\n', '') + ' '

            for i in range(0, len(section)):
                headerFileList = []
                gnu = False

                if '_GNU_SOURCE' in section[i]:
                    gnu = True

                for header in re.findall('[<]\S+[>]', section[i]):
                    headerFileList.append(header.replace('<', '').replace('>', ''))
                functionData = re.findall(
                    '(?:[(][^().,;<>]+[)]|[^().,;<>]+)(?:[(][^().,;]+[)]|[\S]+)[\s]?[(](?:[(][^0-9][^,;]+[)]|[^('
                    ');])*[)]',
                    section[i])
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
                    tmp = function[j + 1:function.rfind(')')].split(' ')

                    argument = ''
                    level = 0
                    for word in tmp:
                        argument += word + ' '
                        level += word.count('(') - word.count(')')
                        if ',' in word and level == 0:
                            argument = argument.split(',')[0]
                            arguments.append(argument.strip())
                            if len(argument.split(',')) > 1:
                                argument = argument.split(',')[1]
                            else:
                                argument = ''
                        if word == tmp[-1]:
                            arguments.append(argument.strip())

                    # check header files list info
                    if len(headerFileList) == 0:
                        continue
                    info['header file'] = headerFileList

                    # check return type info
                    if returnType.strip().count(' ') > 3 or returnType == '':
                        continue
                    info['return type'] = returnType.strip()

                    # check arguments list info
                    if len(arguments) == 0 or (' ' not in arguments[0] and arguments[0] != 'void') or \
                            (arguments[0].split(' ')[-1].endswith('*')):
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
                raw = soup.select('#DESCRIPTION')[0].findNext('pre').contents
                words = getWordsList(raw)

                fullDescription = ''
                for word in words:
                    fullDescription += word.replace('\n', '') + ' '
                    if 'string' in word:
                        if 'format string' in fullDescription:
                            formatStr = True
                            break

            for functionName in functionList:
                for i in range(0, len(result[functionName])):
                    result[functionName][i]['format string'] = formatStr

            # crawling return value
            # * meaning of return value

            if len(soup.select('#RETURN_VALUE')) != 0:
                raw = soup.select('#RETURN_VALUE')[0].findNext('pre').contents
                words = getWordsList(raw)

                sentence = ''
                for i in range(0, len(words)):
                    sentence += words[i] + ' '
                    if '.' in sentence:
                        for name in functionList:
                            for j in range(0, len(result[name])):
                                result[name][j]['return value'] = sentence.rstrip().replace('\n', '')
                        break

    fm.save_data(history, 'history.list')
    if len(errors) != 0:
        print('total number of data that getFunctionAttr cannot crawling: %d' % len(errors))
        pprint.pprint(errors)
    else:
        print('there is no data that getFunctionAttr cannot crawling.')
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
