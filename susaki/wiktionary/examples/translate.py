from susaki.wiktionary.connectors import APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing
import logging
import time
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger('susaki.wiktionary.parsing').setLevel(logging.INFO)
logging.getLogger('susaki.wiktionary.wiki_parsing.table_parsing').setLevel(logging.INFO)
logger.setLevel(logging.INFO)

connector = APIConnector()


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


def translate(file_path):
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
                        try:
                            xml_root = article_parsing.parse_article(
                                raw_article, line, 'Finnish')
                            translations = collect_translations(xml_root)
                        except Exception as err:
                            logger.info("Error while parsing article. Ignoring")
                            logger.debug(str(err))
                            translations = None
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
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('susaki.wiktionary.parsing').setLevel(logging.DEBUG)
        logging.getLogger('susaki.wiktionary.wiki_parsing.table_parsing').setLevel(logging.DEBUG)
    translate(file_path)
