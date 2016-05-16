'''
Created on May 16, 2016

@author: simon
'''
import pytest
import os
from distutils import dir_util
import requests
from requests_file import FileAdapter
from susaki.wiktionary.parsing import HTMLParser, Article


@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    Source: http://stackoverflow.com/a/29631801
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir


class TestHTMLParser:

    @pytest.fixture
    def raw_article(self, datadir):
        article_path = '/'.join([str(datadir), 'kuu.html'])
        s = requests.Session()
        s.mount('file://', FileAdapter())
        return s.get('file://' + article_path)

    @pytest.fixture
    def parser(self):
        return HTMLParser('Finnish')

    def test_returns_article_object(self, parser, raw_article):
        result = parser.parse_article(raw_article, 'kuu')
        assert isinstance(result, Article)

    def test_only_returns_article_in_correct_target_language(self):
        assert False

    def test_returns_synonyms_if_they_exists(self):
        assert False

    def test_returns_derived_terms_if_they_exists(self):
        assert False

    def test_returns_none_as_synonym_when_no_synonyms_exists(self):
        assert False

    def test_returns_none_as_derived_term_when_no_derived_terms_exist(self):
        assert False

    def test_returns_correct_definitions_of_a_given_word(self):
        assert False

    def test_returns_the_correct_translations_of_the_definitions(self):
        assert False

    def test_returns_correct_examples_for_each_translation(self):
        assert False

    def test_returns_compound_words_if_they_exists(self):
        return False

    def test_returns_none_as_compund_words_if_none_exists(self):
        return False

    def test_returns_declensions_table_if_it_exists(self):
        return False

#
#     #Should be moved to another class
#     def test_can_translate_from_english_to_target_language(self):
#         assert False
