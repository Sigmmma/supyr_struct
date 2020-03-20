# Supyr Struct

[![](https://img.shields.io/pypi/dm/supyr_struct)](https://pypistats.org/packages/supyr_struct)
![](https://ci.appveyor.com/api/projects/status/github/Sigmmma/supyr_struct?svg=true)
[![PyPI version](https://badge.fury.io/py/supyr-struct.svg)](https://pypi.org/project/supyr_struct/)
[![GitHub version](https://badge.fury.io/gh/Sigmmma%2Fsupyr_struct.svg)](https://github.com/Sigmmma/supyr_struct)

Supyr Struct is an extensible and powerful binary data parsing, editing, and serializing library for Python 3.

Supyr's parsing and serializing is declarative, meaning that rather than write code to handle parsing and serializing data, you instead create a description of the structure using various FieldTypes. These descriptions are used by BlockDef objects to build Blocks, which represent/contain the parsed data. A BlockDef is simply a constructor object that scans its description for errors on initialization and uses it for creating Blocks.


Supyr provides a large collection of FieldTypes, ranging from atomic data types(floats and ints of various sizes) to hierarchical structures(structs, containers, and arrays) and logical structures and wrappers(switches and unions).


For a detailed overview of the more abstract concepts and features of Supyr, read the text files in the 'docs' folder.

## Changelog
Check out the changelog [here](https://github.com/Sigmmma/supyr_struct/blob/master/CHANGELOG.MD).

## License
This project is licensed under the MIT License, check out the details and author info [here](https://github.com/Sigmmma/supyr_struct/blob/master/LICENSE.TXT).

## Installing

You'll need Python 3.5 or higher.

In your terminal execute:
```sh
python3 -m pip install supyr_struct
```
or, you can clone/download this repo and run the setup.py:
```sh
git clone git@github.com:Sigmmma/supyr_struct.git
cd supyr_struct
python3 -m pip install .
```


## Examples

Heres a small example of defining a structure using a BlockDef and FieldTypes and using it to create a Block.

```py

>>> from supyr_struct import *
>>>
>>>
>>> asdf = BlockDef('some_block',
... UInt32('some_int'),
... BytesRaw('some_bytes', SIZE=16),
... ENDIAN='>')
>>>
>>>
>>> test_block = asdf.build()
>>> test_block.some_int = 1337
>>> test_block['some_bytes'] = b'here\'s a cstring\x00'
>>>
>>> print('test_block:', test_block)
test_block: [ Container, entries:2, some_block
    [ UInt32, size:4, some_int, 1337 ]
    [ BytesRaw, size:16, some_bytes, <RAWDATA> ]
    ]
>>>
>>>
>>> test_block.serialize()
BytearrayBuffer(b"\x00\x00\x059here\'s a cstring\x00")
```

Supyr allows forcing endianness to be either big, little, or back to normal on a library scale and/or on individual FieldTypes.
```py
>>> field_types.FieldType.force_little()
>>> test_block.serialize()
BytearrayBuffer(b"9\x05\x00\x00here\'s a cstring\x00")
>>>
>>> field_types.FieldType.force_normal()
>>> test_block.serialize()
BytearrayBuffer(b"\x00\x00\x059here\'s a cstring\x00")
>>>
>>> field_types.FieldType.force_big()
>>> test_block.serialize()
BytearrayBuffer(b"\x00\x00\x059here\'s a cstring\x00")
>>>
>>> field_types.FieldType.force_little()
>>> test_block.serialize()
BytearrayBuffer(b"9\x05\x00\x00here\'s a cstring\x00")
```


Take a look at the examples module for some ready-to-run example programs that utilize Supyr in different ways.


## Who do I talk to?

If you're having any issues with the library you can report them on our [GitHub Issues page](https://github.com/Sigmmma/supyr_struct/issues).

If the issue requires some more direct attention we'll drop a contact link.
