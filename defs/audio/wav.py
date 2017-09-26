'''
This definition is badly incomplete, but it serves a purpose for another
library I wrote, so I decided I might as well throw it in here as well.
'''
from supyr_struct.defs.constants import PATHDIV
from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *

def fmt_extra_data_size(parent=None, new_value=None, *args, **kwargs):
    if parent is None:
        return 0
    if new_value is None:
        return parent.length - 16

    parent.length = new_value + 16

wav_header = QStruct("wav_header",
    UInt32("riff_sig", DEFAULT="FFIR"),
    UInt32("filesize"),
    UInt32("wave_sig", DEFAULT="EVAW"),
    )

wav_format = Container("format",
    UInt32("sig", DEFAULT=" tmf"),
    UInt32("length", DEFAULT=20),
    UEnum16("fmt",
        ("pcm",        0x0001),
        ("ima_adpcm",  0x0011),
        ("xbox_adpcm", 0x0069),
        ("wmaudio2",   0x0161),
        DEFAULT=1
        ),
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

wav_data = Container("wav_data",
    UInt32("data_sig", DEFAULT="atad"),
    UInt32("audio_data_size"),
    BytesRaw("audio_data", SIZE='.audio_data_size')
    )

wav_def = TagDef("wav",
    wav_header,
    wav_format,
    wav_data,
    ext='.wav', ENDIAN='<'
    )

def get():
    return wav_def
