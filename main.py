import pprint

import fileManagement as fm
import documentScanner as ds


libFunctionData = fm.open_data('glibc.dict')
useFlags = {}
useModes = {}
useTypes = {}

for name in libFunctionData.keys():
    for i in range(0, len(libFunctionData[name])):
        for j in range(0, len(libFunctionData[name][i]['arguments'])):
            if 'flag' in libFunctionData[name][i]['arguments'][j]:
                useFlags[name] = libFunctionData[name]
            if 'mode' in libFunctionData[name][i]['arguments'][j]:
                useModes[name] = libFunctionData[name]
            if 'type' in libFunctionData[name][i]['arguments'][j]:
                useTypes[name] = libFunctionData[name]

print('use flag argument(%d)' % len(useFlags.keys()))
print(list(useFlags.keys()), end='\n\n')
print('use mode argument(%d)' % len(useModes.keys()))
print(list(useModes.keys()), end='\n\n')
print('use type argument(%d)' % len(useTypes.keys()))
print(list(useTypes.keys()), end='\n\n')
