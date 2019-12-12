'''
This definition is badly incomplete, but it serves a purpose for another
library I wrote, so I decided I might as well throw it in here as well.
'''
from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *

__all__ = ("wav_def", "get", )

chunk_sigs = (
    "data",
    "fact",
    "PEAK",
    )

wav_formats = (
    # TODO: Eventually fill out all these formats with this list
    # https://www.recordingblogs.com/wiki/format-chunk-of-a-wave-file
    ("pcm",          0x0001),
    ("ms_adpcm",     0x0002),
    ("pcm_float",    0x0003),
    ("g_711_a_law",  0x0006),
    ("g_711_u_law",  0x0007),
    ("ima_adpcm",    0x0011),
    ("yamaha_adpcm", 0x0014),
    ("gsm_6_10",     0x0031),
    ("g_721_adpcm",  0x0040),
    ("mpeg",         0x0050),
    ("xbox_adpcm",   0x0069),
    ("wmaudio2",     0x0161),
    )

def fmt_extra_data_size(parent=None, new_value=None, *args, **kwargs):
    if parent is None:
        return 0
    if new_value is None:
        return parent.length - 16

    parent.length = new_value + 16

def has_next_chunk(rawdata=None, **kwargs):
    try:
        data = rawdata.peek(8)
        if len(data) != 8:
            return False

        return len(rawdata) >= (
            rawdata.tell() + 8 + int.from_bytes(data[4:8], 'little'))
    except AttributeError:
        return False

def get_chunk_type(rawdata=None, **kwargs):
    try:
        data = rawdata.peek(4)
        if len(data) == 4:
            return data[: 4].decode("latin-1")
    except AttributeError:
        pass


def chunk_extra_data_size(parent=None, rawdata=None, new_value=None,
                          extra_size=0, **kwargs):
    if new_value is None:
        try:
            return parent.data_size - extra_size
        except AttributeError:
            return 0
    parent.data_size = new_value + extra_size


def fact_chunk_extra_data_size(parent=None, rawdata=None, new_value=None,
                               **kwargs):
    return chunk_extra_data_size(
        parent=parent, rawdata=rawdata, new_value=new_value,
        extra_size=4, **kwargs)

def peak_chunk_extra_data_size(parent=None, rawdata=None, new_value=None,
                               **kwargs):
    try:
        channel_count = len(parent.peak)
    except Exception:
        channel_count = 0

    return chunk_extra_data_size(
        parent=parent, rawdata=rawdata, new_value=new_value,
        extra_size=8 + 8 * channel_count, **kwargs)


peak_position = QStruct("peak_position",
    Float("value"),
    UInt32("position"),
    )

chunk_sig_enum = UEnum32("sig",
    *((fourcc, fourcc[::-1]) for fourcc in chunk_sigs),
    EDITABLE=False
    )

unknown_chunk = Container("unknown_chunk",
    UEnum32("sig", INCLUDE=chunk_sig_enum),
    UInt32("data_size", EDITABLE=False),
    BytesRaw("data", SIZE=chunk_extra_data_size)
    )

data_chunk = Container("data_chunk",
    UEnum32("sig", INCLUDE=chunk_sig_enum, DEFAULT="atad"),
    UInt32("data_size", EDITABLE=False),
    BytesRaw("data", SIZE=chunk_extra_data_size)
    )

fact_chunk = Container("fact_chunk",
    UEnum32("sig", INCLUDE=chunk_sig_enum, DEFAULT="tcaf"),
    UInt32("data_size", DEFAULT=4, EDITABLE=False),
    UInt32("sample_count"),
    BytesRaw("data", SIZE=fact_chunk_extra_data_size, VISIBLE=False)
    )

peak_chunk = Container("peak_chunk",
    UEnum32("sig", INCLUDE=chunk_sig_enum, DEFAULT="KAEP"),
    UInt32("data_size", EDITABLE=False),
    UInt32("version"),
    Timestamp32("timestamp"),
    Array("peak",
        SUB_STRUCT=peak_position,
        SIZE="...wav_format.channels"
        ),
    BytesRaw("data", SIZE=peak_chunk_extra_data_size, VISIBLE=False)
    )


wav_header = QStruct("wav_header",
    UInt32("riff_sig", DEFAULT="FFIR", EDITABLE=False),
    UInt32("filesize"),
    UInt32("wave_sig", DEFAULT="EVAW", EDITABLE=False),
    )

wav_format = Container("wav_format",
    UInt32("sig", DEFAULT=" tmf", EDITABLE=False),
    UInt32("length", DEFAULT=20, EDITABLE=False),
    UEnum16("fmt", *wav_formats, DEFAULT=1),
    UInt16("channels", DEFAULT=2),
    UInt32("sample_rate", DEFAULT=22050),
    # (Sample Rate * BitsPerSample * Channels) // 8
    UInt32("byte_rate", DEFAULT=88200),

    # typically (bits per sample * channels) // 8
    # 1 == 8 bit mono
    # 2 == 8 bit stereo/16 bit mono
    # 4 == 16 bit stereo
    UInt16("block_align", DEFAULT=16), # aka "channel bytes per sample"
    UInt16("bits_per_sample", DEFAULT=4),

    BytesRaw("extra_data", SIZE=fmt_extra_data_size),
    )

chunk = Switch("chunk",
    DEFAULT=unknown_chunk,
    CASE=get_chunk_type,
    CASES={
        "data": data_chunk,
        "fact": fact_chunk,
        "PEAK": peak_chunk,
        }
    )

wav_def = TagDef("wav",
    wav_header,
    wav_format,
    WhileArray("wav_chunks",
        SUB_STRUCT=chunk,
        CASE=has_next_chunk
        ),
    ext='.wav', ENDIAN='<'
    )

def get():
    return wav_def
