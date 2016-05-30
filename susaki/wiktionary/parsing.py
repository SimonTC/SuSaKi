'''
Created on Apr 21, 2016

@author: simon
'''
import re

import logging

from bs4 import BeautifulSoup

from collections import namedtuple

from susaki.wiktionary.connectors import APIConnector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)

translation_tuple = namedtuple('translation', 'translation, examples')
example_tuple = namedtuple('example', 'example, translation')


class HTMLParser():
    PARSER = 'lxml'  #'html.parser' # 'lxml'

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
        # text_to_extract = text_to_extract[:-2]
        soup = BeautifulSoup(text_to_extract, self.PARSER)
        return soup

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

    def _extract_pos_parts(self, language_part):
        logger.debug('Starting extraction of POS-parts')
        pos_tags = language_part.find_all(
            text=re.compile(self.possible_word_classes),
            attrs={'class': 'mw-headline'})
        pos_header_tags = [tag.parent for tag in pos_tags]

        # We can't be sure which level the pos headers are placed at,
        # So we need to extract them.
        header_levels = {header.name for header in pos_header_tags}
        if len(header_levels) != 1:
            # The wiktionary page is badly formatted.
            # TODO: figure out what to do What to do?
            logger.info('Different header levels')
            return None
        header_level = header_levels.pop()[1]
        tag = pos_header_tags[0]
        pos_parts = []
        pos_part_lines = []
        in_pos = True
        while tag:
            logger.debug(tag.name)
            m = re.match(r'^h\d$', str(tag.name))
            if m:
                tag_level = m.group(0)[1]
                if tag_level <= header_level:
                    logger.debug('New header at same or higher level found')
                    if pos_part_lines:
                        logger.debug('Finishing pos part')
                        pos_string = ''.join(str(pos_part_lines))
                        pos_parts.append(BeautifulSoup(pos_string, self.PARSER))
                        pos_part_lines = []
                    if tag in pos_header_tags:
                        logger.debug('Starting new pos part')
                        in_pos = True
                    else:
                        in_pos = False
            if in_pos:
                pos_part_lines.append(tag)
            tag = tag.next_sibling

        if pos_part_lines:
            logger.debug('Finishing pos part')
            pos_string = ''.join(str(pos_part_lines))
            pos_parts.append(BeautifulSoup(pos_string, self.PARSER))
        logger.debug('Number of POS parts: {}'.format(len(pos_parts)))
        return pos_parts

    def _extract_language_part(self, raw_article, language):
        language_header_tags = raw_article.find_all('h2')
        start_tag = None
        end_tag = None
        logger.debug('Number of language headers: {}'.format(
            len(language_header_tags)))
        for i, language_header in enumerate(language_header_tags):
            logger.debug('Checking header {}'.format(i))
            if language_header.find(
                    'span', {'class': 'mw-headline', 'id': language}):
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
    # url = 'https://en.wiktionary.org/wiki/{}'.format(word)
    # parser = HTMLParser()
    # req = requests.get(url)
    # article_dict = parser.parse_article(req.content, word)
    connector = APIConnector()
    content_text = connector.collect_raw_article(word)
    parser = HTMLParser()
    article_dict = parser.parse_article(content_text, word)
    # print_translations(article_dict)
