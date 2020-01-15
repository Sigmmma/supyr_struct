from os.path import dirname, join

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import supyr_struct

long_desc = open("README.MD").read()

setup(
    name='supyr_struct',
    description='A versatile and extensible binary data '
                'parsing/serializing library for Python 3',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    version='%s.%s.%s' % supyr_struct.__version__,
    url=supyr_struct.__website__,
    author=supyr_struct.__author__,
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
        'supyr_struct': [
            'docs/*.*',
            'examples/test_tags/documents/*.*',
            'examples/test_tags/images/*.*',
            'examples/test_tags/keyblobs/*.*',
            '*.MD', '*.txt'
            ]
        },
    platforms=["POSIX", "Windows"],
    keywords=["supyr_struct", "binary", "data structure", "parser",
              "serializer", "serialize"],
    install_requires=[],
    requires=[],
    python_requires=">=3.5",
    provides=['supyr_struct'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        ],
    zip_safe=False,
    )
