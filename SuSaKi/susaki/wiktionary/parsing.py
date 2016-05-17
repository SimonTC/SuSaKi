'''
Created on Apr 21, 2016

@author: simon
'''
import abc
import re

import requests

import logging

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)


class Parser(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def parse_article(self, raw_article, word):
        """Parse the raw article and return a dictionary object 
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

    def __init__(self, language):
        super().__init__(language)
        self.dictionary = {'language': language}

    def _extract_text_until(self, from_tag, to_tag, soup):
        """
        Extract all tags between the from and to tags in the given soup.
        """
        start_extracting = False
        text = str(soup)
        text_array = text.split('\n')
        text_to_extract = ''
        from_tag_text = str(from_tag)
        to_tag_text = str(to_tag)
        for line in text_array:
            if from_tag_text in line:
                start_extracting = True
            elif to_tag_text in line:
                soup = BeautifulSoup(text_to_extract, 'html.parser')
                logging.debug(soup.prettify())
                return text_to_extract
            if start_extracting:
                text_to_extract += line + '\n'

    def _extract_language_part_border(self, language_tags, target_language):
        has_seen_target_language = False
        for tag in language_tags:
            if has_seen_target_language:
                return tag
            elif tag.find_all('span', id=target_language):
                has_seen_target_language = True
        return None

    def _extract_correct_language_part(self, raw_article):
        """
        raw_article: beatiful soup object containing the main content of the raw article
        """
        target_language = self.language
        from_tag = raw_article.find_all('span', id=target_language)[0]
        to_tag = self._extract_language_part_border(
            raw_article.find_all('h2'), target_language)
        text = self._extract_text_until(from_tag, to_tag, raw_article)
        soup = BeautifulSoup(text, 'html.parser')

        return soup

    def _extract_etymologies(self, article):
        raise NotImplementedError

    def _extract_POS_parts(self, etymology):
        raise NotImplementedError

    def _parse_POS(self, pos):
        raise NotImplementedError

    def _extract_article_text(self, raw_article):
        """
        raw_article: soup of the whole article age
        """
        content = raw_article.body.find('div', id='content')
        body_content = content.find('div', id='bodyContent')
        body_text_content = body_content.find('div', id='mw-content-text')
        return body_text_content

    def parse_article(self, raw_article, word):
        """
        raw_article: requests object returned by a call to requests.get()
        word: the word this article is about
        """
        soup = BeautifulSoup(raw_article.content, 'html.parser')
        text_content = self._extract_article_text(soup)
        language_part = self._extract_correct_language_part(text_content)

        return self.dictionary


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

if __name__ == '__main__':
    url = 'https://en.wiktionary.org/wiki/kuu'
    parser = HTMLParser('Finnish')
    req = requests.get(url)
    parser.parse_article(req, 'kuu')
