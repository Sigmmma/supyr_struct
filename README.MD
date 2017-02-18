# Supyr Struct

## What is this repository for?

* Current Version: 0.9.1

* Supyr Struct is an extensible and powerful binary data parsing, editing, and serializing library for Python 3. Supyrs parsing and serializing is declarative, meaning that rather than write code to handle reading and writing data, one instead pieces together a description of the structure using various "FieldTypes". This description is passed to a BlockDef, which uses it to build "Block" objects to represent/hold the parsed data.

* For a detailed overview of the more abstract concepts and features of Supyr, read the text files in the 'docs' folder.

## Installing
* Need to write this when im not sick


## Example usage

```python
>>> from supyr_struct import *
>>> asdf = BlockDef('some_block',
...     UInt32('some_int'),
...     BytesRaw('some_bytes', SIZE=16),
...     ENDIAN='>'
...     )
>>> test_block = asdf.build()
>>> test_block.some_int = 1337
>>> test_block.some_bytes = b'heres a cstring\x00'
>>> print(test_block)
[ Container, entries:2, some_block
    [ UInt32, size:4, some_int, 1337 ]
    [ BytesRaw, size:16, some_bytes, <RAWDATA> ]
    ]
>>> test_block.serialize()
bytearray(b'\x00\x00\x059heres a cstring\x00')
```

Supyr also supports forcing the endianness of the library to be either big, little, or back to normal on a global scale and/or on individual FieldTypes.

```python
>>> field_types.FieldType.force_little()
>>> test_block.serialize()
bytearray(b'9\x05\x00\x00heres a cstring\x00')
>>> field_types.FieldType.force_normal()
>>> test_block.serialize()
bytearray(b'\x00\x00\x059heres a cstring\x00')
>>> field_types.BUInt32.force_little()
>>> test_block.serialize()
bytearray(b'9\x05\x00\x00heres a cstring\x00')
```

Supyr also implements a BlockDef subclass called a TagDef, which creates Tag instances rather than Block instances. Tags are a kind of header object that hold a reference to the root of the structure, the TagDef used to build the Tag, a filepath to parse from/serialize to, and other properties. Tags and TagDefs are not required to parse/serialize files, but are a simple way to treat a parsed structure as a file.

Take a look at the examples module for some ready-to-run example programs that utilize Supyr in different ways.

This readme needs more general highlights of the library, but for now I guess this is fine.
-

## Who do I talk to?

* [Devin Bobadilla](mosesbobadilla@gmail.com)(Author of supyr_struct)