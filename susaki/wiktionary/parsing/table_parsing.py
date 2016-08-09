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
