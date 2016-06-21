#!/usr/bin/env python
from os.path import dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

curr_dir = dirname(__file__)

#               YYYY.MM.DD
release_date = "2016.07.XX"
version = (0, 9, 0)

try:
    long_desc = open(join(curr_dir, "readme.rst")).read()
except Exception:
    long_desc = ''

setup(
    name='supyr_struct',
    description='A versatile and extensible binary data parsing/serializing library for Python 3',
    long_description=long_desc,
    version='0.9.0',
    url='http://bitbucket.org/wcfw/supyr_struct',
    author='MosesofEgypt',
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'supyr_struct',
        'supyr_struct.blocks',
        'supyr_struct.defs',
        'supyr_struct.defs.bitmaps',
        'supyr_struct.defs.crypto',
        'supyr_struct.defs.executables',
        'supyr_struct.defs.tests',
        'supyr_struct.editor',
        ],
    package_data={
        '': ['*.txt', '*.rst'],
        'supyr_struct':['tags/images/*.*',
                        'tags/keyblobs/*.*'
                        ]
        },
    platforms=["POSIX", "Windows"],
    keywords="supyr_struct, binary, data structure, parser, serializer, serialize",
    install_requires=[],
    requires=[],
    provides=['supyr_struct'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        ],
    zip_safe=False,
    )
