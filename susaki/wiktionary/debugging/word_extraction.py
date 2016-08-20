#############################
# Use this module to extract all the words that have resulted in a crash from
# the crash logs.
#############################

import os
import re

folder = '/home/simon/projects/python/SuSaKi/logs/crash'

pattern = r'"(.+)"'
crash_words = []
for f in os.listdir(folder):
    file_name = '/'.join([folder, f])
    with open(file_name, 'r') as log:
        word = re.search(pattern, next(log)).group(1)
        crash_words.append(word)
        print(word)
