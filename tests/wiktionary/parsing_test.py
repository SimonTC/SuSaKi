'''
Created on May 16, 2016

@author: simon
'''
import pytest
import os
from distutils import dir_util
from susaki.wiktionary.parsing import HTMLParser

from bs4 import BeautifulSoup
from lxml import etree


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


def load_text_files(datadir, sub_folder, extension, to_soup=False, remove_whitespace=False):
    article_dict = {}
    article_dir = '{}/{}'.format(str(datadir), sub_folder)
    for article in os.listdir(article_dir):
        if article.endswith('.{}'.format(extension)):
            article_name = os.path.splitext(article)[0]
            article_path = '/'.join([str(article_dir), article])
            with open(article_path, 'r') as f:
                lines = f.readlines()
                if remove_whitespace:
                    clean_lines = []
                    for l in lines:
                        l = l.replace('\n', '')
                        l = l.strip()
                        clean_lines.append(l)
                    lines = clean_lines
                content = ''.join(lines)
                if to_soup:
                    content = BeautifulSoup(content, 'html.parser')
                article_dict[article_name] = content
    return article_dict


def load_html_pages(datadir, sub_folder, to_soup=False):
    return load_text_files(datadir, sub_folder, 'html', to_soup)


@pytest.fixture(scope='module')
def raw_articles(datadir):
    return load_html_pages(datadir, 'raw_pages')


@pytest.fixture(scope='module')
def expected_language_parts(datadir):
    return load_html_pages(datadir, 'expected_language_parts', to_soup=True)


@pytest.fixture(scope='module')
def expected_pos_parts(datadir):
    return load_html_pages(datadir, 'expected_pos_parts', to_soup=True)


@pytest.fixture(scope='module')
def translation_extraction_output(datadir):
    return load_html_pages(datadir, 'translation_extraction_data', to_soup=False)


@pytest.fixture(scope='module')
def inflection_extraction_data(datadir):
    return load_html_pages(datadir, 'inflection_extraction_data', to_soup=False)


@pytest.fixture(scope='module')
def translation_parsing_data(datadir):
    html_dict = load_text_files(datadir, 'translation_parsing_data', extension='html')
    xml_dict = load_text_files(datadir, 'translation_parsing_data', extension='xml', remove_whitespace=True)
    combined_dicts = {**html_dict, **xml_dict}
    return combined_dicts


@pytest.fixture(scope='module')
def example_parsing_data(datadir):
    html_dict = load_text_files(datadir, 'example_parsing_data', extension='html')
    xml_dict = load_text_files(datadir, 'example_parsing_data', extension='xml', remove_whitespace=True)
    combined_dicts = {**html_dict, **xml_dict}
    return combined_dicts


@pytest.fixture(scope='module')
def inflection_parsing_data(datadir):
    html_dict = load_text_files(datadir, 'inflection_parsing_data', extension='html')
    xml_dict = load_text_files(datadir, 'inflection_parsing_data', extension='xml', remove_whitespace=True)
    combined_dicts = {**html_dict, **xml_dict}
    return combined_dicts


@pytest.fixture
def parser():
    return HTMLParser()


class TestLanguageExtraction:

    def extract_language_part(self, article, parser):
        soup = BeautifulSoup(article, 'html.parser')
        language_part = parser._extract_language_part(soup, 'Finnish')
        return language_part

    def output_is_as_expected(self, word, parser, expected_language_parts, raw_articles):
        raw = raw_articles[word]
        expected_output_soup = expected_language_parts[word]
        observed_output = self.extract_language_part(raw, parser)
        as_expected = expected_output_soup == observed_output
        if not as_expected:
            print('Observed:\n{}'.format(observed_output))
            print('Expected:\n{}'.format(expected_output_soup))
        return as_expected

    def test_extract_correctly_when_only_language_in_article_with_table_of_contents(self, parser, expected_language_parts, raw_articles):
        word = 'että'
        assert self.output_is_as_expected(word, parser, expected_language_parts, raw_articles)

    def test_extract_correctly_when_only_language_in_article_without_table_of_contents(self, parser, expected_language_parts, raw_articles):
        word = 'kuussa'
        assert self.output_is_as_expected(word, parser, expected_language_parts, raw_articles)

    def test_extract_correctly_when_first_language_in_article(self, parser, expected_language_parts, raw_articles):
        word = 'koira'
        assert self.output_is_as_expected(word, parser, expected_language_parts, raw_articles)

    def test_extract_correctly_when_last_language_in_article(self, parser, expected_language_parts, raw_articles):
        word = 'luen'
        assert self.output_is_as_expected(word, parser, expected_language_parts, raw_articles)

    def test_extract_correctly_when_between_other_languages(self, parser, expected_language_parts, raw_articles):
        word = 'ilma'
        assert self.output_is_as_expected(word, parser, expected_language_parts, raw_articles)

    def test_throw_exception_when_language_not_present_in_article(self, parser, raw_articles):
        with pytest.raises(KeyError) as exinfo:
            self.extract_language_part(
                raw_articles['hello'], parser)
        assert 'No explanations exists for the language:' in str(exinfo)


