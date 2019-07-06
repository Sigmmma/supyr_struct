'''
PNG image file definitions
'''

from math import log

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.buffer import BytearrayBuffer
from supyr_struct.field_types import *

from supyr_struct.defs.bitmaps.objs.png import PngTag

__all__ = ("png_def", "get", )


def get(): return png_def


def has_next_chunk(rawdata=None, **kwargs):
    try:
        data = rawdata.peek(12)
        if len(data) != 12:
            return False

        return len(rawdata) >= (
            rawdata.tell() + 12 + int.from_bytes(data[:4], 'big'))
    except AttributeError:
        return False


def chunk_data_size(parent=None, rawdata=None, new_value=None,
                    extra_size=0, **kwargs):
    if new_value is None:
        try:
            return parent.data_size - extra_size
        except AttributeError:
            return 0
    parent.data_size = new_value + extra_size


def iccp_chunk_data_size(parent=None, rawdata=None, new_value=None, **kwargs):
    return chunk_data_size(
        parent=parent, rawdata=rawdata,
        extra_size=len(parent.profile_name) + 2, **kwargs)


def itxt_chunk_data_size(parent=None, rawdata=None, **kwargs):
    return chunk_data_size(
        parent=parent, rawdata=rawdata, extra_size=(
        len(parent.keyword) + len(parent.language_tag) +
        len(parent.translated_keyword)) + 5, **kwargs)


def text_chunk_data_size(parent=None, rawdata=None, **kwargs):
    return chunk_data_size(
        parent=parent, rawdata=rawdata,
        extra_size=len(parent.keyword) + 1, **kwargs)


def ztxt_chunk_data_size(parent=None, rawdata=None, **kwargs):
    return chunk_data_size(
        parent=parent, rawdata=rawdata,
        extra_size=len(parent.keyword) + 2, **kwargs)


def get_chunk_type(rawdata=None, **kwargs):
    try:
        data = rawdata.peek(8)
        if len(data) == 8:
            return data[4: 8].decode("latin-1")
    except AttributeError:
        pass


compression_method = UEnum8("compression",
    "deflate"
    )


ihdr_chunk = Struct("ihdr_chunk",
    UInt32("data_size", DEFAULT=13, EDITABLE=False),
    UInt32("sig", DEFAULT='IHDR', EDITABLE=False),
    UInt32("width"),
    UInt32("height"),
    UInt8("bit_depth"),  # bits per channel, not per pixel. usually 8
    UEnum8("color_type",
        "greyscale",
        ("truecolor", 2),
        "indexed_color",
        "greyscale_with_alpha",
        ("truecolor_with_alpha", 6),
        ),
    compression_method,
    UEnum8("filter_method",
        "standard"
        ),
    UEnum8("interlace_method",
        "none",
        "adam7"
        ),
    UInt32("crc", EDITABLE=False),
    )


plte_chunk = Container("plte_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='PLTE', EDITABLE=False),
    BytesRaw("data", SIZE=".data_size"),
    UInt32("crc", EDITABLE=False),
    )


idat_chunk = Container("idat_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='IDAT', EDITABLE=False),
    BytesRaw("data", SIZE=chunk_data_size),
    UInt32("crc", EDITABLE=False),
    )


iend_chunk = Container("iend_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='IEND', EDITABLE=False),
    BytesRaw("data", SIZE=chunk_data_size),
    UInt32("crc", EDITABLE=False),
    )


chrm_chunk = Struct("chrm_chunk",
    UInt32("data_size", DEFAULT=32, EDITABLE=False),
    UInt32("sig", DEFAULT='cHRM', EDITABLE=False),
    UInt32("white_point_x", UNIT_SCALE=1/100000),
    UInt32("white_point_y", UNIT_SCALE=1/100000),
    UInt32("red_x",   UNIT_SCALE=1/100000),
    UInt32("red_y",   UNIT_SCALE=1/100000),
    UInt32("green_x", UNIT_SCALE=1/100000),
    UInt32("green_y", UNIT_SCALE=1/100000),
    UInt32("blue_x",  UNIT_SCALE=1/100000),
    UInt32("blue_y",  UNIT_SCALE=1/100000),
    UInt32("crc", EDITABLE=False),
    )


gama_chunk = Struct("gama_chunk",
    UInt32("data_size", DEFAULT=4, EDITABLE=False),
    UInt32("sig", DEFAULT='gAMA', EDITABLE=False),
    UInt32("gamma", UNIT_SCALE=1/100000),
    UInt32("crc", EDITABLE=False),
    )


iccp_chunk = Container("iccp_chunk",
    UInt32("data_size", DEFAULT=2, EDITABLE=False),
    UInt32("sig", DEFAULT='iCCP', EDITABLE=False),
    CStrLatin1("profile_name"),
    compression_method,
    BytesRaw("compressed_profile", SIZE=iccp_chunk_data_size),
    UInt32("crc", EDITABLE=False),
    )


