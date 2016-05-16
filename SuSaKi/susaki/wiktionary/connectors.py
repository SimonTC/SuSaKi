'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import requests
import re

from bs4 import BeautifulSoup

from susaki.wiktionary.parsing import Article, Definition, Translation
from requests.exceptions import HTTPError


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


class RestfulConnector(Connector):
    '''
    Use this class to connect to Wiktionary through their RESTful API
    '''

    def __init__(self, language):
        super().__init__(language)

    def collect_raw_article(self, word):
        """Collects the article page for the given word using the wiktionary RESTful API"""
        url = 'https://en.wiktionary.org/api/rest_v1/page/definition/{}'.format(
            word)
        req = requests.get(url)
        # Test for bad response. Raises HTTPError if page doesn't exist
        req.raise_for_status()
        return req


class HTMLConnector(Connector):

    def __init__(self, language):
        super().__init__(language)

    def _collect_page(self, word):
        """Collects the html page for the given word"""
        url = 'https://en.wiktionary.org/wiki/Special:Search?search={}&go=Try+exact+match'.format(
            word)
#         url = 'https://en.wiktionary.org/wiki/{}'.format(
#             word)
        req = requests.get(url)
        return req

    def collect_raw_article(self, word):
        # Collect html page
        req = self._collect_page(word)
        soup = BeautifulSoup(req.content, 'html.parser')
        content = soup.body.find('div', id='content')
        heading = content.find('h1', id='firstHeading')
        article_content = content.find('div', id='mw-content-text')

        if heading.string == 'Search results':
            # Check to see if they have any recommendations
            search_results = article_content.select(
                '[class~=searchresults]')[0]
            if search_results.select('[class~=mw-search-nonefound]'):
                print('I have no idea what you are looking for')
            else:
                suggestions = search_results.select(
                    '[class~=mw-search-results]')[0]
                suggested_words = []
                for li in suggestions.find_all('li'):
                    suggestion = li.select(
                        '[class~=mw-search-result-heading]')[0]
                    suggested_words.append(suggestion.next_element.string)
                print('"{}" does not have its own page, but you can check these pages:'.format(
                    word))
                print(', '.join(suggested_words))
        else:
            # Page exists
            print("Yay! We have a page about {}".format(word))

if __name__ == '__main__':
    collector = HTMLConnector('fi')
    word = 'sää'
#     word = 'hkjhk'
    collector.collect_raw_article(word)