class TestPOSExtraction:

    def output_is_as_expected(self, word, parser, expected_pos_parts, expected_language_parts):
        counter = 0
        language_part = expected_language_parts[word]
        observed_output_list = parser._extract_pos_parts(language_part)
        while True:
            try:
                pos_part = '{}_{}'.format(word, counter)
                print('Testing pos part {}'.format(pos_part))
                expected_output = expected_pos_parts[pos_part]
            except KeyError:
                # Don't need to test if extractor has extracted more than expected
                # since this is already tested in other test.
                return True

            observed_output = observed_output_list[counter]
            if expected_output != observed_output:
                print('The expected output is not as the observed output')
                print('Expected output:\n{}'.format(expected_output.prettify()))
                print('\nObserved output:\n{}'.format(observed_output.prettify()))
                return False
            counter += 1

    def extract_pos_parts(self, language_part, parser):
        soup = BeautifulSoup(language_part, 'lxml')
        pos_parts = parser._extract_pos_parts(soup)
        return pos_parts

    @pytest.mark.parametrize('word,expected', [
        ('kuu', 3),
        ('sää', 2),
        ('luen', 1),
        ('koira', 1),
        ('päästä', 3)])
    def test_does_return_correct_number_of_pos_parts(self, parser, expected_language_parts, word, expected):
        language_part = expected_language_parts[word]
        pos_parts = parser._extract_pos_parts(language_part)
        assert len(pos_parts) == expected

    def test_extract_correctly_when_no_etymology_tags(self, parser, expected_pos_parts, expected_language_parts):
        word = 'ilman'
        assert self.output_is_as_expected(word, parser, expected_pos_parts, expected_language_parts)

    def test_extract_correctly_when_only_single_POS(self, parser, expected_pos_parts, expected_language_parts):
        word = 'ilma'
        assert self.output_is_as_expected(word, parser, expected_pos_parts, expected_language_parts)

    def test_extract_correctly_when_multiple_identical_POS_tags(self, parser, expected_pos_parts, expected_language_parts):
        word = 'kuu'
        assert self.output_is_as_expected(word, parser, expected_pos_parts, expected_language_parts)

    def test_extract_correctly_when_multiple_different_POS_tags(self, parser, expected_pos_parts, expected_language_parts):
        word = 'päästä'
        assert self.output_is_as_expected(word, parser, expected_pos_parts, expected_language_parts)

    def test_raise_error_if_POS_tags_on_different_levels(self, parser):
        bad_html_lines = [
            '<h4><span class="mw-headline" id="Noun">Noun</span><\h4>',
            '<h3><span class="mw-headline" id="Verb">Noun</span><\h3>']
        bad_html = '\n'.join(bad_html_lines)
        with pytest.raises(ValueError) as error:
            bad_soup = BeautifulSoup(bad_html, 'lxml')
            parser._extract_pos_parts(bad_soup)
        assert str(error.value) == 'The POS-parts are placed at different header levels'

    def test_raise_error_if_no_POS_tags_present(self, parser):
        bad_html_lines = [
            '<h4><span class="mw-headline" id="Bob">Bob</span><\h4>',
            '<h4><span class="mw-headline" id="Kimmie">Kimmie</span><\h4>']
        bad_html = '\n'.join(bad_html_lines)
        with pytest.raises(ValueError) as error:
            bad_soup = BeautifulSoup(bad_html, 'lxml')
            parser._extract_pos_parts(bad_soup)
        assert str(error.value) == 'No POS-parts present'


