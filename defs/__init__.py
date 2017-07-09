'''
This module contains library constants, an immutable FrozenDict,
dict subclass, some common descriptors, the BlockDef and TagDef
classes, a few test TagDefs, and various example TagDefs and
descriptors for images, executables, and crypto keyblobs.
'''

__all__ = ['block_def', 'common_descs', 'constants', 'util',
           'frozen_dict', 'tag_def', 'test_defs',
           'audio', 'bitmaps', 'crypto', 'documents', 'executables',
           'filesystem']

from . import audio, bitmaps, crypto, documents, executables, filesystem
