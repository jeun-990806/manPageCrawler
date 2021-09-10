# manPageCrawler


crawling glibc function data from https://man7.org/linux/man-pages/

---
## 기능 설명
* headerFileScanner.py: 헤더파일에서 구조체 정보를 읽어 structure_list/에 저장한다.
* pageScanner.py
  * getURLsList(sectionURL): sectionURL 내에 존재하는 문서 url을 크롤링하여 반환한다.
  * getFunctionAttr(urlList): urlList에 존재하는 모든 페이지에서 다음의 정보를 크롤링하여 하나의 Dictionary로 반환한다.
    * function name (key value)
    * header file list
    * arguments
    * return type
    * posix api 여부
    * _GNU_SOURCE 이용 여부
* textAnalyzer.py: nltk를 사용하여 텍스트 내에 특정 단어가 존재하는지 검색한다.
* tools.py: 테스트 시의 편의를 위한 함수들. (실질적 기능과는 관련 없음)