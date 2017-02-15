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

wav_header = QStruct("wav header",
    UInt32("riff sig", DEFAULT="FFIR"),
    UInt32("filesize"),
    UInt32("wave sig", DEFAULT="EVAW"),
    )

wav_format = Container("format",
    UInt32("sig", DEFAULT=" tmf"),
    UInt32("length", DEFAULT=20),
    UEnum16("fmt",
        ("pcm", 1),
        ("ima adpcm",  0x11),
        ("xbox adpcm", 0x69),
        DEFAULT=1
        ),
    UInt16("channels", DEFAULT=2),
    UInt32("sample rate", DEFAULT=22050),
    # (Sample Rate * BitsPerSample * Channels) // 8
    UInt32("byte rate", DEFAULT=88200),

    # typically (bits per sample * channels) // 8
    # 1 == 8 bit mono
    # 2 == 8 bit stereo/16 bit mono
    # 4 == 16 bit stereo
    UInt16("block align", DEFAULT=16), # aka "channel bytes per sample"
    UInt16("bits per sample", DEFAULT=4),

    BytesRaw("extra data", SIZE=fmt_extra_data_size),
    )

wav_data = Container("wav data",
    UInt32("data sig", DEFAULT="atad"),
    UInt32("audio data size"),
    BytesRaw("audio data", SIZE='.audio_data_size')
    )

wav_def = TagDef("wav",
    wav_header,
    wav_format,
    wav_data,
    ext='.wav', ENDIAN='<'
    )
