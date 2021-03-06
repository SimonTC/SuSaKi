'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import requests
from bs4 import BeautifulSoup
import logging
logger = logging.getLogger(__name__)


class Connector(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def collect_raw_article(self, word):
        """Access Wiktionary to collect the article for the given word.
           Returns a HTTPError if the page doesn't exists.
           Returns a LookupError if the page does exists but no definitions exists for the given word
           in the target language """
        raise NotImplementedError


class APIConnector:

    def __init__(self):
        logger.debug('Initializing APIConnector')

    def collect_raw_article(self, word):
        logger.debug('Collecting the raw article for "{}" using the API'.format(word))
        url = 'https://en.wiktionary.org/w/api.php?format=xml&action=query&prop=revisions&titles={}&rvprop=content&rvparse&redirects=true'.format(word)
        req = requests.get(url)
        soup = BeautifulSoup(req.content, 'lxml')
        content = soup.find('rev', {'xml:space': 'preserve'})
        try:
            content_text = content.text
        except AttributeError:
            raise LookupError("Article can't be accessed by API")
        logger.debug('Article found')
        return content_text


class HTMLConnector(Connector):

    def __init__(self, language, server_location='https://'):
        logger.debug('Initializing HTMLConnector')
        super().__init__(language)
        self.server_location = server_location

    def _collect_page(self, word):
        """Collects the html page for the given word"""
        url = '{}en.wiktionary.org/wiki/Special:Search?search={}&go=Try+exact+match'.format(
            self.server_location, word)
        req = requests.get(url)
        return req

    def collect_raw_article(self, word):
        """
        Will return the HTML page if an article for the given word exists.
        If no page exists, but the word does exist in other articles a list of the names of these articles is returned.
        If The word doesn't exist on Wiktionary a KeyError excpetion is raised
        """
        logger.debug('Collecting the raw article for {} using the HTML connector'.format(word))
        # Collect html page
        req = self._collect_page(word)
        soup = BeautifulSoup(req.content, 'html.parser')
        content = soup.body.find('div', id='content')
        heading = content.find('h1', id='firstHeading')
        article_content = content.find('div', id='mw-content-text')

        if heading.string == 'Search results':
            logger.debug("Article doesn't exist")
            # Check to see if they have any recommendations
            search_results = article_content.select(
                '[class~=searchresults]')[0]
            if search_results.select('[class~=mw-search-nonefound]'):
                raise LookupError(
                    'The word "{}" does not exist on Wiktionary'.format(word))
            else:
                logger.debug('Suggestions found')
                suggestions = search_results.find(
                    'ul', attrs={'class': 'mw-search-results'})
                suggested_words = []
                for li in suggestions.find_all('li'):
                    suggestion = li.div.a.text
                    suggested_words.append(suggestion)
                return suggested_words
        else:
            # Page exists
            logger.debug('Article found')
            return req


if __name__ == '__main__':
    # collector = HTMLConnector('fi')
    # collector = APIConnector()
    collector = HTMLConnector('fi', 'http://localhost:8080/')
    word = 'säälle'
#     word = 'hkjhk'
    text = collector.collect_raw_article(word)
    print(text.text)
