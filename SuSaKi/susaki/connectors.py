'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import requests
import re
from pprint import pprint

from bs4 import BeautifulSoup

from susaki.parsing import Article, Definition, Explanation
from requests.exceptions import HTTPError


class Connector(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def collect_article(self, word):
        """Access Wiktionary to collect the article for the given word."""


class RestfulConnector(Connector):
    '''
    Use this class to connect to Wiktionary through their RESTful API
    '''

    def __init__(self, language):
        super().__init__(language)

    def collect_page(self, word):
        url = 'https://en.wiktionary.org/api/rest_v1/page/definition/{}'.format(
            word)
        req = requests.get(url)
        req.raise_for_status()  # Test for bad response
        return req

    def extract_definitions(self, json_page):
        """Return a list of dictionaries each containing information about a 
        different definition of the given word"""
        try:
            definition_list = json_page[self.language]
        except KeyError:
            definition_list = None
        return definition_list

    def clean_line(self, line):
        # Apparently we have to soup twice before it recognizes the tags
        soup = BeautifulSoup(line, 'html.parser')
        soup = BeautifulSoup(soup.get_text(), 'html.parser')
        for tag in soup.findAll(True):
            tag.unwrap()
        text = soup.get_text()
        text = re.sub(r'  +', ' ', text)
        return text

    def parse_definition(self, definition_dict):
        pos = definition_dict['partOfSpeech']
        definition = Definition(pos)
        definition_elements = definition_dict['definitions']
        for element in definition_elements:
            explanation_text = self.clean_line(element['definition'])
            explanation = Explanation(explanation_text)
            try:
                examples = element['examples']
                for example in examples:
                    explanation.add_example(self.clean_line(example))
            except KeyError:
                pass
            definition.add_explanation(explanation)

        return definition

    def collect_article(self, word):
        try:
            req = self.collect_page(word)
        except HTTPError:
            article = None
            print(
                '"{}" does not seem to have a page on Wiktionary'.format(word))
        else:
            definition_dict_list = self.extract_definitions(req.json())
            if not definition_dict_list:
                article = None
                print(
                    '"{}" does not seem to exists as a word in the {}-en dictionary'.format(word, self.language))
            else:
                article = Article(word, self.language)
                for definition_dict in definition_dict_list:
                    definition = self.parse_definition(definition_dict)
                    article.add_definition(definition)
        return article
