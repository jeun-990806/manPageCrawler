import pprint

import fileManagement as fm
import documentScanner as ds

'''
libFunctionData = fm.open_data('glibc.dict')
useFlags = {}
useModes = {}
useTypes = {}

for name in libFunctionData.keys():
    for i in range(0, len(libFunctionData[name])):
        for j in range(0, len(libFunctionData[name][i]['arguments'])):
            if 'flag' in libFunctionData[name][i]['arguments'][j]:
                useFlags[name] = libFunctionData[name][i]['url']
            if 'mode' in libFunctionData[name][i]['arguments'][j]:
                useModes[name] = libFunctionData[name][i]['url']
            if 'type' in libFunctionData[name][i]['arguments'][j]:
                useTypes[name] = libFunctionData[name][i]['url']
'''