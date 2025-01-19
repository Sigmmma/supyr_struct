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
    "LIST",
    "id3 ",
    )

list_type_sigs = (
    "INFO",
    "adtl",
    )

list_info_type_sigs = (
    # taken from here:
    #   https://www.recordingblogs.com/wiki/list-chunk-of-a-wave-file
    "IARL", # The location where the subject of the file is archived
    "IART", # The artist of the original subject of the file
    "ICMS", # The name of the person or organization that commissioned the original subject of the file
    "ICMT", # General comments about the file or its subject
    "ICOP", # Copyright information about the file (e.g., "Copyright Some Company 2011")
    "ICRD", # The date the subject of the file was created (creation date) (e.g., "2022-12-31")
    "ICRP", # Whether and how an image was cropped
    "IDIM", # The dimensions of the original subject of the file
    "IDPI", # Dots per inch settings used to digitize the file
    "IENG", # The name of the engineer who worked on the file
    "IGNR", # The genre of the subject
    "IKEY", # A list of keywords for the file or its subject
    "ILGT", # Lightness settings used to digitize the file
    "IMED", # Medium for the original subject of the file
    "INAM", # Title of the subject of the file (name)
    "IPLT", # The number of colors in the color palette used to digitize the file
    "IPRD", # Name of the title the subject was originally intended for
    "ISBJ", # Description of the contents of the file (subject)
    "ISFT", # Name of the software package used to create the file
    "ISRC", # The name of the person or organization that supplied the original subject of the file
    "ISRF", # The original form of the material that was digitized (source form)
    "ITCH", # The name of the technician who digitized the subject file
    )

list_adtl_type_sigs = (
    "labl",
    "note",
    "ltxt",
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

def get_set_chunk_size(parent=None, new_value=None, *args, **kwargs):
    if parent is None:
        return 0
    if new_value is None:
        return ((parent.data_size+3)//4)*4

    parent.data_size = ((new_value+3)//4)*4

def get_list_chunk_size(list_data):
    return 4 + sum(
        8 + get_set_chunk_size(parent=p) for p in list_data
        )

def has_next_chunk(rawdata=None, **kwargs):
    try:
        data = rawdata.peek(8)
        if len(data) != 8:
            return False

        return len(rawdata) >= (
            rawdata.tell() + 8 + int.from_bytes(data[4:8], 'little'))
    except AttributeError:
        return False

def has_next_list_sub_chunk(parent=None, rawdata=None, **kwargs):
    if None in (parent, rawdata):
        return False

    try:
        return (
            get_set_chunk_size(parent=parent.parent) > 
            get_list_chunk_size(parent.parent.list_data)
            )
    except Exception:
        pass

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

def read_write_id3_data_size(
        parent=None, writebuffer=None, rawdata=None, offset=0, root_offset=0, **kwargs
        ):
    buffer = writebuffer if rawdata is None else rawdata
    if not parent or buffer is None:
        return

    try:
        buffer.seek(offset + root_offset)
        
        # it's weird, but here's how they define the size:
        #   The ID3 tag size is encoded with four bytes where the first bit (bit 7) 
        #   is set to zero in every byte, making a total of 28 bits. The zeroed bits 
        #   are ignored, so a 257 bytes long tag is represented as $00 00 02 01.
        if writebuffer is not None:
            buffer.write(bytes(
                (size >> (7 * (3 - i))) & 0x7F
                for i, val in enumerate([parent.frame_data_size] * 4)
                ))
        else:
            parent.frame_data_size = sum(
                (b & 0x7F) << 8*i 
                for i, b in enumerate(buffer.read(4))
                )

        return offset + 4
    except Exception:
        pass

def Chunk(name, all_sigs, sig_default, *fields, **desc):
    return Container(name,
        UEnum32("sig", 
            *((sig, sig[::-1]) for sig in all_sigs),
            DEFAULT=sig_default[::-1]
            ),
        UInt32("data_size", EDITABLE=False),
        *fields,
        **desc
        )

unknown_chunk = Chunk("unknown_chunk",
    chunk_sigs, '\x00\x00\x00\x00',
    BytesRaw("data", SIZE=chunk_extra_data_size)
    )

data_chunk = Chunk("data_chunk",
    chunk_sigs, 'data',
    BytesRaw("data", SIZE=chunk_extra_data_size)
    )


peak_position = QStruct("peak_position",
    Float("value"),
    UInt32("position"),
    )

peak_chunk = Chunk("peak",
    chunk_sigs, 'PEAK',
    UInt32("version"),
    Timestamp32("timestamp"),
    Array("peak",
        SUB_STRUCT=peak_position,
        SIZE="...wav_format.channels"
        ),
    BytesRaw("data", SIZE=peak_chunk_extra_data_size, VISIBLE=False)
    )


fact_chunk = Chunk("fact",
    chunk_sigs, 'fact',
    UInt32("sample_count"),
    BytesRaw("data", SIZE=fact_chunk_extra_data_size, VISIBLE=False)
    )


adtl_sub_chunk = Chunk("label",
    list_adtl_type_sigs, "\x00\x00\x00\x00",
    BytesRaw("data", SIZE=chunk_extra_data_size, VISIBLE=False)
    )

info_sub_chunk = Chunk("list_info",
    list_info_type_sigs, "\x00\x00\x00\x00",
    StrLatin1("info", SIZE=get_set_chunk_size),
    )

list_chunk = Chunk("list_chunk",
    chunk_sigs, 'LIST',
    UEnum32("list_type_sig", 
        *((sig, sig[::-1]) for sig in list_type_sigs)
        ),
    Switch("list_data",
        CASE=".list_type_sig.enum_name",
        CASES={
            "INFO": WhileArray("list_data", 
                SUB_STRUCT=info_sub_chunk, 
                CASE=has_next_list_sub_chunk
                ),
            "adtl": WhileArray("list_data", 
                SUB_STRUCT=adtl_sub_chunk, 
                CASE=has_next_list_sub_chunk
                )
            }
        )
    )


id3_chunk = Chunk("id3_chunk",
    chunk_sigs, 'id3 ',
    # what the fuck is up with this spec? it's like it was written by a
    # sanitarium patient. Look at the comment in read_write_id3_data_size
    # to get an idea. anyway, the spec is here:
    #   https://mutagen-specs.readthedocs.io/en/latest/id3/id3v2.2.html#id3v2-header
    UInt24("id3_sig", DEFAULT="ID3", EDITABLE=False, ENDIAN=">"),
    UInt8("version"),
    UInt8("revision"),
    Bool8("flags",
        "uses_unsynchronisation",
        "uses_compression",
        ),
    # okay so, this value was designed by essentially a skooma
    # eater, so you'll have to bear with how it's calculated. 
    WritableComputed("frame_data_size",
        COMPUTE_READ=read_write_id3_data_size, 
        COMPUTE_WRITE=read_write_id3_data_size,
        SIZE=4, EDITABLE=False, MAX=((1<<27) - 1)
        ),
    # yeah so, the frame data spec is even more weird. we're not gonna bother
    # trying to parse it, and instead just read it as a byte string.
    BytesRaw("frame_data", SIZE=".frame_data_size", MAX=((1<<27) - 1)),
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
        "LIST": list_chunk,
        "id3 ": id3_chunk,
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
