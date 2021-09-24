import Cralwer
import OptionReader
import sys

reader = OptionReader.OptionReader(sys.argv[1:])
crawler = Cralwer.Crawler(*reader.applyAllOptions())

crawler.crawling()
crawler.export()