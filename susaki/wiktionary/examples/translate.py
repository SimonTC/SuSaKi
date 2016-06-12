from susaki.wiktionary.connectors import APIConnector
from susaki.wiktionary.parsing import HTMLParser
import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)

file_path = '/media/simon/Data/Dropbox/Onnenkieli/Vocabularies/14 - Puhelin soi.csv'
connector = APIConnector()
parser = HTMLParser()


def collect_raw_article(word):
    try:
        raw_article = connector.collect_raw_article(word)
        return raw_article
    except:
        return None


def collect_translations(article_root):
    translation_list = []
    language_part = article_root.find('Languages').find('Finnish')
    pos_parts = language_part.find('POS-parts')
    for pos in pos_parts:
        # print('\n   {}'.format(pos.tag))
        translations = pos.find('Translations')
        for translation in translations:
            text = translation.find('Text')
            text = text.text
            translation_list.append(text)
    return translation_list

start_time = time.time()
logger.info('Starting translation of words in the file {}'.format(file_path))
logger.debug('Opening source file {}'.format(file_path))
with open(file_path) as source_file:
    logger.debug('Opening target file {}'.format(file_path))
    with open(file_path + '_translated', 'w') as target_file:
        for line in source_file:
            line = line.replace('\n', '')
            if line != '':
                logger.info('Collecting article for {}'.format(line))
                raw_article = collect_raw_article(line)
                if raw_article:
                    logger.debug('Article exists')
                    xml_root = parser.parse_article(
                        raw_article, line, 'Finnish')
                    translations = collect_translations(xml_root)
                else:
                    logger.debug('No article exists')
                    translations = None
                if translations:
                    target_file.write(
                        '{}\t{}\n'.format(line, ' | '.join(translations)))
                else:
                    target_file.write('{}\t[UNKNOWN]\n'.format(line))

logger.info('Finished translating the words in the file. Took {:d} seconds.'.format(int(
    time.time() - start_time)))
