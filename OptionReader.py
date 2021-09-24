class OptionReader:
    __s = 3
    __v = False
    __o = 'output'

    def __init__(self, optionList):
        self.__readOption(optionList)
        print('Setting:\tsection number = %s' % self.__s)
        print('\t\tverbose =', self.__v)
        print('\t\toutput file name = %s' % self.__o)

    def __readOption(self, optionList):
        for opt in optionList:
            if opt.startswith('-v'):
                self.__v = True
            elif opt.startswith('-o'):
                self.__o = opt[opt.find('=') + 1:]
            elif opt.startswith('-s'):
                self.__s = opt[opt.find('=') + 1:]

    def applyAllOptions(self):
        return [self.__o, self.__s, self.__v]
