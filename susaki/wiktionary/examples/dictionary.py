import argparse
from collections import defaultdict
from susaki.wiktionary.connectors import HTMLConnector, APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing
import re
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Wiktionary:

    def __init__(self, language):
        self.language = language
        self._setup_command_dict()
        self.api_connector = APIConnector()
        self.html_connector = HTMLConnector(language)

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
        logger.info('Changedlanguage from {} to {}'.format(old_language, new_language))
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
        logger.info('Processing user querry: {}'.format(word))
        if re.match('^ *$', word):
            return True
        word = word.strip()
        word = word.lower()
        try:
            raw_article = self.api_connector.collect_raw_article(word)
            logger.info('Found raw article using the API')
        except LookupError:
            logger.debug('Lookup error while getting article from api')
            try:
                req = self.html_connector.collect_raw_article(word)
                if type(req) is list:
                    logger.info('No article found but suggestions exist')
                    print(
                        '"{}" does not have its own article, however it does exist in the articles for the following words:'.format(word))
                    for suggestion in req:
                        print(''.join(['  ', suggestion]))
                    return True
                else:
                    logger.info('No articles exists containing "{}"'.format(word))
                    raise LookupError(
                        'The word "{}" does not exist on Wiktionary'.format(word))

            except LookupError as error:
                if 'does not exist on Wiktionary' in str(error):
                    logger.info('No article exist for {}'.format(word))
                    print(str(error).replace("'", ""))
                    return True
                else:
                    raise
        try:
            article = article_parsing.parse_article(
                raw_article, word, self.language, parse_tables=False)
            logger.info('Parsing of article succeeded')
        except LookupError as err:
            if 'No explanations exists for the language:' in str(err):
                message = '"{}" does not exist as a word in the {} - English dictionary'.format(word, self.language)
                logger.info(message)
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
            except Exception as e:
                report_exception(e, command)
                raise
            else:
                print()


def report_exception(exception, command):
    """ Dirty reporting of exceptions. Should be handled in the logger module"""
    root_dir = os.path.normpath(os.path.join(__file__, '..', '..', '..', '..'))
    crash_dir = '/'.join([root_dir, 'logs', 'crash'])
    if not os.path.exists(crash_dir):
        os.makedirs(crash_dir)

    crash_log_name = '/'.join([crash_dir, '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())])

    with open(crash_log_name, 'w') as f:
        f.write('Exception while processing following command: "{}"\n'.format(command))
        f.write(str(exception))


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    parser.add_argument(
        "-l", "--language", help="The language you want translations from", default="Finnish")
    parser.add_argument(
        "-d", "--debug", help="Set to true if you want debug output", default=False
    )
    args = parser.parse_args()
    language = args.language
    if args.debug:
        logger.setLevel(logging.DEBUG)
    wiktionary = Wiktionary(language)
    wiktionary.run()
