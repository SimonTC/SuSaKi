from susaki.wiktionary.connectors import HTMLConnector, APIConnector
from susaki.wiktionary.wiki_parsing import article_parsing
import re
import logging
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('__name__')
#logging.getLogger("requests").setLevel(logging.WARNING)


class Wiktionary:

    def __init__(self, language):
        self.language = language
        self.api_connector = APIConnector()
        self.html_connector = HTMLConnector(language)

    def lookup(self, word, only_api=True):
        """ Lookup the given word on wiktionary.
            only_api: if true it will only use the wiktionaty api meaning that
                      no suggestions will be given if the article doesn't exist.
                      If False it will first use the api and then the normal page to see if any suggestions exists.
            Returns a XML tree of the info from the article if it exists.
            Otherwise it returns a list of suggestions if those exists.
            Otherwise it will raise a lookup error.
        """
        if re.match('^ *$', word):
            raise ValueError("The search string cannot be empty")

        try:
            raw_article = self.api_connector.collect_raw_article(word)
        except LookupError:
            if only_api:
                raise
            else:
                suggestions = self.html_connector.collect_raw_article(word)
                return suggestions
        else:
            article_root = article_parsing.parse_article(raw_article, word, self.language)

        return article_root

if __name__ == '__main__':
    from lxml import etree
    wiki = Wiktionary('Finnish')
    root = wiki.lookup('test')
    print(etree.tostring(root, pretty_print=True, encoding='unicode'))