sbit_chunk = Container("sbit_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='sBIT', EDITABLE=False),
    UInt8Array("significant_bits", SIZE=".data_size"),
    UInt32("crc", EDITABLE=False),
    )


srgb_chunk = Struct("srgb_chunk",
    UInt32("data_size", DEFAULT=1, EDITABLE=False),
    UInt32("sig", DEFAULT='sRGB', EDITABLE=False),
    UEnum8("intent",
        "perceptual",
        "relative_colorimetric",
        "saturation",
        "absolute_colorimetric",
        ),
    UInt32("crc", EDITABLE=False),
    )


hist_chunk = Container("hist_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='hIST', EDITABLE=False),
    UInt16Array("frequencies", SIZE=".data_size"),
    UInt32("crc", EDITABLE=False),
    )


phys_chunk = Struct("phys_chunk",
    UInt32("data_size", DEFAULT=9, EDITABLE=False),
    UInt32("sig", DEFAULT='pHYs', EDITABLE=False),
    UInt32("pixels_per_x_unit"),
    UInt32("pixels_per_y_unit"),
    UEnum8("units",
        "unknown",
        "meter",
        ),
    UInt32("crc", EDITABLE=False),
    )


trns_chunk = Container("trns_chunk",
    UInt32("data_size", EDITABLE=False),
    UInt32("sig", DEFAULT='tRNS', EDITABLE=False),
    BytesRaw("palette", SIZE=".data_size"),
    UInt32("crc", EDITABLE=False),
    )


time_chunk = QStruct("time_chunk",
    UInt32("data_size", DEFAULT=7, EDITABLE=False),
    UInt32("sig", DEFAULT='tIME', EDITABLE=False),
    UInt16("year"),
    UInt8("month"),
    UInt8("day"),
    UInt8("hour"),
    UInt8("minute"),
    UInt8("second"),
    UInt32("crc", EDITABLE=False),
    )


itxt_chunk = Container("itxt_chunk",
    UInt32("data_size", DEFAULT=5, EDITABLE=False),
    UInt32("sig", DEFAULT='iTXt', EDITABLE=False),
    CStrLatin1("keyword", EDITABLE=False),
    UInt8("is_compressed"),
    compression_method,
    CStrLatin1("language_tag", EDITABLE=False),
    CStrLatin1("translated_keyword", EDITABLE=False),
    BytesRaw("text", SIZE=itxt_chunk_data_size),
    UInt32("crc", EDITABLE=False),
    )


text_chunk = Container("text_chunk",
    UInt32("data_size", DEFAULT=5, EDITABLE=False),
    UInt32("sig", DEFAULT='tEXt', EDITABLE=False),
    CStrLatin1("keyword", EDITABLE=False),
    BytesRaw("text", SIZE=text_chunk_data_size),
    UInt32("crc", EDITABLE=False),
    )


ztxt_chunk = Container("ztxt_chunk",
    UInt32("data_size", DEFAULT=5, EDITABLE=False),
    UInt32("sig", DEFAULT='zTXt', EDITABLE=False),
    CStrLatin1("keyword", EDITABLE=False),
    compression_method,
    BytesRaw("text", SIZE=ztxt_chunk_data_size),
    UInt32("crc"),
    )


unknown_chunk = Container("unknown_chunk",
    UInt32("data_size"),
    UInt32("sig"),
    BytesRaw("data", SIZE=chunk_data_size),
    UInt32("crc"),
    )


chunk = Switch("chunk",
    DEFAULT=unknown_chunk,
    CASE=get_chunk_type,
    CASES={
        "IHDR": ihdr_chunk,
        "PLTE": plte_chunk,
        "IDAT": idat_chunk,
        "IEND": iend_chunk,
        "cHRM": chrm_chunk,
        "gAMA": gama_chunk,
        "iCCP": iccp_chunk,
        "sBIT": sbit_chunk,
        "sRGB": srgb_chunk,
        "hIST": hist_chunk,
        "pHYs": phys_chunk,
        "tRNS": trns_chunk,
        "tIME": time_chunk,
        "iTXt": itxt_chunk,
        "tEXt": text_chunk,
        "zTXt": ztxt_chunk,
        }
    )


png_def = TagDef("png",
    StrRawLatin1("png_sig",
        DEFAULT='\x89PNG\x0D\x0A\x1A\x0A', EDITABLE=False, SIZE=8),
    WhileArray("chunks",
        SUB_STRUCT=chunk,
        CASE=has_next_chunk
        ),

    ext=".png", endian=">", tag_cls=PngTag
    )
