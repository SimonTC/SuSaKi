'''
Created on Apr 22, 2016

@author: simon
'''

import re
import logging
from collections import namedtuple

VerbTypePattern = namedtuple("VerbTypePattern", "pattern, verb_type")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

vowels = 'eyuioaöä'
consonants = 'qwrtipsdfghjklzxcvbnm'


class SyllableDivisor:

    def divide_word(self, word):
        """Divide the word into syllables using the rules from
        http://people.uta.fi/~km56049/finnish/syldiv.html
        """
        syllable_indicator = ''
        syllable_letters = ''
        syllable = ''
        for i, letter in enumerate(word):
            if syllable_indicator == '':
                if letter in vowels:
                    syllable_indicator += 'V'
                    syllable_letters += letter
            else:
                syllable_letters += letter
                if letter in vowels:
                    syllable_indicator += 'V'
                else:
                    syllable_indicator += 'C'
            if syllable_indicator in ['VCV', 'VCCV', 'VCCCV']:
                syllable = word[:i - 1]
                rest = word[i - 1:]
                break
            elif syllable_indicator == 'VV':
                diphtong_pattern = re.compile(
                    r'([aeiouyäö]i)|([aeiu]u)|([eiäö]y)|ie|uo|yö')
                long_sound_pattern = re.compile(r'aa|ee|yy|uu|ii|oo|ää|öö')

                if not (diphtong_pattern.match(syllable_letters) or long_sound_pattern.match(syllable_letters)):
                    syllable = word[:i]
                    rest = word[i:]
                    break
                else:
                    syllable_indicator = syllable_indicator[-1]
                    syllable_letters = syllable_letters[-1]

        if syllable != '':
            syllable_list = [syllable]
            syllable_list += self.divide_word(rest)
        else:
            syllable_list = [word]
        return syllable_list


class VerbConjugator():

    strong_kpt_patterns = [r'(lke|lki|rke|rki|hke|uku|yky)',
                           r'(lk|kk|tt|pp|nk|lp|rp|mp|ht|lt|rt|nt|rk)',
                           r'((?!([hst]))(?:k)|(?:p)|(?!s)(?:t))']

    weak_kpt_patterns = [r'(lje|lje|rje|rje|hje|uvu|yvy)',
                         r'(ng|lv|rv|mm|hd|ll|rr|nn)',
                         r'((?!([hst]))(?:k)|(?:p)|(?:(?!s)(?:t))|v|d|r|l)']

    post_pattern_dict = {1: r'(?=[eyuioaöä]$)',
                         2: r'$)',
                         3: r'(?='}

    pre_pattern = r'(?=\w*?)'
    post_pattern = r'(?=[aeouiyäö]*$)'

    #pattern_strong = r'(?=\w*?)((?:lke|lki|rke|rki|hke|uku|yky)|(?:lk|kk|tt|pp|nk|lp|rp|mp|ht|lt|rt|nt|rk)|(?:[^hst](?:k)|(?:p)|[^s](?:t)))(?=[aeouiyäö]+$)'

    KPT_dict_strong = {
        'kk': 'k',
        'pp': 'p',
        'tt': 't',
        'k': '',
        'p': 'v',
        't': 'd',
        'rt': 'rr',
        'lt': 'll',
        'nt': 'nn',
        'nk': 'ng',
        'mp': 'mm',
        'lp': 'lv',
        'tp': 'rv',
        'ht': 'hd',
        'rk': 'r',
        'lke': 'lje',
        'lki': 'lje',
        'rke': 'rje',
        'rki': 'rje',
        'hke': 'hje',
        'uku': 'uvu',
        'yky': 'yvy',
        'lk': 'l'}

    def __init__(self):
        self._setup_weak_kpt_dict()
        self.syllable_divisor = SyllableDivisor()
