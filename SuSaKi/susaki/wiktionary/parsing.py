'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import re

from bs4 import BeautifulSoup


class Parser(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def parse_article(self, raw_article, word):
        """Parse the raw article and return a Article object 
        containing all information from the article"""
        raise NotImplementedError


class RestfulParser(Parser):

    def __init__(self, language):
        super().__init__(language)

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
            explanation = Translation(explanation_text)
            try:
                examples = element['examples']
                for example in examples:
                    explanation.add_example(self._clean_line(example))
            except KeyError:
                pass
            definition.add_translation(explanation)

        return definition

    def parse_article(self, raw_article, word):
        """ Parse the json object representing the article as 
        returned by a call to the restful API of Wiktionary"""
        definition_dict_list = self._extract_definitions(raw_article.json())
        if not definition_dict_list:
            raise IndexError(
                "{} does not exist as word in the target language".format(word))
        article = Article(word, self.language)
        for definition_dict in definition_dict_list:
            definition = self._parse_definition(definition_dict)
            article.add_definition(definition)

        return article


class HTMLParser(Parser):

    def parse_article(self, raw_article, word):
        return None


class Article:
    """
    The article holds all the information about a single word in a given language
    """

    def __init__(self, word, language):
        self.word = word
        self.language = language
        self.definitions = []

    def add_definition(self, definition):
        self.definitions.append(definition)


class Definition:
    """
    One definition of a word.
    """

    def __init__(self, pos):
        """
        pos: Part of speech (fx Noun, adjective)
        """
        self.pos = pos
        self.translations = []

    def add_translation(self, translation):
        self.translations.append(translation)


class Translation:
    """
    A single translation of a word.
    """

    def __init__(self, translation):
        self.translation = translation
        self.examples = []

    def add_example(self, example):
        self.examples.append(example)