class TestTranslationExtraction:
    # TODO: Make testing of translation better. The need for splitting lines
    # is not good

    def output_items_is_as_expected(self, parser, input_, expected_output_items):
        observed_output_items = parser._extract_translations(input_)
        for observed, expected in zip(observed_output_items, expected_output_items):
            expected_str = str(expected)
            observed_str = str(observed)
            if expected_str != observed_str:
                print('Observed: \n{}'.format(observed))
                print('Expected: \n{}'.format(expected))
                return False
        return True

    def throws_error(self, parser, soup, err_type, expected_err_message):
        with pytest.raises(err_type) as error:
            parser._extract_translations(soup)
        return str(error.value) == expected_err_message

    @pytest.mark.parametrize('word,expected_count', [
        ('ilma_0', 2),
        ('ilman_1', 1),
        ('kuu_0', 2),
        ('päästä_0', 9),
        ('päästä_1', 1)])
    def test_extract_expected_number_of_translations(self, parser, expected_pos_parts, word, expected_count):
        pos_part = expected_pos_parts[word]
        translations = parser._extract_translations(pos_part)
        num_translations = len(translations)
        assert num_translations == expected_count

    def test_raise_error_if_no_translations(self, parser, translation_extraction_output):
        no_translation_list = translation_extraction_output['no_translation_list']
        no_translation_list_soup = BeautifulSoup(no_translation_list, 'html.parser')
        no_translation_list_items = translation_extraction_output['no_translation_list_items']
        no_translation_list_items_soup = BeautifulSoup(no_translation_list_items, 'html.parser')
        expected_err_message = 'No translations present'
        expected_err_type = ValueError
        assert self.throws_error(parser, no_translation_list_soup, expected_err_type, expected_err_message)
        assert self.throws_error(parser, no_translation_list_items_soup, expected_err_type, expected_err_message)

    def test_extract_correctly_if_only_one_translation(self, parser, translation_extraction_output, expected_pos_parts):
        input_ = expected_pos_parts['ilman_1']
        expected_output = translation_extraction_output['only_one_translation']
        expected_output_items = expected_output.split('{SPLIT}')
        assert self.output_items_is_as_expected(parser, input_, expected_output_items)

    def test_extract_correctly_if_multiple_translations(self, parser, translation_extraction_output, expected_pos_parts):
        input_ = expected_pos_parts['päästä_0']
        expected_output = translation_extraction_output['multiple_translations']
        expected_output_items = expected_output.split('{SPLIT}\n')
        assert self.output_items_is_as_expected(parser, input_, expected_output_items)

    def test_extract_correctly_when_pos_part_also_contains_items_other_than_translations(self, parser, translation_extraction_output, expected_pos_parts):
        input_ = expected_pos_parts['päästä_0']
        expected_output = translation_extraction_output['not_only_translations']
        expected_output_items = expected_output.split('{SPLIT}\n')
        assert self.output_items_is_as_expected(parser, input_, expected_output_items)

    def test_extract_correctly_when_pos_part_only_contains_translations(self, parser, translation_extraction_output, expected_pos_parts):
        input_ = expected_pos_parts['ilman_1']
        expected_output = translation_extraction_output['only_translations']
        expected_output_items = expected_output.split('{SPLIT}\n')
        assert self.output_items_is_as_expected(parser, input_, expected_output_items)


class HTML_To_XML_Parsing:
    def output_is_as_expected(self, parsing_function, input_text, expected_output_text):
        input_soup = BeautifulSoup(input_text, 'html.parser')
        expected_output = etree.fromstring(expected_output_text)
        observed_output = parsing_function(input_soup)
        observed_output_string = etree.tostring(observed_output, encoding='unicode', pretty_print=True)
        expected_output_string = etree.tostring(expected_output, encoding='unicode', pretty_print=True)
        print('Observed\n{}'.format(observed_output_string))
        print('Expected\n{}'.format(expected_output_string))
        return observed_output_string == expected_output_string


