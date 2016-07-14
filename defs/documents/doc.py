'''
Definition for Microsoft Word doc files.
'''
from ..filesystem.olecf import *

def get(): return ms_doc_def

ms_doc_def = TagDef("doc",
    descriptor=olecf_def.descriptor, sanitize=False,
    ext=".doc", endian="<", tag_cls=olecf_def.tag_cls
    )
