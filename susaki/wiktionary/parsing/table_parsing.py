import re

import logging

from bs4 import BeautifulSoup
from lxml import etree

from susaki.wiktionary.connectors import APIConnector

import argparse
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('__name__')


class TableParser:

    def _extract_meta_information(self, headline_text):
        """ Extract meta information from the headline text"""
        meta_info = re.match(r' *Inflection of (\w+) \(Kotus type (\d\d?)/(\w+), (.*) gradation\)', headline_text)
        word = meta_info.group(1)
        kotus_type = meta_info.group(2)
        kotus_word = meta_info.group(3)
        gradation = meta_info.group(4)
        logger.debug('Word: {}'.format(word))
        logger.debug('Kotus type: {}'.format(kotus_type))
        logger.debug('Kotus word: {}'.format(kotus_word))
        logger.debug('Gradation {}'.format(gradation))
        return word, kotus_type, kotus_word, gradation

    def _create_meta_tree(self, word, kotus_type, kotus_word, gradation):
        meta_element = etree.Element('meta')
        kotus_element = etree.SubElement(meta_element, 'kotus')
        kotus_type_element = etree.SubElement(kotus_element, 'type')
        kotus_type_element.text = kotus_type
        kotus_word_element = etree.SubElement(kotus_element, 'word')
        kotus_word_element.text = kotus_word
        gradation_element = etree.SubElement(meta_element, 'gradation')
        gradation_element.text = gradation
        word_element = etree.SubElement(meta_element, 'word')
        word_element.text = word
        return meta_element

    def _parse_meta_information(self, headline_row):
        logger.debug('Extracting meta info from table')
        headline_element = headline_row.th
        headline_text = headline_element.text
        logger.debug('Headline text: {}'.format(headline_text))
        word, kotus_type, kotus_word, gradation = self._extract_meta_information(headline_text)
        meta_element = self._create_meta_tree(word, kotus_type, kotus_word, gradation)
        return meta_element

    def _clean_text(self, text):
        clean = text.replace('\n', '')
        clean = clean.strip()
        clean = re.sub(r'  *', ' ', clean)
        return clean


class NounTableParser(TableParser):

    def parse_table(self, rows):
        logger.debug('Inflection table type: Noun')
        table_root = etree.Element('table')
        in_accusative = False
        noun_case_element = None

        start_row = self._find_table_start(rows)

        for i, row in enumerate(rows[start_row:]):
            logger.debug('Parsing row {}'.format(i + start_row))
            noun_case_name = row.th.text
            noun_case_name = self._clean_text(noun_case_name)
            logger.debug('Creating new noun case element: {}'.format(
                noun_case_name))
            noun_case_element = etree.Element(noun_case_name)
            if in_accusative:
                logger.debug('Entering second accusative row (genitive)')
                self._parse_second_accusative_row(noun_case_element, row)
                in_accusative = False
            else:
                table_root.append(noun_case_element)
                if noun_case_name == 'accusative':
                    logger.debug('Found the accusative case')
                    in_accusative = True
                    noun_case_element = etree.SubElement(
                        noun_case_element, 'nominative')
                self._parse_noun_table_row(
                    row, noun_case_element, noun_case_name)
        return table_root

    def _find_table_start(self, rows):
        """ The noun table has to parts. The first part contains nominative,
        genitive, partitive and illative.
        After these four cases the main table begins and those four cases
        are repeated there but not in the same other. Because of this we want to
        ignore the first lines and first start parsing on the main table.
        Rows: The rows of the table
        Returns: the id of the row where the first entry of the main table exists.
                 (After the table headers)
        """
        logger.debug('Starting search for the main table')
        for i, row in enumerate(rows[1:]):
            noun_case_name = row.th.text
            noun_case_name = self._clean_text(noun_case_name)
            try:
                etree.Element(noun_case_name)
            except ValueError as err:
                if str(err) == 'Empty tag name':
                    # We found the headers of the real table
                    logger.debug('Found the table headers')
                    return i + 1
                else:
                    raise
        raise ValueError("Couldn't find the start of the main table")

    def _parse_second_accusative_row(self, noun_case_element, row):
        noun_case_element = noun_case_element.getparent()
        noun_case_element = etree.SubElement(noun_case_element, 'genitive')
        noun_case_element.text = self._clean_text(row.find('td').text)

    def _parse_noun_table_row(self, row, noun_case_element, noun_case_name):
        """Extracts the singular and plural form from the table row"""
        row_elements = row.find_all('td')
        singular = row_elements[0].text
        if noun_case_name == 'genitive':
            logger.debug('Entering genitive case')
            plural = self._clean_text(row_elements[1].find('span').text)
        else:
            plural = self._clean_text(row_elements[1].text)
        singular_element = etree.SubElement(noun_case_element, 'singular')
        singular_element.text = self._clean_text(singular)
        plural_element = etree.SubElement(noun_case_element, 'plural')
        plural_element.text = self._clean_text(plural)
