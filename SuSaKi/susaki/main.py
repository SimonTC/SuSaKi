'''
Created on Apr 20, 2016

@author: simon
'''

import requests
import re
from bs4 import BeautifulSoup
import argparse
from requests.exceptions import HTTPError


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
        etymology_list = None
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


def process_user_query(word, language):
    try:
        req = collect_page(word)
    except HTTPError:
        print('"{}" does not seem to have a page on Wiktionary'.format(word))
    else:
        etymology_list = extract_etymologies(req.json(), language=language)
        if not etymology_list:
            print(
                '"{}" does not seem to exists as a word in the {}-en dictionary'.format(word, language))
        else:
            print_information(word, etymology_list)


def run(language):
    greet_user(language)
    while True:
        command = input('>> ')
        if command.lower() == 'close()' or command.lower() == 'exit()':
            break
        elif command.lower() == 'help()':
            greet_user(language)
        else:
            word = command
            process_user_query(word, language)
        print()


def greet_user(language):
    print('*********************************************')
    print(
        'Welcome to SuSaKi - a simple tool to access the online user generated dictionary Wikitionary.')
    print('You are currently accessing the en-{} dictionary.'.format(language))
    print(
        'To look up a word and its meaning in English just write it an press Enter.')
    print('To exit this program write "close()" or "exit()" and press Enter')
    print('To show this message again write "help()" and press Enter')
    print('*********************************************')

if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Look for translations into English on wiktionary')
    parser.add_argument(
        "-l", "--language", help="The language you want translations from", default="fi")
    args = parser.parse_args()
    language = args.language
    run(language)
