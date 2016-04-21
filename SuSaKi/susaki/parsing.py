'''
Created on Apr 21, 2016

@author: simon
'''


class Article:

    def __init__(self, word, language, definitions=[]):
        self.word = word
        self.language = language
        self.definitions = definitions

    def add_definition(self, definition):
        self.definitions.append(definition)


class Definition:

    def __init__(self, pos):
        self.pos = pos
        self.explanations = []

    def add_explanation(self, explanation):
        self.explanations.append(explanation)


class Explanation:

    def __init__(self, explanation):
        self.explanation = explanation
        self.examples = []

    def add_example(self, example):
        self.examples.append(example)
