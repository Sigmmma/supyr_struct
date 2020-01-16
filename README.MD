Supyr Struct
============

Supyr Struct is an extensible and powerful binary data parsing, editing, and serializing library for Python 3.

Supyr's parsing and serializing is declarative, meaning that rather than write code to handle parsing and serializing data, you instead piece together a description of the structure using various [FieldTypes](https://github.com/MosesofEgypt/supyr_struct/blob/master/supyr_struct/field_types.py). These descriptions are used by [BlockDef](defs/block_def.py) objects to build [Blocks](https://github.com/MosesofEgypt/supyr_struct/blob/master/supyr_struct/blocks/block.py), which represent/contain the parsed data. A BlockDef is simply a constructor object that scans its description for errors on initialization and uses it for creating Blocks.


Supyr provides a large collection of FieldTypes, ranging from atomic data types(floats and ints of various sizes) to hierarchical structures(structs, containers, and arrays) and logical structures and wrappers(switches and unions).


For a detailed overview of the more abstract concepts and features of Supyr, read the text files in the 'docs' folder.

Changelog
----------
Check out the changelog [here](https://github.com/MosesofEgypt/supyr_struct/blob/master/CHANGELOG.MD).

License
----------
This project is licensed under the MIT License, check out the details and author info [here](https://github.com/MosesofEgypt/supyr_struct/blob/master/LICENSE.TXT).

Installing
----------

You'll need Python 3.5 or higher.

In your terminal execute:
```sh
python3 -m pip install supyr_struct
```
or, you can clone/download this repo and run the setup.py:
```sh
git clone git@github.com:MosesofEgypt/supyr_struct.git
cd supyr_struct
python3 -m pip install .
```


Examples
--------

Heres a small example of defining a structure using a BlockDef and FieldTypes and using it to create a Block.

```py

>>> from supyr_struct import *


>>> asdf = BlockDef('some_block',
... UInt32('some_int'),
... BytesRaw('some_bytes', SIZE=16),
... ENDIAN='>')

>>> test_block = asdf.build()
>>> test_block.some_int = 1337
>>> test_block.some_bytes = b'heres a cstring\x00'

>>> print(test_block)
... [ Container, entries:2, some_block
... [ UInt32, size:4, some_int, 1337 ]
... [ BytesRaw, size:16, some_bytes, <rawdata> ]
... ]

>>> test_block.serialize()
... bytearray(b'\x00\x00\x059heres a cstring\x00')
```

Supyr allows forcing endianness to be either big, little, or back to normal on a library scale and/or on individual FieldTypes.
```py
>>> field_types.FieldType.force_little()
>>> test_block.serialize()
... bytearray(b'9\x05\x00\x00heres a cstring\x00')
>>> field_types.FieldType.force_normal()
>>> test_block.serialize()
... bytearray(b'\x00\x00\x059heres a cstring\x00')
>>> field_types.BUInt32.force_little()
>>> test_block.serialize()
... bytearray(b'9\x05\x00\x00heres a cstring\x00')
```


Take a look at the examples module for some ready-to-run example programs that utilize Supyr in different ways.


Who do I talk to?
-----------------

 - Devin Bobadilla mosesbobadilla@gmail.com
