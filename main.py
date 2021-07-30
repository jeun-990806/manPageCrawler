import pprint

import fileManagement as fm
import documentScanner as ds
import nltk

urls = fm.openData('crawled/section0-searchResult.list')
result, = ds.getSymbolicConstants(urls)
pprint.pprint(result)