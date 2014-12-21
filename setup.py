#! /usr/bin/env python
from setuptools import setup
from os import path

import pypandoc

here = path.abspath(path.dirname(__file__))

readme_fname = path.join(here, 'README.md')
long_description = pypandoc.convert(readme_fname, 'rst')

setup(
    # Project metadata
    name='simpleactors',
    version=open(path.join(here, 'VERSION')).read().strip(),
    license='GPLv3+',
    description='An extremely simple implementation of the Actor model',
    long_description=long_description,
    url='https://github.com/quasipedia/simpleactors',

    # Author details
    author='Mac Ryan',
    author_email='quasipedia@gmail.com',

    # Classifiers & Keywords
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='actor model actor-model development framework lightweight',

    # Package contents
    py_modules=['simpleactors'],

    # Dependencies
    extras_require={
        'dev': ['pypandoc', 'wheel>=0.24.0', 'twine'],
        'test': ['nose', 'rednose', 'coverage'],
    },
)
