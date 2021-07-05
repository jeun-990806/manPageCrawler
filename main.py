import requests
from bs4 import BeautifulSoup
import pprint

errors = {}

start = 0 + 3
targetPages = 100
end = start + targetPages


def getURLList(sectionURL):
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
            while words[j] != '*/' and j < len(words) - 1:
                j += 1
            if words[j].endswith(';'):
                words[j] = words[j].replace('*/', '')
                del words[i:j]
                words[j - (j - i) - 1] += words[j - (j - i)]
                words.pop()
            else:
                j += 1
                del words[i:j]
        i += 1
        if i >= len(words):
            break

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
            if len(soup.select('#SYNOPSIS')) == 0:
                errors[url] = 'There is no SYNOPSIS paragraph.'
                continue
            raw = soup.select('#SYNOPSIS')[0].findNext('pre').contents
            words = getWordsList(raw)

            index = 0
            headerFileList = []
            formatStr = False
            numberOfFunctions = 0
            while 1:
                info = {}
                functionName = ''
                returnType = ''
                argument = ''
                arguments = []

                if '_GNU_SOURCE' in words[index:]:
                    info['use _GNU_SOURCE'] = True
                else:
                    info['use _GNU_SOURCE'] = False

                if url.endswith('p.html'):
                    info['POSIX api'] = True
                else:
                    info['POSIX api'] = False

                info['source'] = url

                if index == 0:
                    while index < len(words) and words[index] != '#include':
                        index += 1

                if index >= len(words):
                    break

                if words[index] == '#include':
                    headerFileList = []
                    index += 1
                    headerFileList.append(words[index].replace('<', '').replace('>', ''))
                    index += 1
                    if index < len(words) and words[index] == '#include':
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
                    if numberOfFunctions == 0:
                        errors[url] = 'No function could be found.'
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
                        if '(' in argument or ')' in argument:
                            functionName = ''
                            break

                if functionName == '':
                    if numberOfFunctions == 0:
                        errors[url] = 'No function could be found.'
                    break

                info['header file'] = headerFileList
                info['return value'] = returnType
                info['number of arguments'] = str(len(arguments))

                if len(arguments) == 1 and arguments[0] == 'void':
                    info['number of arguments'] = '0'
                if '...' in arguments:
                    info['number of arguments'] += ' or more'

                info['arguments'] = arguments
                if len(headerFileList) != 0 and returnType != '' and len(arguments) != 0:
                    if functionName not in result:
                        result[functionName] = [info]
                    else:
                        if not overlapVerification(result[functionName], info):
                            result[functionName].append(info)
                    numberOfFunctions += 1
                else:
                    if url not in errors.keys():
                        errors[url] = 'Some of the attribute could not be crawled.'

            # crawling description
            # * format string

            if len(soup.select('#DESCRIPTION')) != 0:
                raw = soup.select('#DESCRIPTION')[0].findNext('pre').contents
                words = getWordsList(raw)

                for i in range(0, len(words)):
                    if words[i] == 'format':
                        if words[i + 1] == 'string':
                            formatStr = True
                            break

            for functionName in result.keys():
                for i in range(0, len(result[functionName])):
                    result[functionName][i]['format string'] = formatStr

    return result


urls = getURLList('https://man7.org/linux/man-pages/dir_section_3.html')
# urls = ['https://man7.org/linux/man-pages/man3/fmaf.3.html']

print('crawling from the %dth to the %dth' % (start, end))
print('(' + urls[0] + ' ~ ' + urls[len(urls) - 1] + ')', end='\n\n')

libFunctionData = getFunctionAttr(urls)
pprint.pprint(libFunctionData)

print(list(libFunctionData.keys()))
print('total number of data that getFunctionAttr crawling: %d' % len(list(libFunctionData.keys())))

if len(errors) != 0:
    print('total number of data that getFunctionAttr cannot crawling: %d' % len(errors))
    pprint.pprint(errors)
else:
    print('there is no data that getFunctionAttr cannot crawling.')
