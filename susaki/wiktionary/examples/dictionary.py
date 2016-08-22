import argparse
from collections import defaultdict
from susaki.wiktionary.connectors import HTMLConnector, APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing
import re
from examplelogging import setup_logging


class Wiktionary:

    def __init__(self, language, debugging=False):
        self.language = language
        self._setup_command_dict()
        self.api_connector = APIConnector()
        self.html_connector = HTMLConnector(language)
        self.logger = setup_logging(debugging)
        self.logger.info('Initialized Wiktionary class')

    def _setup_command_dict(self):
        self.command_dict = defaultdict(lambda: self.process_user_query)
        self.command_dict['*exit'] = self._stop
        self.command_dict['*language'] = self.change_language
        self.command_dict['*help'] = self.greet_user

    def _stop(self, command):
        return False

    def change_language(self, command):
        # print('Language change is currently not implemented')
        print('WARNING: This tool has not been tested with other source languages '
              'than Finnish. It should work, but you might get weird results.')
        new_language = input('Which source language would you like to use?: >> ')
        old_language = self.language
        self.language = new_language
        print('The source language was changed from {} to {}'.format(
            old_language, self.language))
        self.logger.info('Changedlanguage from {} to {}'.format(old_language, new_language))
        return True

    def print_information(self, article_root):
        language_part = article_root.find('Languages').find(self.language)
        pos_parts = language_part.find('POS-parts')
        for pos in pos_parts:
            print('\n   {}'.format(pos.tag))
            translations = pos.find('Translations')
            for translation in translations:
                print('')
                text = translation.find('Text')
                print('      - ' + text.text)
                examples = translation.find('Examples')
                try:
                    for example in examples:
                        print('        * ' + example.find('Text').text)
                        try:
                            print('          ' + example.find('Translation').text)
                        except AttributeError:
                            pass
                except TypeError:
                    pass

    def process_user_query(self, word):
        self.logger.info('Processing user query: {}'.format(word))
        if re.match('^ *$', word):
            return True
        word = word.strip()
        word = word.lower()
        try:
            raw_article = self.api_connector.collect_raw_article(word)
            self.logger.info('Found raw article using the API')
        except LookupError:
            self.logger.debug('Lookup error while getting article from api')
            try:
                req = self.html_connector.collect_raw_article(word)
                if type(req) is list:
                    self.logger.info('No article found but suggestions exist')
                    print(
                        '"{}" does not have its own article, however it does exist in the articles for the following words:'.format(word))
                    for suggestion in req:
                        print(''.join(['  ', suggestion]))
                    return True
                else:
                    self.logger.info('No articles exists containing "{}"'.format(word))
                    raise LookupError(
                        'The word "{}" does not exist on Wiktionary'.format(word))

            except LookupError as error:
                if 'does not exist on Wiktionary' in str(error):
                    self.logger.info('No article exist for {}'.format(word))
                    print(str(error).replace("'", ""))
                    return True
                else:
                    raise
        try:
            article = article_parsing.parse_article(
                raw_article, word, self.language, parse_tables=False)
            self.logger.info('Parsing of article succeeded')
        except LookupError as err:
            if 'No explanations exists for the language:' in str(err):
                message = '"{}" does not exist as a word in the {} - English dictionary'.format(word, self.language)
                self.logger.info(message)
                print(message)
                return True
            else:
                raise
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
            try:
                status = self.command_dict[command](command)
            except Exception:
                self.logger.error(
                    'Failed to process the following command: "{}"'.format(command),
                    exc_info=True)
                print('An error occured while processing the command "{}"'.format(command))
            else:
                print()


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    parser.add_argument(
        "-l", "--language", help="The language you want translations from", default="Finnish")
    parser.add_argument(
        "-d", "--debug", help="Set to True if you want debug output", default=False
    )
    args = parser.parse_args()
    language = args.language
    wiktionary = Wiktionary(language, args.debug)
    wiktionary.run()
