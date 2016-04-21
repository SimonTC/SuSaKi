'''
Created on Apr 20, 2016

@author: simon
'''

import json
import requests
from pprint import pprint
import re
from bs4 import BeautifulSoup
import argparse


def collect_page(word):
    url = 'https://en.wiktionary.org/api/rest_v1/page/definition/{}'.format(
        word)
    req = requests.get(url)
    req.raise_for_status()  # Test for bad response
    return req


def extract_etymologies(json_page, language='fi'):
    try:
        etymology_list = json_page[language]
    except:
        pass
    return etymology_list


def clean_line(line):
    # Apparently we have to soup twice before it recognizes the tags
    soup = BeautifulSoup(line, 'html.parser')
    soup = BeautifulSoup(soup.get_text(), 'html.parser')
    for tag in soup.findAll(True):
        tag.unwrap()
    text = soup.get_text()
    text = re.sub(r'  +', ' ', text)
    return text


def print_etymology_information(etymology_dict):
    print(etymology_dict['partOfSpeech'])
    definitions = etymology_dict['definitions']
    for definition in definitions:
        print(' ' + clean_line(definition['definition']))

    print()


def print_information(word, etymology_list):
    print('Search term: {}'.format(word))
    print()
    for etymology in etymology_list:
        print_etymology_information(etymology)


def run(language='fi'):
    while True:
        command = input('>> ')
        if command.lower() == 'close()':
            break
        word = command
        req = collect_page(word)
        etymology_list = extract_etymologies(req.json(), language=language)
        print_information(word, etymology_list)
        print()


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    parser.add_argument(
        "-l", "--language", help="The language you want translations from", default="fi")
    args = parser.parse_args()
    language = args.language
    run(language)
