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
    def calculate_chunk_checksum(self, chunk):
        chunk.crc = zlib.crc32(chunk.serialize(calc_pointers=False)[4: -4])
        if chunk.crc < 0: chunk.crc += 0x100000000
        chunk.crc = chunk.crc & 0xFFffFFff

    def get_chunk_data(self, chunk):
        if chunk.sig == IDAT_CHUNK_SIG:
            compression = chunk.parent[0].compression
        elif hasattr(chunk, "compression"):
            compression = chunk.compression
        else:
            raise TypeError("This chunk cannot contain compressed raw data.")

        if compression.enum_name == "deflate":
            return zlib.decompress(chunk[-2])  # second to last thing is data
        return None

    def set_chunk_data(self, chunk, new_data):
        if chunk.sig == IDAT_CHUNK_SIG:
            compression = chunk.parent[0].compression
        elif hasattr(chunk, "compression"):
            compression = chunk.compression
        else:
            raise TypeError("This chunk cannot contain compressed raw data.")

        if compression.enum_name == "deflate":
            chunk[-2] = zlib.compress(new_data)

    def serialize(self, *args, **kwargs):
        for chunk in self.data.chunks:
            self.calculate_chunk_checksum(chunk)
        Tag.serialize(self, *args, **kwargs)
