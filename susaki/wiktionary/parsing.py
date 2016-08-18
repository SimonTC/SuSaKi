'''
Created on Apr 21, 2016

@author: Simon T. Clement
'''


import logging

from lxml import etree

from susaki.wiktionary.connectors import APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing


import argparse
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


def print_translations(article_root):
    language_part = article_root.find('Languages').find('Finnish')
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


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    arg_parser.add_argument('word')
    args = arg_parser.parse_args()
    word = args.word
    connector = APIConnector()
    content_text = connector.collect_raw_article(word)
    article_root = article_parsing.parse_article(content_text, word)
    # s = etree.tostring(article_root, pretty_print=True, encoding='unicode')
    # print(s)
    print_translations(article_root)
    s = etree.tostring(article_root, pretty_print=True, encoding='unicode')
    print(s)
