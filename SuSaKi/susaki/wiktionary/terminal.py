'''
Created on Apr 20, 2016

@author: simon
'''

import argparse
from collections import defaultdict
from requests.exceptions import HTTPError
import abc
import requests
import re

from bs4 import BeautifulSoup


class Article:

    def __init__(self, word, language):
        self.word = word
        self.language = language
        self.definitions = []

    def add_definition(self, definition):
        self.definitions.append(definition)


class Definition:

    def __init__(self, pos):
        self.pos = pos
        self.translations = []

    def add_translation(self, translation):
        self.translations.append(translation)


class Translation:

    def __init__(self, translation):
        self.translation = translation
        self.examples = []

    def add_example(self, example):
        self.examples.append(example)


class Connector(metaclass=abc.ABCMeta):

    def __init__(self, language):
        self.language = language

    @abc.abstractmethod
    def collect_raw_article(self, word):
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
            explanation = Translation(explanation_text)
            try:
                examples = element['examples']
                for example in examples:
                    explanation.add_example(self._clean_line(example))
            except KeyError:
                pass
            definition.add_translation(explanation)

        return definition

    def collect_raw_article(self, word):
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


class Wiktionary:

    def __init__(self, language):
        self.language = language
        self._setup_command_dict()
        self.connector = RestfulConnector(language)

    def _setup_command_dict(self):
        self.command_dict = defaultdict(lambda: self.process_user_query)
        self.command_dict['*exit'] = self._stop
        self.command_dict['*language'] = self.change_language
        self.command_dict['*help'] = self.greet_user

    def _stop(self, command):
        return False

    def change_language(self, command):
        new_language = input('Which language would you like to use?: >>')
        old_language = self.language
        self.connector = RestfulConnector(new_language)
        print('The language was changed from {} to {}'.format(
            old_language, self.connector.language))
        return True

    def print_information(self, article):
        print('Search term: {}'.format(article.word))
        print()
        for definition in article.definitions:
            print(definition.pos)
            for explanation in definition.translations:
                print("  " + explanation.translation)
            print()

    def process_user_query(self, word):
        try:
            article = self.connector.collect_raw_article(word)
        except HTTPError:
            print(
                '"{}" does not seem to have a page on Wiktionary'.format(word))
        except IndexError:
            print(
                '"{}" does not seem to exists as a word in the {}-en dictionary'.format(word, self.language))
        else:
            self.print_information(article)
        return True

    def greet_user(self, command):
        stop_word = [
            word for word in self.command_dict if self.command_dict[word] == self._stop]
        language_change_word = [
            word for word in self.command_dict if self.command_dict[word] == self.change_language]
        help_word = [
            word for word in self.command_dict if self.command_dict[word] == self.greet_user]

        print('*********************************************')
        print(
            'Welcome to SuSaKi - a simple tool to access the online user generated dictionary Wiktionary.')
        print(
            'You are currently accessing the en-{} dictionary.'.format(self.language))
        print(
            'To look up a word and its meaning in English just write it an press Enter.')
        print('To change the language used write "{}" and press Enter'.format(
            language_change_word[0]))
        print(
            'To exit this program write "{}" and press Enter'.format(stop_word[0]))
        print('To show this message again write "{}" and press Enter'.format(
            help_word[0]))
        print('*********************************************')
        return True

    def run(self):
        self.greet_user('')
        status = True
        while status:
            command = input('>> ')
            status = self.command_dict[command](command)
            print()

if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    parser.add_argument(
        "-l", "--language", help="The language you want translations from", default="fi")
    args = parser.parse_args()
    language = args.language
    wiktionary = Wiktionary(language)
    wiktionary.run()
