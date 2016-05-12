'''
Created on Apr 21, 2016

@author: simon
'''


class Article:
    """
    The article holds all the information about a single word in a given language
    """

    def __init__(self, word, language):
        self.word = word
        self.language = language
        self.definitions = []

    def add_definition(self, definition):
        self.definitions.append(definition)


class Definition:
    """
    One definition of a word.
    """

    def __init__(self, pos):
        """
        pos: Part of speech (fx Noun, adjective)
        """
        self.pos = pos
        self.translations = []

    def add_translation(self, translation):
        self.translations.append(translation)


class Translation:
    """
    A single translation of a word.
    """

    def __init__(self, translation):
        self.translation = translation
        self.examples = []

    def add_example(self, example):
        self.examples.append(example)
