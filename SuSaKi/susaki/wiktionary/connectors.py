'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import requests
import re

from bs4 import BeautifulSoup

from susaki.wiktionary.parsing import Article, Definition, Explanation
from requests.exceptions import HTTPError


class Connector(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def collect_article(self, word):
        """Access Wiktionary to collect the article for the given word.
           Returns a HTTPError if the page doesn't exists.
           Returns a LookupError if the page does exists but no definitions exists for the given word
           in the target language """


class RestfulConnector(Connector):
    '''
    Use this class to connect to Wiktionary through their RESTful API
    '''

    def __init__(self, language):
        super().__init__(language)

    def _collect_page(self, word):
        """Collects the article page for the given word using the wiktionary RESTful API"""
        url = 'https://en.wiktionary.org/api/rest_v1/page/definition/{}'.format(
            word)
        req = requests.get(url)
        return req

    def _extract_definitions(self, json_page):
        """Return a list of dictionaries each containing information about a 
        different definition of the given word"""
        try:
            definition_list = json_page[self.language]
        except KeyError:
            definition_list = None
        return definition_list

    def _clean_line(self, line):
        """Remove all html tags from the line"""
        # Apparently we have to soup twice before it recognizes the tags
        soup = BeautifulSoup(line, 'html.parser')
        soup = BeautifulSoup(soup.get_text(), 'html.parser')
        for tag in soup.findAll(True):
            tag.unwrap()
        text = soup.get_text()
        text = re.sub(r'  +', ' ', text)
        return text

    def _parse_definition(self, definition_dict):
        """Parse the definition using the given definition dictionary"""
        pos = definition_dict['partOfSpeech']
        definition = Definition(pos)
        definition_elements = definition_dict['definitions']
        for element in definition_elements:
            explanation_text = self._clean_line(element['definition'])
            explanation = Explanation(explanation_text)
            try:
                examples = element['examples']
                for example in examples:
                    explanation.add_example(self._clean_line(example))
            except KeyError:
                pass
            definition.add_explanation(explanation)

        return definition

    def collect_article(self, word):
        req = self._collect_page(word)
        # Test for bad response. Raises HTTPError if page doesn't exist
        req.raise_for_status()
        definition_dict_list = self._extract_definitions(req.json())
        if not definition_dict_list:
            raise IndexError(
                "{} does not exist as word in the target language".format(word))
        article = Article(word, self.language)
        for definition_dict in definition_dict_list:
            definition = self._parse_definition(definition_dict)
            article.add_definition(definition)

        return article


class RawConnector(Connector):

    def __init__(self, language):
        super().__init__(language)

    def _collect_page(self, word):
        """Collects the raw article page for the given word"""
        url = 'https://en.wiktionary.org/w/index.php?title={}&action=raw'.format(
            word)
        req = requests.get(url)
        return req

    def _extract_language_part(self, page):
        language_part = re.findall('==Finnish==', page)

    def _extract_definitions(self, json_page):
        """Return a list of dictionaries each containing information about a 
        different definition of the given word"""
        try:
            definition_list = json_page[self.language]
        except KeyError:
            definition_list = None
        return definition_list

    def _clean_line(self, line):
        """Remove all html tags from the line"""
        # Apparently we have to soup twice before it recognizes the tags
        soup = BeautifulSoup(line, 'html.parser')
        soup = BeautifulSoup(soup.get_text(), 'html.parser')
        for tag in soup.findAll(True):
            tag.unwrap()
        text = soup.get_text()
        text = re.sub(r'  +', ' ', text)
        return text

    def _parse_definition(self, definition_dict):
        """Parse the definition using the given definition dictionary"""
        pos = definition_dict['partOfSpeech']
        definition = Definition(pos)
        definition_elements = definition_dict['definitions']
        for element in definition_elements:
            explanation_text = self._clean_line(element['definition'])
            explanation = Explanation(explanation_text)
            try:
                examples = element['examples']
                for example in examples:
                    explanation.add_example(self._clean_line(example))
            except KeyError:
                pass
            definition.add_explanation(explanation)

        return definition

    def collect_article(self, word):
        req = self._collect_page(word)
        # Test for bad response. Raises HTTPError if page doesn't exist
        req.raise_for_status()
        definition_dict_list = self._extract_definitions(req.json())
        if not definition_dict_list:
            raise IndexError(
                "{} does not exist as word in the target language".format(word))
        article = Article(word, self.language)
        for definition_dict in definition_dict_list:
            definition = self._parse_definition(definition_dict)
            article.add_definition(definition)

        return article
