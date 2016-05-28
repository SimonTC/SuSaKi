'''
Created on May 12, 2016

@author: simon
'''
import pytest
import requests
from requests_file import FileAdapter

import os
from distutils import dir_util

from susaki.wiktionary.connectors import HTMLConnector
from unittest.mock import MagicMock, patch


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


class TestHTMLConnector:

    @pytest.fixture
    def connector(self):
        return HTMLConnector('Finnish')

    @pytest.fixture
    def request_session(self):
        s = requests.Session()
        s.mount('file://', FileAdapter())
        return s

    @patch('susaki.wiktionary.connectors.HTMLConnector._collect_page')
    def test_returns_KeyError_when_word_is_completely_unknown(self, mock_collector, connector, datadir, request_session):
        page_path = '/'.join([str(datadir), 'no_result.html'])
        mock_collector.return_value = request_session.get(
            'file://' + page_path)
        with pytest.raises(KeyError) as error:
            connector.collect_raw_article('')
        assert 'does not exist on Wiktionary' in str(error)

    @patch('susaki.wiktionary.connectors.HTMLConnector._collect_page')
    def test_returns_suggestions_when_the_word_doesnt_have_an_article_but_exists_in_other_article(self, mock_collector, connector, datadir, request_session):
        page_path = '/'.join([str(datadir), 'multiple_suggestions.html'])
        mock_collector.return_value = request_session.get(
            'file://' + page_path)
        result = connector.collect_raw_article('')
        assert type(result) is list

    @patch('susaki.wiktionary.connectors.HTMLConnector._collect_page')
    def test_returns_article_when_word_has_an_article(self, mock_collector, connector, datadir, request_session):
        page_path = '/'.join([str(datadir), 'article_exists.html'])
        mock_collector.return_value = request_session.get(
            'file://' + page_path)
        result = connector.collect_raw_article('')
        assert type(result) is requests.models.Response
