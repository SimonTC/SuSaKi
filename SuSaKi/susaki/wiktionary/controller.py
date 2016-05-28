'''
Created on Apr 20, 2016

@author: simon
'''

import argparse
from collections import defaultdict
from susaki.wiktionary.connectors import HTMLConnector
from susaki.wiktionary.parsing import HTMLParser


class Wiktionary:

    def __init__(self, language):
        self.language = language
        self._setup_command_dict()
        self.connector = HTMLConnector(language)
        self.parser = HTMLParser()

    def _setup_command_dict(self):
        self.command_dict = defaultdict(lambda: self.process_user_query)
        self.command_dict['*exit'] = self._stop
        self.command_dict['*language'] = self.change_language
        self.command_dict['*help'] = self.greet_user

    def _stop(self, command):
        return False

    def change_language(self, command):
        print('Language change is currently not implemented')
#         new_language = input('Which language would you like to use?: >>')
#         old_language = self.language
#         self.connector = RestfulConnector(new_language)
#         print('The language was changed from {} to {}'.format(
#             old_language, self.connector.language))
        return True

    def print_information(self, article):
        print('Search term: {}'.format(article['word']))
        print()
        for etymology in article[self.language]['etymologies']:
            for _, pos in etymology['parts-of-speech'].items():
                print('{}'.format(pos['pos']))
                for translation_tuple in pos['translations']:
                    print('  ' + translation_tuple.translation)
                print()

    def process_user_query(self, word):
        try:
            raw_article = self.connector.collect_raw_article(word)
            if type(raw_article) is list:
                print(
                    '{} does not have its own article, however it does exist in the articles for the following words:'.format(word))
                for suggestion in raw_article:
                    print(''.join(['  ', suggestion]))
            else:
                article = self.parser.parse_article(
                    raw_article.content, word, self.language)
                self.print_information(article)
        except KeyError as error:
            if 'No explanations exists for the language:' in str(error):
                print(
                    '"{}" does not seem to exists as a word in the {}-en dictionary'.format(word, self.language))
            elif 'does not exist on Wiktionary' in str(error):
                print(str(error).replace("'", ""))
            else:
                raise
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
        "-l", "--language", help="The language you want translations from", default="Finnish")
    args = parser.parse_args()
    language = args.language
    wiktionary = Wiktionary(language)
    wiktionary.run()
