import requests
from bs4 import BeautifulSoup

url = 'https://man7.org/linux/man-pages/man3/printf.3.html'
response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    texts = soup.select('pre')
    for text in texts:
        print(text.get_text())