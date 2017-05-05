#!/usr/bin/env python
from os.path import dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

curr_dir = dirname(__file__)

#               YYYY.MM.DD
release_date = "2017.05.04"
version = (0, 9, 10)

try:
    try:
        long_desc = open(join(curr_dir, "readme.rst")).read()
    except Exception:
        long_desc = open(join(curr_dir, "readme.md")).read()
except Exception:
    long_desc = 'Could not read long description from readme.'

setup(
    name='supyr_struct',
    description='A versatile and extensible binary data \
parsing/serializing library for Python 3',
    long_description=long_desc,
    version='%s.%s.%s' % version,
    url='http://bitbucket.org/moses_of_egypt/supyr_struct',
    author='Devin Bobadilla',
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'supyr_struct',
        'supyr_struct.blocks',
        'supyr_struct.defs',
        'supyr_struct.defs.audio',
        'supyr_struct.defs.bitmaps',
        'supyr_struct.defs.bitmaps.objs',
        'supyr_struct.defs.crypto',
        'supyr_struct.defs.documents',
        'supyr_struct.defs.executables',
        'supyr_struct.defs.filesystem',
        'supyr_struct.defs.filesystem.objs',
        'supyr_struct.examples',
        'supyr_struct.tests',
        ],
    package_data={
        '': ['*.txt', '*.md', '*.rst'],
        'supyr_struct': [
            'docs/*.*',
            'examples/test_tags/document/*.*',
            'examples/test_tags/images/*.*',
            'examples/test_tags/keyblobs/*.*'
            ]
        },
    platforms=["POSIX", "Windows"],
    keywords="supyr_struct, binary, data structure, parser, \
serializer, serialize",
    install_requires=[],
    requires=[],
    provides=['supyr_struct'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        ],
    zip_safe=False,
    )
