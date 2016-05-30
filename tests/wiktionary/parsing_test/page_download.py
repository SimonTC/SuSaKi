# Use this script to download pages to be used when testing
# the parser
import os
import shutil
from susaki.wiktionary.connectors import APIConnector


current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = '{}/raw_pages'.format(current_dir)
connector = APIConnector()
for file_name in os.listdir(str(current_dir)):
    if file_name.endswith('.html'):
        file_path = '{}/{}'.format(current_dir, file_name)
        word = os.path.splitext(file_name)[0]
        print('Downloading {}'.format(word))
        shutil.move(file_name, '{}.bak'.format(file_path))
        with open (file_path, 'w') as f:
            content = connector.collect_raw_article(word)
            f.write(content)

for file_name in os.listdir(str(current_dir)):
    if file_name.endswith('.bak'):
        print('Deleting {}'.format(file_name))
        file_path = '{}/{}'.format(current_dir, file_name)
        os.remove(file_path)
