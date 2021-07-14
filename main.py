import requests
from bs4 import BeautifulSoup
import pprint
import pickle
import os
import sys
import re

start = 0 + 3
targetPages = 1000
end = start + targetPages

sys.setrecursionlimit(10000)  # pickle recursion depth error.


def _save_data(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    f.close()


def _open_data(path, dataType):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, 'rb') as f:
            result = pickle.load(f)
    else:
        if dataType == 'dict':
            result = {}
        else:
            result = []
    f.close()
    return result


def checkAccuracy(fullList):
    titles = []
    founded = []
    unfounded = []
    absence = []
    response = requests.get('https://man7.org/linux/man-pages/dir_section_3.html')
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.select('td a')[start:]
        for title in data:
            titles.append(title.string.split('(')[0])

    f = open('glibcABI.txt', 'r')
    glibcList = f.read().splitlines()

    for function in glibcList:
        if function in fullList:
            founded.append(function)
        else:
            if function in titles:
                unfounded.append(function)
            else:
                absence.append(function)
    print('founded glibc(%d)' % len(founded))
    print(founded)
    print('unfounded glibc(%d)' % len(unfounded))
    print(unfounded)
    print('absent glibc(%d)' % len(absence))
    print(absence)

    _save_data(unfounded, 'unfounded.bin')
    _save_data(absence, 'absence.bin')
    f.close()
    return unfounded


def getURLList(sectionURL, targets):
    result = []
    url_pre = 'https://man7.org/linux/man-pages'
    response = requests.get(sectionURL)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.select('td a')[start:]
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
            if len(soup.select('#NOTES')) != 0:
                raw = soup.select('#NOTES')[0].findNext('pre').contents
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
                functionData = re.findall('(?:[(][^().,;<>]+[)]|[^().,;<>]+)(?:[(][^().,;]+[)]|[\S]+)[\s]?[(](?:[(][^0-9][^.,;]+[)]|[^().;])+[)]', section[i])
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
                        returnType = function[:j].strip().replace(functionName, '').strip()
                        returnType += ' '
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
                    if len(arguments) == 0 or (' ' not in arguments[0] and arguments[0] != 'void') or\
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

    _save_data(history, 'history.bin')
    if len(errors) != 0:
        print('total number of data that getFunctionAttr cannot crawling: %d' % len(errors))
        pprint.pprint(errors)
    else:
        print('there is no data that getFunctionAttr cannot crawling.')
    return result


unfoundedFunction = _open_data('unfounded.bin', 'list')
urls = getURLList('https://man7.org/linux/man-pages/dir_section_3.html', unfoundedFunction)

print('crawling from the %dth to the %dth' % (start, end))
print('(' + urls[0] + ' ~ ' + urls[len(urls) - 1] + ')', end='\n\n')

libFunctionData = _open_data('libs.bin', 'dict')
newData = getFunctionAttr(urls)
pprint.pprint(newData)
libFunctionData.update(newData)

checkAccuracy(list(libFunctionData.keys()))

_save_data(libFunctionData, 'libs.bin')
