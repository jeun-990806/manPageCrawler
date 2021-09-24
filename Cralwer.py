from bs4 import BeautifulSoup
import requests
import re
import fileManagement
import pprint


class Crawler:
    functionInfo = {}
    errorCase = []

    def __init__(self, o, s='3', v=False):
        self.__outputFileName = o
        self.__sectionNumber = s
        self.__verbose = v

    def __getURLList(self):
        response = requests.get('https://man7.org/linux/man-pages/dir_section_%s.html' % self.__sectionNumber)
        if response.status_code == 200:
            bs = BeautifulSoup(response.text, 'html.parser')
            result = ['https://man7.org/linux/man-pages' + link['href'][1:] for link in bs.select('td a')]
            return result

    def __toText(self, b):
        raw = []
        text = ''
        for paragraphName in ['SYNOPSIS', 'C_SYNOPSIS', 'SYNOPSIS_AND_DESCRIPTION']:
            if len(b.select('#' + paragraphName)) != 0:
                raw = b.select('#' + paragraphName)[0].findNext('pre').contents
                break
        if len(raw) == 0:
            return ''

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

        text = re.sub(r'[\s][\s]+', ' ', text)
        return text

    def __getFunctionName(self, function):
        RE_FunctionName = r'(?!^)(?:\s|\*)([a-zA-Z0-9_]+|\([a-zA-Z0-9_*\s]+\))\s?\([a-zA-Z0-9_,*()\s]*\)$'
        #                                  ----------------------------------> capture
        regexResult = re.findall(RE_FunctionName, function)
        if len(regexResult) != 0:
            return regexResult[0]
        return None

    def __getHeaderFileList(self, text):
        RE_Header = r'#include\s?<([a-zA-Z0-9_/]+\.h)>'
        return re.findall(RE_Header, text)

    def __getArgumentList(self, function):
        RE_Argument = r'\s?(void|[a-zA-Z0-9_*\s]+|[a-zA-Z0-9_()*\s]*\([a-zA-Z0-9_*,\s]+\))(?:,|\)$)'
        return re.findall(RE_Argument, function)

    def __getReturnType(self, function):
        RE_ReturnType = r'^(?:[\s]+|)([a-zA-Z0-9_*\s]+(?:\s|\*))'
        regexResult = re.findall(RE_ReturnType, function)
        if len(regexResult) != 0:
            return regexResult[0].strip()
        return None

    def __checkPosixAPI(self, url):
        if url.endswith('p.html'):
            return True
        return False

    def __checkGNUSource(self, text):
        RE_GNU_Source = r'#define\s?_GNU_SOURCE'
        if len(re.findall(RE_GNU_Source, text)) != 0:
            return True
        return False

    def crawling(self):
        RE_Function = r'[a-zA-Z0-9_*\s]+\([a-zA-Z0-9_,*()\s]*\)'
        targetDocuments = self.__getURLList()

        for doc in targetDocuments:
            response = requests.get(doc)
            if response.status_code == 200:
                bs = BeautifulSoup(response.text, 'html.parser')
                text = self.__toText(bs)
                for function in re.findall(RE_Function, text):
                    functionName = self.__getFunctionName(function)
                    arguments = self.__getArgumentList(function)
                    returnType = self.__getReturnType(function)
                    headerFiles = self.__getHeaderFileList(text)
                    posixAPI = self.__checkPosixAPI(doc)
                    useGNUSource = self.__checkGNUSource(text)
                    if functionName is not None and returnType is not None and len(arguments) > 0 and len(headerFiles) > 0:
                        self.functionInfo[functionName] = {'header files': headerFiles,
                                                           'arguments': arguments,
                                                           'return type': returnType,
                                                           'posix API': posixAPI,
                                                           'use _GNU_SOURCE': useGNUSource}
                        if self.__verbose:
                            print('\n' + functionName)
                            pprint.pprint(self.functionInfo[functionName])
                    else:
                        self.errorCase.append(function)
                        if self.__verbose:
                            print(function + ' -> this text is be matched with regular expression, '
                                             'but It is not a complete form of function.')
                            print('(' + doc + ')')
        print('Total number of crawled functions: %d' % len(self.functionInfo.keys()))
        print('Total number of functions that cannot be crawled: %d' % len(self.errorCase))

    def export(self):
        fileManagement.saveData(self.functionInfo, self.__outputFileName)