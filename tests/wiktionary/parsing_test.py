'''
Created on May 16, 2016

@author: simon
'''
import pytest
import os
from distutils import dir_util
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


class TestLanguageExtraction:

    @pytest.mark.xfail
    def test_extract_correctly_when_only_language_in_article():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_first_language_in_article():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_last_language_in_article():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_between_other_languages():
        assert False

    @pytest.mark.xfail
    def test_throw_exception_when_language_not_present_in_article():
        assert False


class TestPOSExtraction:

    @pytest.mark.xfail
    def test_extract_correctly_when_no_etymology_tags():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_only_single_POS():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_multiple_identical_POS_parts():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_when_multiple_different_POS_parts():
        assert False

    @pytest.mark.xfail
    def test_POS_extraction_raises_error_if_POS_tags_on_different_levels():
        assert False

    @pytest.mark.xfail
    def test_POS_extraction_raises_error_if_no_POS_tags_present():
        assert False


class TestTranslationExtraction:

    @pytest.mark.xfail
    def test_return_null_if_no_translations():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_if_only_one_translation():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_if_multiple_translations():
        assert False


class TestExampleExtraction:

    @pytest.mark.xfail
    def test_return_null_if_no_examples():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_if_example_and_its_translation_are_on_same_line():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_if_example_and_its_translation_are_on_different_lines():
        assert False

    @pytest.mark.xfail
    def test_extract_correctly_if_multiple_examples():
        assert False


class TestConjugationExtraction:

    @pytest.mark.xfail
    def test_return_null_if_no_conjugation_table():
        assert False

    @pytest.mark.xfail
    def test_exract_verb_conjugation_table_correctly():
        assert False

    @pytest.mark.xfail
    def test_extract_noun_conjugation_table_correctly():
        assert False


class TestHTMLParser:

    def load_html_pages(self, datadir, sub_folder):
        article_dict = {}
        article_dir = '{}/{}'.format(str(datadir), sub_folder)
        for article in os.listdir(article_dir):
            if article.endswith('.html'):
                article_name = os.path.splitext(article)[0]
                article_path = '/'.join([str(article_dir), article])
                with open(article_path, 'r') as f:
                    lines = f.readlines()
                    content = ''.join(lines)
                    article_dict[article_name] = content
        return article_dict

    @pytest.fixture(scope='module')
    def raw_articles(self, datadir):
        return self.load_html_pages(datadir, 'raw_pages')

    @pytest.fixture
    def expected_language_parts(self, datadir):
        return self.load_html_pages(datadir, 'expected_language_parts')

    @pytest.fixture
    def parser(self):
        return HTMLParser()

    def extract_language_part(self, article, parser):
        soup = BeautifulSoup(article, 'lxml')
        language_part = parser._extract_language_part(soup, 'Finnish')
        return language_part

    def test_output_dict_formatted_correctly():
        assert False

    def test_returns_dict_object(self, parser, raw_articles):
        result = parser.parse_article(raw_articles['kuu'], 'kuu')
        assert isinstance(result, dict)

    @pytest.mark.parametrize('word, not_included', [
        ('kuu', ['Estonian', 'Ingrian', 'Votic']),
        ('ilma', ['Estonian', 'Maltese', 'Votic', 'Võro']),
        ('koira', ['Karelian', 'Votic']),
        ('luen', ['Danish'])])
    def test_only_returns_article_about_correct_source_language(self, parser, raw_articles, word, not_included):
        language_part = self.extract_language_part(
            raw_articles[word], parser)
        assert language_part.find(id='Finnish')
        for language in not_included:
            assert not language_part.find(id=language)

    def test_does_return_error_if_article_doesnt_contain_source_language(self, parser, raw_articles):
        with pytest.raises(KeyError) as exinfo:
            self.extract_language_part(
                raw_articles['hello'], parser)
        assert 'No explanations exists for the language:' in str(exinfo)

    @pytest.mark.parametrize('word', ['että', 'haluta', 'ilma', 'ilman', 'koira', 'kuu', 'kuussa', 'lähettää', 'luen', 'olla', 'päästä', 'sää'])
    def test_does_return_correct_lanugage_parts(self, parser, expected_language_parts, raw_articles, word):
        language_part = self.extract_language_part(
            raw_articles[word], parser)
        expected = BeautifulSoup(expected_language_parts[word], 'lxml')
        expected_text = str(expected)
        # Need to remove the extra line break at the end of the file.
        # Line break is automatically added by editors when saving the files
        expected_text = expected_text
        observed_text = str(language_part)
        print('Expected text:\n{}\n'.format(expected_text))
        print('Observed text:\n{}\n'.format(observed_text))
        assert observed_text == expected_text

    @pytest.mark.parametrize('word,expected', [
        ('kuu', 3),
        ('sää', 2),
        ('luen', 1),
        ('koira', 1)])
    def test_does_return_correct_number_of_pos_parts(self, parser, raw_articles, word, expected):
        article = raw_articles[word]
        language_part = self.extract_language_part(article, parser)
        pos_parts = parser._extract_pos_parts(language_part)
        assert len(pos_parts) == expected

    def test_pos_extraction_fails_on_bad_formatting(self, parser):
        bad_html_lines = [
            '<h4><span class="mw-headline" id="Noun">Noun</span><\h4>',
            '<h3><span class="mw-headline" id="Verb">Noun</span><\h3>']
        bad_html = '\n'.join(bad_html_lines)
        with pytest.raises(ValueError):
            bad_soup = BeautifulSoup(bad_html, 'lxml')
            parser._extract_pos_parts(bad_soup)


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
