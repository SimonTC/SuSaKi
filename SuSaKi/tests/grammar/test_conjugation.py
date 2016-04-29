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

    def test_can_conjugate_verb_type_1_correctly_in_present_tense(self):
        assert False

    def test_can_conjugate_verb_type_2_correctly_in_present_tense(self):
        assert False

    def test_can_conjugate_verb_type_3_correctly_in_present_tense(self):
        assert False

    def test_can_conjugate_verb_type_4_correctly_in_present_tense(self):
        assert False

    def test_can_conjugate_verb_type_5_correctly_in_present_tense(self):
        assert False

    def test_can_conjugate_verb_type_6_correctly_in_present_tense(self):
        assert False


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

    def test_can_find_correct_strong_kpt_patterns(self):
        assert False

    def test_can_find_correct_weak_kpt_patterns(self):
        assert False

    def test_can_deal_with_diabolical_k(self):
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
