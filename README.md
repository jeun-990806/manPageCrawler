# manPageCrawler


crawling glibc function data from https://man7.org/linux/man-pages/

---
## 사용법
```shell
python3 main.py -s=[SECTION_NUMBER] -o=[OUTPUT_FILE_NAME]
```
 * -v: Verbose (해당 옵션을 추가하면 크롤링과 동시에 결과가 출력된다.)
 * -s: 크롤링할 문서들이 있는 섹션 번호. 기본값은 3이다.
 * -o: pickle로 출력할 파일의 이름. 기본값은 'output'이다.

---
## 기능 설명
 * Crawler.py: Crawler class 정의. Crawler class는 아래와 같은 동작을 한다.
   1. 섹션 페이지에 존재하는 문서들의 url을 전부 크롤링하여 url list에 저장한다.
   2. url list에 있는 모든 문서를 전부 크롤링하여 함수 정보를 읽고, 딕셔너리 형태로 저장한다.
   3. 함수 정보가 저장된 딕셔너리를 파일로 출력한다.
 * OptionReader.py: OptionReader class 정의. OptionReader class는 사용자가 입력한 옵션을 인식하여 반환한다.
 * fileManagement.py: Pickle API를 이용하여 dictionary file을 저장하는 함수가 정의되어 있다.