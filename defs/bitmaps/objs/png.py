'''
This module provides a base Tag class for a Png image file.
'''
import zlib

from supyr_struct.tag import *


IDAT_CHUNK_SIG = int.from_bytes(b'IDAT', 'big')

def pad_idat_data(data, stride):
    new_data = b''
    for i in range(0, len(data), stride):
        new_data += b'\x00' + data[i: i+stride]

    return new_data


class PngTag(Tag):
    '''
    Png image file class.
    '''
    def get_chunk_data(self, chunk):
        if chunk.sig == IDAT_CHUNK_SIG:
            compression = chunk.parent[0].compression
        else:
            compression = chunk.compression

        if compression.enum_name == "deflate":
            return zlib.decompress(chunk[-2])  # second to last thing is data
        return None

    def set_chunk_data(self, chunk, new_data):
        if chunk.sig == IDAT_CHUNK_SIG:
            compression = chunk.parent[0].compression
        else:
            compression = chunk.compression

        if compression.enum_name == "deflate":
            chunk[-2] = zlib.compress(new_data)
