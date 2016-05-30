'''
Created on Apr 21, 2016

@author: simon
'''
import re

import requests

import logging

from bs4 import BeautifulSoup

from collections import namedtuple

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)

translation_tuple = namedtuple('translation', 'translation, examples')
example_tuple = namedtuple('example', 'example, translation')


class HTMLParser():

    possible_word_classes = r'Verb|Noun|Adjective|Numeral|Pronoun|Adverb|Suffix|Conjunction|Determiner|Exclamation|Preposition'

    def _extract_soup_between(self, from_tag, to_tag, soup):
        """
        Extract all tags between the from and to tags in the given soup.
        If to_tag doesn't exist, all text from the from_tag to the end of the page is returned.
        The soup is converted to a string since there might be problems with
        the html which prevents BeautifulSoup from working correctly.
        Returns a new soup object of the text between the two tags.
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
        """
        Extract the language tag that comes after the target language tag.
        """
        has_seen_target_language = False
        for tag in language_tags:
            if has_seen_target_language:
                return tag
            elif tag.find_all('span', id=target_language):
                has_seen_target_language = True
        if not has_seen_target_language:
            raise KeyError(
                'No explanations exists for the language: {}'.format(target_language))
        else:
            return tag

    def _extract_correct_language_part(self, raw_articles, source_language):
        """
        raw_articles: beautiful soup object containing the main content of the raw article
        """
        from_tag = raw_articles.find(
            'span', {'class': 'mw-headline', 'id': source_language})
        to_tag = self._extract_language_part_border(
            raw_articles.find_all('h2'), source_language)
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
        pos_type = pos_part.find('span', {'class': 'mw-headline'}).text
        pos_dict = {'pos': pos_type}
        # Extract translations + examples
        # The list of translations should always be the first list in the POS
        # part
        translation_list = pos_part.find_all('ol')[0]
        # Each list item contains a translation together with eventual examples
        translations = translation_list.find_all('li')
        pos_translation_list = []
        for i, translation in enumerate(translations):
            only_translation = self._extract_soup_between(
                '<li>', '<dl>', translation)
            translation_text = only_translation.get_text()
            translation_text = translation_text.replace('\n', '')
            examples = translation.find_all('dl')
            t = translation_tuple(translation=translation_text, examples=[])
            pos_translation_list.append(t)
        pos_dict['translations'] = pos_translation_list

        # Extract declension

        # Extract usage notes

        # Extract synonyms

        # Extract related terms

        # Extract Derived terms

        # Extract compunds
        return pos_dict

    def _parse_etymology_part(self, etymology_part):
        etymology_dict = {}
        POS_parts = self._extract_parts(
            etymology_part, 'span', self.possible_word_classes, None)
        pos_parts_dict = {}
        for j, pos_part in enumerate(POS_parts):
            pos_dict = self._parse_POS(pos_part)
            pos_parts_dict['pos {}'.format(j)] = pos_dict
        etymology_dict['parts-of-speech'] = pos_parts_dict
        return etymology_dict

    def _extract_pos_parts(self, language_part):
        pos_tags = language_part.find_all(text=re.compile(self.possible_word_classes), attrs={'class': 'mw-headline'})
        pos_heading_tags = [tag.parent for tag in pos_tags]

        # We can't be sure of the header levels so we need to extract them
        # to know when to stop extracting
        header_levels = {header.name for header in pos_heading_tags}
        if len(header_levels) != 1:
            # The wiktionary page is badly formatted.
            # TODO: figure out what to do What to do?
            logger.info('Different header levels')
            return None
        header_level = header_levels.pop()[1]
        tag = pos_heading_tags[0]
        # logger.debug('heading tags: {}'.format(pos_heading_tags))
        # logger.debug('lenght: {}'.format(len(pos_heading_tags)))
        # logger.debug('First header tag: {}'.format(pos_heading_tags[0]))
        # logger.debug("First header's sibling: {}".format(tag.next_sibling))
        pos_parts = []
        pos_part = []
        in_pos = True
        while tag:
            logger.debug(tag.name)
            m = re.match(r'^h\d$', str(tag.name))
            if m:
                level = m.group(0)[1]
                if level <= header_level:
                    logger.debug('New header at same     or higher level found')
                    if pos_part:
                        logger.debug('Finishing pos part')
                        pos_string = ''.join(str(pos_part))
                        pos_parts.append(BeautifulSoup(pos_string, 'lxml'))
                        pos_part = []
                    if tag in pos_heading_tags:
                        logger.debug('Starting new pos part')
                        in_pos = True
                    else:
                        in_pos = False
            if in_pos:
                pos_part.append(tag)
            tag = tag.next_sibling

        if pos_part:
            logger.debug('Finishing pos part')
            pos_string = ''.join(str(pos_part))
            pos_parts.append(BeautifulSoup(pos_string, 'lxml'))
        logger.debug('Number of POS parts: {}'.format(len(pos_parts)))
        for pos in pos_parts:
            print(pos.prettify())
            print('\n\n\n')

        # print(header_level)
        # pos_tag = language_part.find(text=re.compile(self.possible_word_classes), attrs={'class': 'mw-headline'})
        # pos_tag = language_part.find(
        #    'span', {'class': 'mw-headline', 'text': re.compile(self.possible_word_classes)})

        # print(type(pos_tag))
        # print(pos_tag)
        # print(pos_tag.text)
        # print(pos_tag.parent)
        # print(type(pos_tag.parent))
        pass

    def _parse_language_part(self, language_part, language):
        language_dict = {}
        etymology_parts = self._extract_parts(
            language_part, 'span', 'Etymology', self.possible_word_classes)
        etymologies_list = []
        for etymology in etymology_parts:
            etymologies_list.append(self._parse_etymology_part(etymology))
        language_dict['etymologies'] = etymologies_list
        return language_dict

    def parse_article(self, raw_article, word, language='Finnish'):
        """
        raw_article: html-document of the whole article for the word
        word: the word this article is about
        language: source language of the word.
            This language is used to do the translation into English
        """
        article_dict = {'word': word}
        soup = BeautifulSoup(raw_article, 'html.parser')
        main_content = soup.find(
            'div', {'class': 'mw-content-ltr', 'id': 'mw-content-text'})
        language_part = self._extract_correct_language_part(
            main_content, language)

        self._extract_pos_parts(language_part)

        # article_dict[language] = self._parse_language_part(
        #     language_part, language)

        return article_dict


def print_translations(article_dict):
    print(article_dict['word'])
    for etymology in \
            article_dict['Finnish']['etymologies']:
        for _, pos in etymology['parts-of-speech'].items():
            print('   {}'.format(pos['pos']))
            for translation_tuple in pos['translations']:
                print('      - ' + translation_tuple.translation)


if __name__ == '__main__':
    word = 'sää'
    url = 'https://en.wiktionary.org/wiki/{}'.format(word)
    parser = HTMLParser()
    req = requests.get(url)
    article_dict = parser.parse_article(req.content, word)
    # print_translations(article_dict)