#         with open('dict.txt', 'w') as filehandler:
#             json.dump(self.KPT_dict_strong, filehandler)

    def _setup_weak_kpt_dict(self):
        """ Create the weak kpt dict as a mirror of the string kpt dict"""
        self.KPT_dict_weak = {
            value: key for key, value in self.KPT_dict_strong.items()}

    def conjugate_verb(self, verb, tense):
        """ Conjugate the verb in the given tense"""
        verb_type = self.verb_type(verb)
        if tense == 'present':
            return self._conjugate_present(verb, verb_type)

    def _find_kpt_pattern(self, word, pattern_list):
        """ 
        Using the prioritized list of patterns, return the first 
        match together with its corresponding kpt_pattern.
        The letters in the match has to be near the border between the last two syllables.
        """
        for kpt_pattern in pattern_list:
            search_pattern = '{}{}{}'.format(
                self.pre_pattern, kpt_pattern, self.post_pattern)
            match = re.search(search_pattern, word)
            if match:
                return match, search_pattern
        return None, None

    def _extract_stem(self, naive_stem, to_strong):
        """
        Extract the stem from the naive stem.
        naive_stem: the stem of a word without kpt-changes
        to_strong: boolean indicating if the naive stem should be changed from weak to strong (True)
                   or from strong to weak (False)
        """

        if to_strong:
            kpt_pattern_list = self.weak_kpt_patterns
            kpt_pattern_dict = self.KPT_dict_weak
            stem_type = 'strong'
        else:
            kpt_pattern_list = self.strong_kpt_patterns
            kpt_pattern_dict = self.KPT_dict_strong
            stem_type = 'weak'

        logger.debug(
            'Extracting the {} infinitive stem using the naïve stem {}'.format(stem_type, naive_stem))
        match, pattern = self._find_kpt_pattern(naive_stem, kpt_pattern_list)
        if match:
            kpt_group = match.group(0)
            logger.debug(
                'Found KPT-group {} using pattern {}'.format(kpt_group, pattern))
            replacement = kpt_pattern_dict[kpt_group]
            logger.debug(
                'Replacement for {} is {}'.format(kpt_group, replacement))
            correct_stem = re.sub(pattern, replacement, naive_stem)
            logger.debug(
                'The correct stem of {} is {}'.format(naive_stem, correct_stem))
        else:
            logger.debug('No kpt-changes in {}'.format(naive_stem))
            correct_stem = naive_stem
        return correct_stem

    def _infinitive_stem(self, verb, verb_type, to_strong):
        """
        Extract the infinite stem of the verb
        if to_strong == True the strong stem will be extracted.
        Otherwise the weak stem is extracted.
        """
        if verb_type == 1:
            naive_stem = verb[:-1]
            logger.debug('Naïve stem is {}'.format(naive_stem))
            if not to_strong:
                stem = self._extract_stem(naive_stem, to_strong)
            else:
                stem = naive_stem
        elif verb_type == 2:
            stem = verb[:-2]
        elif verb_type == 3:
            # We also remove the last 'l' since if we keep it it messes up the
            # KPT-changes
            naive_stem = verb[:-3]
            stem = self._extract_stem(naive_stem, to_strong=True)
            stem = stem + 'l'
        elif verb_type == 4:
            naive_stem = re.sub(r't(?=.$)', '', verb)
            stem = self._extract_stem(naive_stem, to_strong=True)
        elif verb_type == 5:
            stem = verb[:-1] + 'se'
        elif verb_type == 6:
            naive_stem = verb[:-2]
            stem = self._extract_stem(naive_stem, to_strong=True)
            stem = stem + 'ne'

        return stem

    def _letters_exists_in_word(self, letter_set, word):
        for letter in letter_set:
            if letter in word:
                return True
        return False

    def _conjugate_present(self, verb, verb_type):
        """Conjugate the given verb in its present form"""
        conjugation_dict = {}
        if self._letters_exists_in_word({'a', 'o', 'u'}, verb):
            he = 'vat'
        else:
            he = 'vät'
        if verb_type == 1:
            weak_stem = self._infinitive_stem(verb, verb_type, to_strong=False)
            strong_stem = self._infinitive_stem(
                verb, verb_type, to_strong=True)
            conjugation_dict = {'minä': weak_stem + 'n',
                                'sinä': weak_stem + 't',
                                'hän': strong_stem + strong_stem[-1],
                                'me': weak_stem + 'mme',
                                'te': weak_stem + 'tte',
                                'he': strong_stem + he}
        elif verb_type == 2:
            stem = self._infinitive_stem(verb, verb_type, to_strong=True)
            conjugation_dict = {'minä': stem + 'n',
                                'sinä': stem + 't',
                                'hän': stem,
                                'me': stem + 'mme',
                                'te': stem + 'tte',
                                'he': stem + he}
        elif verb_type == 3:
            stem = self._infinitive_stem(verb, verb_type, to_strong=True)
            conjugation_dict = {'minä': stem + 'en',
                                'sinä': stem + 'et',
                                'hän': stem + 'ee',
                                'me': stem + 'emme',
                                'te': stem + 'ette',
                                'he': stem + 'e' + he}
        elif verb_type == 4:
            stem = self._infinitive_stem(verb, verb_type, to_strong=True)
            last_vowel = stem[-1]
            if stem[-2] == last_vowel:
                last_vowel = ''
            conjugation_dict = {'minä': stem + 'n',
                                'sinä': stem + 't',
                                'hän': stem + last_vowel,
                                'me': stem + 'mme',
                                'te': stem + 'tte',
                                'he': stem + he}
        elif verb_type == 5:
            stem = self._infinitive_stem(verb, verb_type, to_strong=True)
            last_vowel = stem[-1]
            conjugation_dict = {'minä': stem + 'n',
                                'sinä': stem + 't',
                                'hän': stem + last_vowel,
                                'me': stem + 'mme',
                                'te': stem + 'tte',
                                'he': stem + he}
        elif verb_type == 6:
            stem = self._infinitive_stem(verb, verb_type, to_strong=True)
            last_vowel = stem[-1]
            conjugation_dict = {'minä': stem + 'n',
                                'sinä': stem + 't',
                                'hän': stem + last_vowel,
                                'me': stem + 'mme',
                                'te': stem + 'tte',
                                'he': stem + he}

        logger.debug(conjugation_dict)
        return conjugation_dict

    def verb_type(self, verb):
        """
        Reads the given verb and returns the verb type.
        Does not take irregularities into account (verbs that belong to the 'wrong' verb type.
        The verb must be in its infinitive form.
        Verb rules taken from http://people.uta.fi/~km56049/finnish/verbs.html
        """
        logger.debug('Get verb type for {}'.format(verb))
        verb_type_pattern_list = [
            VerbTypePattern(r'[aeiouyäö][aä]$', 1),
            VerbTypePattern(r'd[aä]$', 2),
            VerbTypePattern(r'(?:[lnr]|st)[aä]$', 3),
            VerbTypePattern(r'[aouyäö]t[aä]$', 4),
            VerbTypePattern(r'it[aä]$', 5),
            VerbTypePattern(r'et[aä]$', 6)
        ]

        for verb_type_pattern in verb_type_pattern_list:
            logger.debug(
                'Checking verb type {1} using pattern {0}'.format(*verb_type_pattern))
            if re.search(verb_type_pattern.pattern, verb):
                return verb_type_pattern.verb_type
        return -1


def print_conjugation(conjugation_dict):
    string = 'Minä {minä}\nSinä {sinä}\nHän {hän}\nMe {me}\nTe {te}\nHe {he}'.format(
        **conjugation_dict)
    print(string)

if __name__ == '__main__':
    verb = 'pidetä'
    conjugator = VerbConjugator()
    conjugation_dict = conjugator.conjugate_verb(verb, 'present')
    print(conjugation_dict)
    print_conjugation(conjugation_dict)
    word = 'kirjoitta'
    divisor = SyllableDivisor()
    print(divisor.divide_word(word))
