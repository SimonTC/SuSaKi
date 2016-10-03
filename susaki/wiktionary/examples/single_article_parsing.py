from susaki.wiktionary.wiki_parsing.article_parsing import parse_article
from examplelogging import setup_logging
import requests
from lxml import etree

from bs4 import BeautifulSoup
logger = setup_logging(debugging=True)
word = 'koti'

url = 'http://localhost:8080/en.wiktionary.org/wiki/{}'.format(word)
raw_article = requests.get(url)
soup = BeautifulSoup(raw_article.text, 'lxml')
content = soup.body.find('div', id='content')
article_content = content.find('div', id='mw-content-text')
xml = parse_article(str(article_content), word)

s = etree.tostring(xml, pretty_print=True, encoding='unicode')
print(s)
