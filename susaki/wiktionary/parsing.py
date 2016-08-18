'''
Created on Apr 21, 2016

@author: Simon T. Clement
'''
import re

import logging

from bs4 import BeautifulSoup
from lxml import etree

from susaki.wiktionary.connectors import APIConnector
from susaki.wiktionary.wiki_parsing.table_parsing import parse_inflection_table, clean_text

import argparse
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


class HTMLParser():
    PARSER = 'html.parser'

    possible_word_classes = ('Verb|Noun|Adjective|Numeral|Pronoun|Adverb|'
                             'Suffix|Conjunction|Determiner|Exclamation|'
                             'Preposition|Postposition|Prefix|Abbreviation|Particle')

    def _extract_soup_between(self, from_tag, to_tag, soup):
        """
        Extract all tags between the from and to tags in the given soup.
        If to_tag is None, all tags from from_tag to the end of the soup are extracted.
        Returns a new soup object of the text between the two tags.
        """
        logger.debug('Extracting soup between two tags')
        logger.debug('From tag: {}'.format(from_tag.name))
        if to_tag:
            name = to_tag.name
        else:
            name = None
        logger.debug('To tag: {}'.format(name))
        tags_between = []
        next_ = from_tag
        while True:
            logger.debug('Appending {}'.format(next_.name))
            tags_between.append(str(next_))
            next_ = next_.nextSibling
            if not next_ or next_ == to_tag:
                break
        soup_text = ''.join(tags_between)
        new_soup = BeautifulSoup(soup_text, self.PARSER)
        return new_soup

    def _extract_inflection_table(self, pos_soup):
        """
        Extracts the inflection table from the given pos_soup.
        Raises a LookupError if no inflectiont table is present.
        """
        logger.debug('Starting extraction of inflection table')
        inflection_table_soup = pos_soup.find(
            'table',
            attrs={'class': 'inflection-table vsSwitcher vsToggleCategory-inflection'})
        if not inflection_table_soup:
            raise LookupError('No inflection table present')
        else:
            logger.debug('Found inflection table')
        return inflection_table_soup

    def _extract_translations(self, pos_soup):
        """Extracts all translations from the given part-of-speech soup"""
        logger.debug('Starting extraction of translations')
        translation_list = pos_soup.find('ol')
        try:
            translations = translation_list.find_all('li', recursive=False)
        except AttributeError:
            raise LookupError('No translations present')
        num_translations = len(translations)
        if num_translations == 0:
            raise LookupError('No translations present')
        logger.debug('Translations found: {}'.format(num_translations))
        return translations

    def _parse_example(self, example_soup):
        logging.debug('Start example parsing on following soup:\n{}\n'.format(example_soup))
        example_part_root = etree.Element('Examples')
        example_elements = example_soup.find_all(
            re.compile('dd|li'), recursive=False)
        logger.debug('Found {} example elements'.format(len(example_elements)))
        for i, example in enumerate(example_elements):
            logger.debug('Parsing example {}'.format(i))
            example_root = etree.Element('Example')
            example_part_root.append(example_root)
            example_translation = example.find('dl')
            try:
                example_translation_text = example_translation.text
            except AttributeError:
                # Example is placed as a quotation insted of a standard example
                logger.debug('Example placed as a quotation')
                example_text = example.text
            else:
                example_translation_text_clean = clean_text(
                    example_translation_text)
                # Remove translation to avoid having it show up in the example text
                example_translation.clear()
                example_text = example.text
                example_translation_element = etree.Element('Translation')
                example_translation_element.text = example_translation_text_clean
                example_root.append(example_translation_element)

            example_text_clean = clean_text(example_text)
            example_text_element = etree.Element('Text')
            example_text_element.text = example_text_clean
            example_root.append(example_text_element)

        example_soup.clear()
        return example_part_root

    def _parse_translation(self, translation_soup):
        logger.debug('Parsing translation part')
        root = etree.Element('Translation')
        example_part = translation_soup.find(re.compile('dl|ul'))
        if example_part:
            example_part_root = self._parse_example(example_part)
            root.append(example_part_root)
        text = translation_soup.text
        text_clean = clean_text(text)
        text_element = etree.Element('Text')
        text_element.text = text_clean
        root.append(text_element)
        return root

    def _parse_POS(self, pos_part):
        pos_type = pos_part.find('span', {'class': 'mw-headline'}).text
        pos_root = etree.Element(pos_type)
        translations_root = etree.Element('Translations')
        pos_root.append(translations_root)
        translation_parts = self._extract_translations(pos_part)
        for translation_part in translation_parts:
            translation_element = self._parse_translation(translation_part)
            translations_root.append(translation_element)
        try:
            inflection_table = self._extract_inflection_table(pos_part)
        except LookupError as err:
            logger.debug("Didn't find an inflection table")
            if str(err) == 'No inflection table present':
                pass
            else:
                raise
        else:
            logger.debug('Found a {} inflection table'.format(pos_type))
            table_element = parse_inflection_table(inflection_table, pos_type.lower())
            pos_root.append(table_element)
        return pos_root

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
        logger.debug('Starting extraction of POS-parts')
        pos_tags = language_part.find_all(
            text=re.compile(self.possible_word_classes),
            attrs={'class': 'mw-headline'})
        num_pos_tags = len(pos_tags)
        if num_pos_tags == 0:
            logger.debug("No POS-parts present")
            raise LookupError('No POS-parts present')
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
        logger.debug('Finished extraction of POS-parts')
        return pos_parts

    def _extract_language_part(self, raw_article, language):
        """
        Extracts the part of the article that contains information about the
        source language.
        """
        logger.debug('Starting language part extraction')
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
            raise LookupError(
                'No explanations exists for the language: {}'.format(language))
        language_part = self._extract_soup_between(start_tag, end_tag, raw_article)
        logger.debug("Finished language part extraction")
        return language_part

    def parse_article(self, raw_article, word, language='Finnish'):
        """
        raw_article: html-document of the whole article for the word.
            Must have the same format as that returned by the Wiktionary API
        word: the word this article is about
        language: source language of the word.
            This language is used to do the translation into English
        """
        logger.debug('Parsing article')
        article_root = etree.Element('Article')
        word_element = etree.Element('Word')
        word_element.text = word
        article_root.append(word_element)

        languages_root = etree.Element('Languages')
        article_root.append(languages_root)
        language_element = etree.Element(language)
        languages_root.append(language_element)

        raw_soup = BeautifulSoup(raw_article, self.PARSER)
        language_part = self._extract_language_part(raw_soup, language)

        pos_parts = self._extract_pos_parts(language_part)
        pos_parts_root = etree.Element('POS-parts')
        language_element.append(pos_parts_root)
        for pos_part in pos_parts:
            pos_part_element = self._parse_POS(pos_part)
            pos_parts_root.append(pos_part_element)

        return article_root


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
    parser = HTMLParser()
    article_root = parser.parse_article(content_text, word)
    # s = etree.tostring(article_root, pretty_print=True, encoding='unicode')
    # print(s)
    print_translations(article_root)
    s = etree.tostring(article_root, pretty_print=True, encoding='unicode')
    print(s)
