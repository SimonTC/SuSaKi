'''
Created on Apr 20, 2016

@author: simon
'''

import requests
import re
from bs4 import BeautifulSoup
import argparse
from requests.exceptions import HTTPError
from collections import defaultdict


class Wiktionary:

    def __init__(self, language):
        self.language = language
        self._setup_command_dict()

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
        self.language = new_language
        print('The language was changed from {} to {}'.format(
            old_language, self.language))
        return True

    def collect_page(self, word):
        url = 'https://en.wiktionary.org/api/rest_v1/page/definition/{}'.format(
            word)
        req = requests.get(url)
        req.raise_for_status()  # Test for bad response
        return req

    def extract_etymologies(self, json_page):
        try:
            etymology_list = json_page[self.language]
        except:
            etymology_list = None
        return etymology_list

    def clean_line(self, line):
        # Apparently we have to soup twice before it recognizes the tags
        soup = BeautifulSoup(line, 'html.parser')
        soup = BeautifulSoup(soup.get_text(), 'html.parser')
        for tag in soup.findAll(True):
            tag.unwrap()
        text = soup.get_text()
        text = re.sub(r'  +', ' ', text)
        return text

    def print_etymology_information(self, etymology_dict):
        print(etymology_dict['partOfSpeech'])
        definitions = etymology_dict['definitions']
        for definition in definitions:
            print(' ' + self.clean_line(definition['definition']))

        print()

    def print_information(self, word, etymology_list):
        print('Search term: {}'.format(word))
        print()
        for etymology in etymology_list:
            self.print_etymology_information(etymology)

    def process_user_query(self, word):
        try:
            req = self.collect_page(word)
        except HTTPError:
            print(
                '"{}" does not seem to have a page on Wiktionary'.format(word))
        else:
            etymology_list = self.extract_etymologies(req.json())
            if not etymology_list:
                print(
                    '"{}" does not seem to exists as a word in the {}-en dictionary'.format(word, self.language))
            else:
                self.print_information(word, etymology_list)
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
