'''
Created on Apr 21, 2016

@author: simon
'''
import re

import logging

from bs4 import BeautifulSoup

from collections import namedtuple

from susaki.wiktionary.connectors import APIConnector

import argparse
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)

translation_tuple = namedtuple('translation', 'translation, examples')
example_tuple = namedtuple('example', 'example, translation')


class HTMLParser():
    PARSER = 'lxml'  # 'html.parser' # 'lxml'

    possible_word_classes = 'Verb|Noun|Adjective|Numeral|Pronoun|Adverb|Suffix|Conjunction|Determiner|Exclamation|Preposition|Postposition|Prefix'

    def _extract_soup_between(self, from_tag, to_tag, soup):
        """
        Extract all tags between the from and to tags in the given soup.
        The from tag is included in the extracted tags.
        If to_tag doesn't exist, all text from the from_tag to the end of the page is returned.
        Returns a new soup object of the text between the two tags.
        """
        logger.debug('Extracting soup between two tags')
        logger.debug('From tag: \n{}\n'.format(from_tag))
        logger.debug('To tag: \n{}\n'.format(to_tag))
        tags_between = []
        next_ = from_tag
        while True:
            tags_between.append(str(next_))
            next_ = next_.nextSibling
            if not next_ or next_ == to_tag:
                break
        soup_text = ''.join(tags_between)
        new_soup = BeautifulSoup(soup_text, self.PARSER)
        return new_soup

    def _extract_translations(self, pos_part):
        logger.debug('Starting extraction of translations')
        translation_list = pos_part.find('ol')
        translations = translation_list.find_all('li', recursive=False)
        num_translations = len(translations)
        logger.debug('Translations found: {}'.format(num_translations))
        return translations

    def _extract_translations0(self, pos_part):
        logger.debug('Starting extraction of translations')
        translation_list = pos_part.find('ol')
        # Each list item contains a translation together with eventual examples
        translations = translation_list.find_all('li', recursive=False)
        logger.debug('Translations found: {}'.format(len(translations)))
        pos_translation_list = []
        for i, translation in enumerate(translations):
            logger.debug('Extractig translation {}'.format(i))
            translation_text_elements = []
            try:
                children = translation.contents
            except AttributeError:
                translation_text = translation.replace('\n', '')
            else:
                for i, child in enumerate(children):
                    if child.name != 'dl':
                        try:
                            child_text = child.text
                        except AttributeError:
                            # Child is a navigable string
                            child_text = child
                        child_text = child_text.replace('\n', '')
                        translation_text_elements.append(child_text)
                    else:
                        # There are examples
                        examples = child
                translation_text = ''.join(translation_text_elements)
            logger.debug('Translation text: {}'.format(translation_text))
            t = translation_tuple(translation=translation_text, examples=[])
            pos_translation_list.append(t)
        return pos_translation_list

    def _parse_POS(self, pos_part):
        pos_type = pos_part.find('span', {'class': 'mw-headline'}).text
        pos_dict = {'pos': pos_type}
        # Extract translations + examples
        # The list of translations should always be the first list in the POS
        # part
        pos_translation_list = self._extract_translations(pos_part)
        pos_dict['translations'] = pos_translation_list

        # Extract declension

        # Extract usage notes

        # Extract synonyms

        # Extract related terms

        # Extract Derived terms

        # Extract compunds
        return pos_dict

    def _get_pos_header_level(self, pos_tag_headers):
        header_levels = {header.name for header in pos_tag_headers}
        if len(header_levels) != 1:
            raise ValueError('The POS-parts are placed at different header levels')
        pos_header_level = header_levels.pop()[1]
        return pos_header_level

    def _tag_ends_pos_part(self, tag, pos_tag_header_level):
        if not re.match(r'^h\d$', str(tag.name)):
            return False
        elif tag.name[1] > pos_tag_header_level:
            return False
        else:
            return True

    def _extract_pos_parts(self, language_part):
        pos_tags = language_part.find_all(
            text=re.compile(self.possible_word_classes),
            attrs={'class': 'mw-headline'})
        num_pos_tags = len(pos_tags)
        if num_pos_tags == 0:
            raise ValueError('No POS-parts present')
        logger.debug('Number of POS-tags in language part: {}'.format(num_pos_tags))
        pos_tag_headers = [tag.parent for tag in pos_tags]
        pos_tag_header_level = self._get_pos_header_level(pos_tag_headers)
        pos_parts = []
        start_tag = pos_tag_headers[0]
        for tag in start_tag.next_siblings:
            if start_tag and self._tag_ends_pos_part(tag, pos_tag_header_level):
                logger.debug('Tag {} ends current pos part'.format(tag.name))
                pos_part = self._extract_soup_between(start_tag, tag, language_part)
                pos_parts.append(pos_part)
                start_tag = None
            tag_starts_new_pos_part = tag in pos_tag_headers
            if tag_starts_new_pos_part:
                logger.debug('Tag {} starts a new pos part'.format(tag.name))
                start_tag = tag
        if start_tag:
            logger.debug('No tag to end last pos part. '
                         'Extract from last start tag to end of language part')
            pos_part = self._extract_soup_between(start_tag, None, language_part)
            pos_parts.append(pos_part)
        logger.debug('Found {} POS-tags in language part'.format(len(pos_parts)))
        return pos_parts

    def _extract_language_part(self, raw_article, language):
        language_header_tags = raw_article.find_all('h2')
        start_tag = None
        end_tag = None
        logger.debug('Number of language headers: {}'.format(
            len(language_header_tags)))
        for i, language_header in enumerate(language_header_tags):
            logger.debug('Checking header {}'.format(i))
            target_language_found = language_header.find(
                'span', {'class': 'mw-headline', 'id': language})
            if target_language_found:
                start_tag = language_header
                logger.debug('Start tag found')
                try:
                    end_tag = language_header_tags[i + 1]
                    logger.debug('End tag found')
                except IndexError:
                    logger.debug('No end tag found')
                    pass
                finally:
                    break
        if not start_tag:
            raise KeyError(
                'No explanations exists for the language: {}'.format(language))
        language_part = self._extract_soup_between(start_tag, end_tag, raw_article)
        return language_part

    def parse_article(self, raw_article, word, language='Finnish'):
        """
        raw_article: html-document of the whole article for the word.
            Must have the same format as that returned by the Wiktionary API
        word: the word this article is about
        language: source language of the word.
            This language is used to do the translation into English
        """
        article_dict = {'word': word}
        soup = BeautifulSoup(raw_article, self.PARSER)
        language_part = self._extract_language_part(soup, language)
        pos_parts = self._extract_pos_parts(language_part)
        pos_dict_list = []
        for pos_part in pos_parts:
            pos_dict = self._parse_POS(pos_part)
            pos_dict_list.append(pos_dict)
        language_dict = {'pos-parts': pos_dict_list}
        article_dict[language] = language_dict

        return article_dict


def print_translations(article_dict):
    print(article_dict['word'])
    language_dict = article_dict['Finnish']
    # logger.debug('Number of pos: {}'.format(len(language_dict['pos-parts'])))
    for pos_dict in language_dict['pos-parts']:
        print('\n   {}'.format(pos_dict['pos']))
        # logger.debug('Number of translations: {}'.format(len(pos_dict['translations'])))
        for translation_tuple in pos_dict['translations']:
            print('      - ' + translation_tuple.translation)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    arg_parser.add_argument('word')
    args = arg_parser.parse_args()
    word = args.word
    connector = APIConnector()
    content_text = connector.collect_raw_article(word)
    parser = HTMLParser()
    article_dict = parser.parse_article(content_text, word)
    print_translations(article_dict)
