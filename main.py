import requests
from bs4 import BeautifulSoup
import pprint


def getURLList(sectionURL, start, end):
    result = []
    url_pre = 'https://man7.org/linux/man-pages'
    response = requests.get(sectionURL)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.select('td a')[start:end]
        for i in data:
            url = url_pre + i['href'][1:]
            result.append(url)
    return result


def getWordsList(raw):
    paragraph = ''
    for data in raw:
        if type(data) is not str:
            data = data.string
        paragraph += data

    paragraph = paragraph.replace('\n', ' ')
    paragraph = paragraph.strip()
    words = paragraph.split(' ')
    for i in range(0, words.count('')):
        words.remove('')

    i = 0
    while True:
        if words[i] == '/*':
            j = i + 1
            while words[j] != '*/':
                j += 1
            j += 1
            del words[i:j]
        i += 1
        if i >= len(words):
            break

    return words


def getFunctionAttr(urlList):
    result = {}

    for url in urlList:
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # crawling synopsis
            # * header files
            # * function info
            #   - name
            #   - type of return value
            #   - arguments
            #   - number of arguments
            raw = soup.select('#SYNOPSIS')[0].findNext('pre').contents
            words = getWordsList(raw)

            index = 0
            headerFileList = []
            while 1:
                info = {}
                functionName = ''
                returnType = ''
                argument = ''
                arguments = []

                if index >= len(words):
                    break

                if words[index] == '#include':
                    headerFileList = []
                    index += 1
                    headerFileList.append(words[index].replace('<', '').replace('>', ''))
                    index += 1
                    if words[index] == '#include':
                        index += 1
                        headerFileList.append(words[index].replace('<', '').replace('>', ''))
                        index += 1

                for word in words[index:]:
                    if word.find('(') != -1:
                        functionName = word.split('(')[0]
                        argument = word.split('(')[1] + ' '
                        for i in range(index, words.index(word)):
                            returnType += words[i] + ' '
                            if words[i].endswith(';'):
                                returnType = ''
                        if functionName.startswith('*'):
                            functionName = functionName.replace('*', '')
                            returnType += '*'
                        else:
                            returnType = returnType.rstrip()
                        index += words[index:].index(word) + 1
                        break
                if functionName == '':
                    break

                if argument.endswith('; '):
                    argument = argument.replace('); ', '')
                    arguments.append(argument)
                else:
                    for word in words[index:]:
                        argument += word + ' '
                        if word.endswith(','):
                            argument = argument.replace(', ', '')
                            arguments.append(argument)
                            argument = ''
                        if word.endswith(';'):
                            argument = argument.replace('); ', '')
                            arguments.append(argument)
                            index += words[index:].index(word) + 1
                            break

                info['header file'] = headerFileList
                info['return value'] = returnType
                info['number of arguments'] = len(arguments)
                info['arguments'] = arguments

                result[functionName] = info

            # crawling description
            # * format string

            raw = soup.select('#DESCRIPTION')[0].findNext('pre').contents
            words = getWordsList(raw)

    return result


urls = getURLList('https://man7.org/linux/man-pages/dir_section_3.html', 10, 30)
libFunctionData = getFunctionAttr(urls)
pprint.pprint(libFunctionData)
