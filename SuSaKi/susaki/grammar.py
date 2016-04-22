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


def verb_type(verb):
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


if __name__ == '__main__':
    verb = 'pudetl'
    print(verb_type(verb))
