try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import supyr_struct

long_desc = ""
try:
    long_desc = open("README.MD").read()
except Exception:
    print("Couldn't read readme.")

setup(
    name='supyr_struct',
    description='A versatile and extensible binary data '
                'parsing/serializing library for Python 3',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    version='%s.%s.%s' % supyr_struct.__version__,
    url=supyr_struct.__website__,
    project_urls={
        #"Documentation": <Need a string entry here>,
        "Source": supyr_struct.__website__,
        "Funding": "https://liberapay.com/MEK/",
    },
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
        'supyr_struct.field_type_methods',
        'supyr_struct.tests',
        ],
    package_data={
        'supyr_struct': [
            'docs/*.*',
            'examples/test_tags/documents/*.*',
            'examples/test_tags/images/*.*',
            'examples/test_tags/keyblobs/*.*',
            '*.[Mm][Dd]', '*.[Tt][Xx][Tt]',
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        ],
    zip_safe=False,
    )
