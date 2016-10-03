#!/home/simon/anaconda3/envs/SuSaKi/bin/python
from susaki.wiktionary.connectors import APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing
import time
import argparse
from examplelogging import setup_logging
import logging


class ListTranslator():

    def __init__(self, debug=False):
        self.setup_logging(debug)
        self.connector = APIConnector()

    def setup_logging(self, debug):
        self.logger = setup_logging(args.debug)
        info_handler = logging.StreamHandler()
        info_handler.addFilter(logging.Filter('root'))
        self.logger.addHandler(info_handler)

    def collect_raw_article(self, word):
        word = word.lower()
        try:
            raw_article = self.connector.collect_raw_article(word)
            return raw_article
        except:
            return None

    def collect_translations(self, article_root):
        translation_list = []
        language_part = article_root.find('Languages').find('Finnish')
        pos_parts = language_part.find('POS-parts')
        self.logger.debug('Number of POS-parts: {}'.format(len(pos_parts)))
        for pos in pos_parts:
            # print('\n   {}'.format(pos.tag))
            translations = pos.find('Translations')
            self.logger.debug('Number of translations-parts: {}'.format(len(translations)))
            for translation in translations:
                text = translation.find('Text')
                text = text.text
                translation_list.append(text)
        return translation_list

    def translate(self, file_path):
        start_time = time.time()
        self.logger.info('Starting translation of words in the file {}'.format(file_path))
        self.logger.debug('Opening source file {}'.format(file_path))
        with open(file_path) as source_file:
            self.logger.debug('Opening target file {}'.format(file_path))
            with open(file_path + '_translated', 'w') as target_file:
                for line in source_file:
                    line = line.replace('\n', '')
                    if line != '':
                        self.logger.info('Collecting article for {}'.format(line))
                        raw_article = self.collect_raw_article(line)
                        if raw_article:
                            self.logger.debug('Article exists')
                            try:
                                xml_root = article_parsing.parse_article(
                                    raw_article, line, 'Finnish')
                                translations = self.collect_translations(xml_root)
                            except Exception as err:
                                self.logger.info("Error while parsing article. Ignoring")
                                self.logger.debug(str(err))
                                translations = None
                        else:
                            self.logger.info('No article exists')
                            translations = None
                        if translations:
                            target_file.write(
                                '{}\t{}\n'.format(line, ' | '.join(translations)))
                        else:
                            target_file.write('{}\t[UNKNOWN]\n'.format(line))

        self.logger.info('Finished translating the words in the file. Took {:d} seconds.'.format(int(
            time.time() - start_time)))

if __name__ == '__main__':
    # Parse arguments
    argparser = argparse.ArgumentParser(
        description='Translate a list of words from Finnish into English using Wiktionary')
    argparser.add_argument('file', help='The file path to the file containing the English words')
    argparser.add_argument(
        "-d", "--debug", help="Set to true if you want debug output", default=False
    )
    args = argparser.parse_args()
    file_path = args.file
    translator = ListTranslator(debug=args.debug)
    translator.translate(file_path)
