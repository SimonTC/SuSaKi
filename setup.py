from setuptools import setup, find_packages


config = {
    'description': 'API to interface with the english witkionary when looking up Finnish words.',
    'author': 'Simon T. Clement',
    'author_email': 'simon.clement@gmail.com',
    'version': '0.3dev',
    'install_requires': ['requests', 'beautifulsoup4', 'lxml'],
    'packages': find_packages(exclude='*.tests'),
    'name': 'SuSaKi'}

setup(**config)
