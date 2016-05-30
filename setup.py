from setuptools import setup, find_packages


config = {
    'description': 'API to interface with the english witkionary when looking up Finnish words.',
    'author': 'Simon T. Clement',
    'author_email': 'simon.clement@gmail.com',
    'version': '0.1dev',
    'install_requires': ['requests', 'beautifulsoup4'],
    'packages': find_packages(exclude='*.tests'),
    'name': 'SuSaKi'}

setup(**config)
