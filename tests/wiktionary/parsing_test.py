'''
Created on May 16, 2016

@author: simon
'''
import pytest
import os
from distutils import dir_util
import requests
from requests_file import FileAdapter
from susaki.wiktionary.parsing import HTMLParser

from bs4 import BeautifulSoup


@pytest.fixture(scope='module')
def datadir(tmpdir_factory, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    Source: http://stackoverflow.com/a/29631801
    Using tmpdir_factory to only create the directory once.
    Otherwise it would be created for each test using this fixture
    (https://pytest.org/latest/tmpdir.html)
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    tmpdir_ = tmpdir_factory.getbasetemp()
    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir_))

    return tmpdir_


class TestHTMLParser:

    @pytest.fixture(scope='module')
    def raw_articles(self, datadir):
        article_dict = {}
        for article in os.listdir(str(datadir)):
            if article.endswith('.html'):
                article_name = article.replace('.html', '')
                article_path = '/'.join([str(datadir), article])
                s = requests.Session()
                s.mount('file://', FileAdapter())
                article_dict[article_name] = s.get('file://' + article_path)
        return article_dict

    @pytest.fixture
    def parser(self):
        return HTMLParser()

    def extract_language_part(self, article, parser):
        soup = BeautifulSoup(article, 'html.parser')
        main_content = soup.find(
            'div', {'class': 'mw-content-ltr', 'id': 'mw-content-text'})
        language_part = parser._extract_correct_language_part(
            main_content, 'Finnish')
        return language_part

    def test_returns_dict_object(self, parser, raw_articles):
        result = parser.parse_article(raw_articles['kuu'].content, 'kuu')
        assert isinstance(result, dict)

    @pytest.mark.parametrize('word, not_included', [
        ('kuu', ['Estonian', 'Ingrian', 'Votic']),
        ('ilma', ['Estonian', 'Maltese', 'Votic', 'Võro']),
        ('koira', ['Karelian', 'Votic']),
        ('luen', ['Danish'])])
    def test_only_returns_article_about_correct_source_language(self, parser, raw_articles, word, not_included):
        language_part = self.extract_language_part(
            raw_articles[word].content, parser)
        assert language_part.find(id='Finnish')
        for language in not_included:
            assert not language_part.find(id=language)

    def test_does_return_error_if_article_doesnt_contain_source_language(self, parser, raw_articles):
        with pytest.raises(KeyError) as exinfo:
            language_part = self.extract_language_part(
                raw_articles['hello'].content, parser)
        assert 'No explanations exists for the language:' in str(exinfo)

    @pytest.mark.parametrize('word,expected', [
        ('kuu', 3),
        ('sää', 2),
        ('luen', 1),
        ('koira', 1)])
    def test_returns_correct_number_of_etymology_parts(self, parser, raw_articles, word, expected):
        article = raw_articles[word]
        language_part = self.extract_language_part(article.content, parser)
        etymologies = parser._extract_parts(
            language_part, 'span', 'Etymology', parser.possible_word_classes)
        assert len(etymologies) == expected

#     def test_extracts_correct_pos_names(self):
#         assert False
#     def test_returns_synonyms_if_they_exists(self):
#         assert False
#
#     def test_returns_derived_terms_if_they_exists(self):
#         assert False
#
#     def test_returns_none_as_synonym_when_no_synonyms_exists(self):
#         assert False
#
#     def test_returns_none_as_derived_term_when_no_derived_terms_exist(self):
#         assert False
#
#     def test_returns_correct_definitions_of_a_given_word(self):
#         assert False
#
#     def test_returns_the_correct_translations_of_the_definitions(self):
#         assert False
#
#     def test_returns_correct_examples_for_each_translation(self):
#         assert False
#
#     def test_returns_compound_words_if_they_exists(self):
#         assert False
#
#     def test_returns_none_as_compund_words_if_none_exists(self):
#         assert False
#
#     def test_returns_declensions_table_if_it_exists(self):
#         assert False
#
# #
# #     #Should be moved to another class
# #     def test_can_translate_from_english_to_target_language(self):
# #         assert False