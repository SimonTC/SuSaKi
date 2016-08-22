import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
CRASH_DIR = os.path.join(LOG_DIR, 'crash')
QUERY_DIR = os.path.join(LOG_DIR, 'query')
