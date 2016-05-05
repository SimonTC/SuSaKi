'''
Created on Apr 28, 2016

@author: simon
'''
import pytest
import yaml
import collections

import os
from distutils import dir_util

from susaki.grammar.conjugation import VerbConjugator, KPTChanger, VerbTypeDetector, SyllableDivisor


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


class TestVerbConjugator:

    @pytest.fixture()
    def verb_dictionary(self, datadir):
        verb_type_path = '/'.join([str(datadir), 'verbs.yml'])
        with open(verb_type_path) as filehandler:
            dict_ = yaml.load(filehandler)
        return dict_

    @pytest.fixture()
    def verb_conjugator(self):
        return VerbConjugator()

    @pytest.fixture(params=[1, 2, 3, 4, 5, 6])
    def type_dict(self, verb_dictionary, request):
        type_dict = verb_dictionary[request.param]
        return type_dict

    def test_can_conjugate_verb_types_correctly_in_present_tense(self, verb_conjugator, type_dict):
        for verb, conjugation_dict in type_dict.items():
            observed_conjugation = verb_conjugator.conjugate_verb(
                verb, 'present')
            for key, value in conjugation_dict.items():
                assert value == observed_conjugation[key]


class TestVerbTypeDetector:

    @pytest.fixture()
    def verb_type_dictionary(self, datadir):
        verb_type_path = '/'.join([str(datadir), 'verb_types.yml'])
        with open(verb_type_path) as filehandler:
            dict_ = yaml.load(filehandler)
        return dict_

    @pytest.fixture()
    def verb_type_detector(self):
        return VerbTypeDetector()

    @pytest.fixture(params=[1, 2, 3, 4, 5, 6])
    def verb_list(self, request, verb_type_dictionary):
        return request.param, verb_type_dictionary[request.param]

    def test_can_recognize_correct_verb_type(self, verb_list, verb_type_detector):
        verb_type, verbs = verb_list
        for verb in verbs:
            assert(verb_type_detector.detect_verb_type(verb) == verb_type)

    def test_return_negative_1_when_word_is_not_ending_in_correct_vowels(self, verb_type_detector):
        wrong_words = ['nukun', 'häkeän', 'ammaltiltaan', 'kirjoi']
        for word in wrong_words:
            assert(verb_type_detector.detect_verb_type(word) == -1)

    def test_can_deal_with_verb_type_exceptions(self):
        assert False


class TestKPTChanger:

    @pytest.fixture()
    def kpt_dictionary(self, datadir):
        dictionary_path = '/'.join([str(datadir), 'kpt_changes_strong.yml'])
        with open(dictionary_path) as filehandler:
            dict_ = yaml.load(filehandler)
        return dict_

    @pytest.fixture()
    def kpt_changer(self):
        return KPTChanger()

    def test_can_change_strong_to_weak(self, kpt_dictionary, kpt_changer):
        for strong, weak in kpt_dictionary.items():
            assert(kpt_changer.change_kpt(strong, to_strong=False) == weak)

    def test_can_change_weak_to_strong(self, kpt_dictionary, kpt_changer):
        for strong, weak in kpt_dictionary.items():
            changed_word = kpt_changer.change_kpt(weak, to_strong=True)
            if weak[-3:] in ['lje', 'rje']:
                # Ugly as hell but currently best way to see if it deals
                # correctly with the weak lje / rje words
                assert('[' in changed_word)
            elif weak == 'lue':
                # Won't test for diabolical k here
                pass
            else:
                assert(changed_word == strong)

    def test_can_deal_with_strong_to_weak_diabolical_k(self):
        assert False

    def test_can_deal_with_weak_to_strong_diabolical_k(self):
        assert False


class TestSyllableDivisor:

    def test_can_divide_words_correctly(self, datadir):
        syllable_dict_path = '/'.join([str(datadir), 'syllables.yml'])
        with open(syllable_dict_path) as filehandler:
            syllable_dict = yaml.load(filehandler)

        divisor = SyllableDivisor()

        for word, syllables in syllable_dict.items():
            assert(collections.Counter(syllables) ==
                   collections.Counter(divisor.divide_word(word)))
