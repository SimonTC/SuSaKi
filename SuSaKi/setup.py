try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


config = {
    'description': 'API to interface with the english witkionary when looking up Finnish words.',
    'author': 'Simon T. Clement',
    'author_email': 'simon.clement@gmail.com',
    'version': '0.1',
    'install_requires': [],
    'packages': ['susaki'],
    'scripts': [],
    'name': 'SuSaKi'}

setup(**config)
