'''
Created on Apr 28, 2016

@author: simon
'''
import pytest

from susaki.grammar.conjugation import VerbConjugator, KPTChanger, VerbTypeDetector


class TestVerbConjugator:

    def __init__(self):
        self.conjugator = VerbConjugator()

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

    def test_can_recognize_verb_type_1(self):
        assert False

    def test_can_recognize_verb_type_2(self):
        assert False

    def test_can_recognize_verb_type_3(self):
        assert False

    def test_can_recognize_verb_type_4(self):
        assert False

    def test_can_recognize_verb_type_5(self):
        assert False

    def test_can_recognize_verb_type_6(self):
        assert False

    def test_can_deal_with_verb_type_exceptions(self):
        assert False


class TestKPTChanger:

    def test_can_find_correct_strong_kpt_patterns(self):
        assert False

    def test_can_find_correct_weak_kpt_patterns(self):
        assert False

    def test_can_deal_with_diabolical_k(self):
        assert False
