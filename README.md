# SuSaKi
SuSaKi is an attempt at creating a program to parse Wiktionary's articles on Finnish words.
It connects to Wiktionary using Wiktionary's API and is capable of returning a machine readable version of an article containing:
* Translations
* Examples (if they exist)
* Conjugations / declensions of the Finnish word *

\* This feature doesn't always work since not all conjugation / declension tables are formatted the same way

Be aware that it is still under active development and is still rough around the edges. The dictionary part does however work quite well.


## Try it out
Currently only the dictionary part of the program has been implemented in demo modules.
### Dictionary
Running susaki/wiktionary/examples/dictionary.py from your terminal will start a terminal dictionary which you can use to look up English translations of Finnish words. In case no article exist for a particular word, the program will inform you of other search terms where that might be related to the word you are looking for.

### List translator
Running susaki/wiktionary/examples/translate.py with a text file as parameter will translate all words in the text file (one search term per line) and create a new file with the pairs of Finnish and English words.
