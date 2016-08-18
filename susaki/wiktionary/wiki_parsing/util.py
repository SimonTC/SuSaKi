from bs4 import BeautifulSoup
import re
import logging
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


def extract_soup_between(from_tag, to_tag, soup, parser='html.parser'):
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
    new_soup = BeautifulSoup(soup_text, parser)
    return new_soup


def clean_text(text):
    """
    Removes line break characters and unneeded spaces from the text
    """
    clean = text.replace('\n', '')
    clean = clean.strip()
    clean = re.sub(r'  *', ' ', clean)
    return clean
