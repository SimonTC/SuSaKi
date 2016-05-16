'''
Created on May 12, 2016

@author: simon
'''
import pytest
import requests

import os
from distutils import dir_util

from susaki.wiktionary.connectors import HTMLConnector
from _pytest.monkeypatch import monkeypatch


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


class HTMLConnectorTest:

    @pytest.fixture
    def connector(self):
        return HTMLConnector('Finnish')

    def test_returns_error_when_word_is_completely_unknown(self, connector, datadir):
        def mock_unknown_page(word):
            page_path = '/'.join([str(datadir), 'no_result.html'])
            return requests.get(page_path)
        monkeypatch.setattr(HTMLConnector, '_collect_page', mock_unknown_page)
        assert connector.collect_raw_article('sää') == False

    def test_returns_suggestions_when_the_word_doesnt_have_an_article_but_exists_in_other_article(self):
        assert False

    def test_returns_article_when_word_has_an_article(self):
        assert False

# Following tests should be in other class since they are about the
# parsing of the page and not retrieval

    def test_only_returns_article_in_correct_target_language(self):
        assert False

    def test_can_translate_from_english_to_target_language(self):
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
