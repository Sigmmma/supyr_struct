Supyr Struct
============


What is this repository for?
----------------------------

Supyr Struct is an extensible and powerful binary data parsing, editing, and serializing library for Python 3. Supyrs parsing and serializing is declarative, meaning that rather than write code to handle parsing and serializing data, one instead pieces together a description of the structure using various `FieldTypes <https://bitbucket.org/moses_of_egypt/supyr_struct/src/default/field_types.py>`_. These descriptions are used by `BlockDef <https://bitbucket.org/moses_of_egypt/supyr_struct/src/default/defs/block_def.py>`_ objects to build `Blocks <https://bitbucket.org/moses_of_egypt/supyr_struct/src/default/blocks/block.py>`_, which represent/contain the parsed data. A BlockDef is simply a constructor object that scans its description for errors on initialization and uses it for creating Blocks.


Supyr provides a large collection of FieldTypes, ranging from atomic data types(floats and ints of various sizes) to hierarchical structures(structs, containers, and arrays) and logical structures and wrappers(switches and unions).


For a detailed overview of the more abstract concepts and features of Supyr, read the text files in the 'docs' folder.

Installing
----------

First install any version of Python 3(The newest version is recommended).

There are two ways to install supyr_struct from this point:

-    Open a command prompt and execute ``pip install supyr_struct``

or

-    Extract a copy of the repository into a directory titled "supyr_struct".
-    Move the file "setup.py" into the directory containing "supyr_struct".
-    Open a command prompt, navigate to the directory containing setup.py, and execute:``python setup.py install``

Once the install finishes, supyr_struct should be ready to use.

Examples
--------

Heres a small example of defining a structure using a BlockDef and FieldTypes and using it to create a Block.

    .. code:: python

		>>> from supyr_struct import *


		>>> asdf = BlockDef('some_block',
			UInt32('some_int'),
			BytesRaw('some_bytes', SIZE=16),
			ENDIAN='>')

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


Supyr allows forcing endianness to be either big, little, or back to normal on a library scale and/or on individual FieldTypes.

    .. code:: python

		>>> field_types.FieldType.force_little()
		>>> test_block.serialize()
		... bytearray(b'9\x05\x00\x00heres a cstring\x00')
		>>> field_types.FieldType.force_normal()
		>>> test_block.serialize()
		... bytearray(b'\x00\x00\x059heres a cstring\x00')
		>>> field_types.BUInt32.force_little()
		>>> test_block.serialize()
		... bytearray(b'9\x05\x00\x00heres a cstring\x00')



Take a look at the examples module for some ready-to-run example programs that utilize Supyr in different ways.

Development and support
-----------------------

- I dont know how to use the issue tracker right now(this is my first release) so this is under construction.


Todo
----

- Finish documentation.

- Write up a simple-ish tutorial that goes over each aspect of the library.


Who do I talk to?
-----------------

- Devin Bobadilla (Author of supyr_struct) mosesbobadilla@gmail.com