class TestTranslationParsing(HTML_To_XML_Parsing):
    # def output_is_as_expected(self, parser, input_text, expected_output_text):
    #     input_soup = BeautifulSoup(input_text, 'html.parser')
    #     expected_output = etree.fromstring(expected_output_text)
    #     observed_output = parser._parse_translation(input_soup)
    #     observed_output_string = etree.tostring(observed_output)
    #     expected_output_string = etree.tostring(expected_output)
    #     print('Observed\n{}'.format(observed_output_string))
    #     print('Expected\n{}'.format(expected_output_string))
    #     return observed_output_string == expected_output_string

    def test_parse_correctly_with_no_examples(self, parser, translation_parsing_data):
        input_text = translation_parsing_data['input_no_examples']
        expected_output_text = translation_parsing_data['output_no_examples']
        assert self.output_is_as_expected(parser._parse_translation, input_text, expected_output_text)

    def test_parse_correctly_if_one_example(self, parser, translation_parsing_data):
        input_text = translation_parsing_data['input_one_example']
        expected_output_text = translation_parsing_data['output_one_example']
        assert self.output_is_as_expected(parser._parse_translation, input_text, expected_output_text)

    def test_parse_correctly_with_multiple_examples(self, parser, translation_parsing_data):
        input_text = translation_parsing_data['input_multiple_examples']
        expected_output_text = translation_parsing_data['output_multiple_examples']
        assert self.output_is_as_expected(parser._parse_translation, input_text, expected_output_text)


class TestExampleParsing(HTML_To_XML_Parsing):

    def test_parse_correctly_if_example_and_its_translation_are_on_same_line(self, parser, example_parsing_data):
        input_text = example_parsing_data['input_same_line_list']
        expected_output_text = example_parsing_data['output_same_line']
        assert self.output_is_as_expected(parser._parse_example, input_text, expected_output_text)

    def test_parse_correctly_if_example_and_its_translation_are_on_different_lines(self, parser, example_parsing_data):
        input_text = example_parsing_data['input_two_lines']
        expected_output_text = example_parsing_data['output_two_lines']
        assert self.output_is_as_expected(parser._parse_example, input_text, expected_output_text)

    def test_parse_correctly_if_example_is_made_as_quotation(self, parser, example_parsing_data):
        input_text = example_parsing_data['input_quotation']
        expected_output_text = example_parsing_data['output_quotation']
        assert self.output_is_as_expected(parser._parse_example, input_text, expected_output_text)


class TestInflectionTableExtraction:

    def test_raise_error_if_no_inflection_table(self, parser, inflection_extraction_data):
        input_html = inflection_extraction_data['input_no_table']
        input_soup = BeautifulSoup(input_html, 'html.parser')
        with pytest.raises(ValueError) as error:
            parser._extract_inflection_table(input_soup)
        assert str(error.value) == 'No inflection table present'

    @pytest.mark.parametrize('html_title', ['input_verb_table', 'input_noun_table'])
    def test_extraction_function_returns_only_table_element(self, parser, inflection_extraction_data, html_title):
        input_html = inflection_extraction_data['input_verb_table']
        input_soup = BeautifulSoup(input_html, 'html.parser')
        observed_output = parser._extract_inflection_table(input_soup)
        assert observed_output.name == 'table'


class TestInflectionParsing(HTML_To_XML_Parsing):

    # @pytest.mark.parametrize('table_type', [
    #     'verb_table',
    #     'noun_table_with_gradation',
    #     'noun_table_without_gradation'])
    @pytest.mark.parametrize('table_type', ['verb_table'])
    def test_parse_inflection_table_correctly(self, parser, inflection_parsing_data, table_type):
        input_text = inflection_parsing_data['input_{}'.format(table_type)]
        expected_output_text = inflection_parsing_data['output_{}'.format(table_type)]
        assert self.output_is_as_expected(parser._parse_inflection_table, input_text, expected_output_text)


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

    @pytest.mark.xfail
    def test_output_dict_formatted_correctly(self):
        assert False


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
