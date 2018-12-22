'''
This module provides a base Tag class for a Png image file.
'''
import zlib

from supyr_struct.tag import *


IDAT_CHUNK_SIG = int.from_bytes(b'IDAT', 'big')

def pad_idat_data(data, stride):
    # this is the fastest way to do this
    new_data = bytearray(((stride + 1)*len(data))//stride)
    pad = 1
    for i in range(0, len(data), stride):
        new_data[i+pad: i+pad+stride] = data[i: i+stride]
        pad += 1

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

    def set_chunk_data(self, chunk, new_data, png_compress_level=None):
        if chunk.sig == IDAT_CHUNK_SIG:
            compression = chunk.parent[0].compression
        elif hasattr(chunk, "compression"):
            compression = chunk.compression
        else:
            raise TypeError("This chunk cannot contain compressed raw data.")

        if compression.enum_name == "deflate":
            if png_compress_level in range(0, 10):
                chunk[-2] = zlib.compress(new_data, png_compress_level)
            else:
                chunk[-2] = zlib.compress(new_data)

    def serialize(self, *args, **kwargs):
        if kwargs.get("calc_checksums", True):
            for chunk in self.data.chunks:
                self.calculate_chunk_checksum(chunk)
        Tag.serialize(self, *args, **kwargs)
