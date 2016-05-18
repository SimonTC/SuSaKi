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
    def parse_article(self, raw_articles, word):
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

    def parse_article(self, raw_articles, word):
        """ Parse the json object representing the article as 
        returned by a call to the restful API of Wiktionary"""
        definition_dict_list = self._extract_definitions(raw_articles.json())
        if not definition_dict_list:
            raise IndexError(
                "{} does not exist as word in the target language".format(word))
        article = Article(word, self.language)
        for definition_dict in definition_dict_list:
            definition = self._parse_definition(definition_dict)
            article.add_definition(definition)

        return article


class HTMLParser(Parser):

    possible_word_classes = r'Verb|Noun|Adjective|Numeral|Pronoun|Adverb|Suffix'

    def __init__(self, language):
        super().__init__(language)
        self.dictionary = {'language': language}

    def _extract_soup_between(self, from_tag, to_tag, soup):
        """
        Extract all tags between the from and to tags in the given soup.
        If to_tag doesn't exist, all text from the from_tag to the end of the page is returned.
        """
        start_extracting = False
        text = str(soup)
        text_array = text.split('\n')
        text_to_extract = ''
        from_tag_text = str(from_tag)
        if to_tag:
            no_to_tag = False
            to_tag_text = str(to_tag)
        else:
            no_to_tag = True
        for line in text_array:
            if from_tag_text in line:
                start_extracting = True
            elif not no_to_tag:
                if to_tag_text in line:
                    break
            if start_extracting:
                text_to_extract += line + '\n'

        soup = BeautifulSoup(text_to_extract, 'html.parser')
        return soup

    def _extract_language_part_border(self, language_tags, target_language):
        has_seen_target_language = False
        for tag in language_tags:
            if has_seen_target_language:
                return tag
            elif tag.find_all('span', id=target_language):
                has_seen_target_language = True
        return None

    def _extract_correct_language_part(self, raw_articles):
        """
        raw_articles: beatiful soup object containing the main content of the raw article
        """
        target_language = self.language
        from_tag = raw_articles.find_all('span', id=target_language)[0]
        to_tag = self._extract_language_part_border(
            raw_articles.find_all('h2'), target_language)
        soup = self._extract_soup_between(from_tag, to_tag, raw_articles)
        return soup

    def _extract_pronounciation(self, article):
        raise NotImplementedError

    def _extract_parts(self, parent_soup, tag_name, primary_id_expression, secondary_id_expression):
        """
        Extract parts from the given soup. 
        parent_soup: soup from which parts are extracted.
        tag_name: name of the tag that is deliminating the parts to be extracted.
        primary_id_expression: regex expression to find the correct tags.
        secondary_id_expression: regex expression to use if nothing is found with the primary expression.
        """
        part_boundaries = parent_soup.find_all(
            tag_name, id=re.compile(primary_id_expression))
        if not part_boundaries:
            # This article does not used etymologies. Might happen when the
            # word in question is a conjugation
            part_boundaries = parent_soup.find_all(
                tag_name, id=re.compile(secondary_id_expression))  # If no etymology is given, the next heading will contain the word class
        parts = []
        for i, boundary in enumerate(part_boundaries):
            try:
                part = self._extract_soup_between(
                    boundary, part_boundaries[i + 1], parent_soup)
            except IndexError:
                part = self._extract_soup_between(
                    boundary, None, parent_soup)
            parts.append(part)
        return parts

    def _parse_POS(self, pos_part):
        pos_dict = {}
        # Extract translations + examples
        # The list of translations should always be the first list in the POS
        # part
        translation_list = pos_part.find_all('ol')[0]
        # Each list item contains a translation together with eventual examples
        translations = translation_list.find_all('li')
        translation_dict = {}
        for i, translation in enumerate(translations):
            only_translation = self._extract_soup_between(
                '<li>', '<dl>', translation)
            translation_text = only_translation.get_text()
            translation_text = translation_text.replace('\n', '')
            translation_dict[
                'translation {}'.format(i)] = translation_text
            examples = translation.find_all('dl')
        pos_dict['translations'] = translation_dict

        # Extract declension

        # Extract usage notes

        # Extract synonyms

        # Extract related terms

        # Extract Derived terms

        # Extract compunds
        return pos_dict

    def _extract_article_text(self, raw_article):
        """
        raw_articles: soup of the whole article age
        """
        content = raw_article.body.find('div', id='content')
        body_content = content.find('div', id='bodyContent')
        body_text_content = body_content.find('div', id='mw-content-text')
        return body_text_content

    def parse_article(self, raw_article, word):
        """
        raw_articles: requests object returned by a call to requests.get()
        word: the word this article is about
        """
        article_dict = self.dictionary
        soup = BeautifulSoup(raw_article.content, 'html.parser')
        text_content = self._extract_article_text(soup)
        language_part = self._extract_correct_language_part(text_content)
        etymology_parts = self._extract_parts(
            language_part, 'span', 'Etymology', self.possible_word_classes)
        for i, etymology in enumerate(etymology_parts):
            etymology_dict = {}
            POS_parts = self._extract_parts(
                etymology, 'span', self.possible_word_classes, None)
            for j, pos_part in enumerate(POS_parts):
                pos_dict = self._parse_POS(pos_part)
                etymology_dict['pos {}'.format(j)] = pos_dict
            article_dict['etymology {}'.format(i)] = etymology_dict

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


def print_translations(article_dict):
    for key, etymology_dict in article_dict.items():
        if 'etymology' in key:
            for _, pos in etymology_dict.items():
                for _, translation in pos['translations'].items():
                    print(translation)

if __name__ == '__main__':
    word = 'lähettää'
    url = 'https://en.wiktionary.org/wiki/{}'.format(word)
    parser = HTMLParser('Finnish')
    req = requests.get(url)
    article_dict = parser.parse_article(req, word)
    print_translations(article_dict)
