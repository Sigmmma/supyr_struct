from . import parsers, serializers, decoders, encoders, sizecalcs


# NOTE: These are all being imported into the module namespace to preserve
#       compatibility with the old implementation. Remove these when possible.
from .parsers import (
    container_parser, array_parser,
    struct_parser, bit_struct_parser, py_array_parser,
    data_parser, cstring_parser, bytes_parser,
    # specialized parsers
    default_parser, f_s_data_parser, computed_parser,
    switch_parser, while_array_parser, void_parser, pad_parser, union_parser,
    stream_adapter_parser, quickstruct_parser,
    # util functions
    format_parse_error
    )
from .serializers import (
    container_serializer, array_serializer,
    struct_serializer, bit_struct_serializer, py_array_serializer,
    f_s_data_serializer, data_serializer, cstring_serializer, bytes_serializer,
    # specialized serializers
    computed_serializer, void_serializer, pad_serializer, union_serializer,
    stream_adapter_serializer, quickstruct_serializer,
    # util functions
    format_serialize_error
    )
from .decoders import (
    decode_numeric, decode_string, no_decode,
    decode_big_int, decode_bit_int, decode_raw_string,
    # specialized decoders
    decode_24bit_numeric, decode_decimal, decode_bit,
    decode_timestamp, decode_string_hex,
    decoder_wrapper
    )
from .encoders import (
    encode_numeric, encode_string, no_encode,
    encode_big_int, encode_bit_int,
    # specialized encoders
    encode_24bit_numeric, encode_decimal, encode_bit, encode_raw_string,
    encode_int_timestamp, encode_float_timestamp, encode_string_hex,
    encoder_wrapper
    )
from .sizecalcs import (
    # size calculators
    no_sizecalc, def_sizecalc, len_sizecalc,
    delim_str_sizecalc, str_sizecalc,
    # specialized size calculators
    delim_utf_sizecalc, utf_sizecalc, array_sizecalc,
    big_sint_sizecalc, big_uint_sizecalc, str_hex_sizecalc,
    bit_sint_sizecalc, bit_uint_sizecalc, computed_sizecalc,
    sizecalc_wrapper
    )


__all__ = [
    'parsers', 'serializers', 'decoders', 'encoders', 'sizecalcs',

    # basic parsers
    'container_parser', 'array_parser',
    'struct_parser', 'bit_struct_parser', 'py_array_parser',
    'data_parser', 'cstring_parser', 'bytes_parser',

    # basic serializers
    'container_serializer', 'array_serializer',
    'struct_serializer', 'bit_struct_serializer', 'py_array_serializer',
    'f_s_data_serializer', 'data_serializer',
    'cstring_serializer', 'bytes_serializer',

    # basic decoders
    'decode_numeric', 'decode_string', 'no_decode',
    'decode_big_int', 'decode_bit_int', 'decode_raw_string',

    # basic encoders
    'encode_numeric', 'encode_string', 'no_encode',
    'encode_big_int', 'encode_bit_int',

    # basic size calculators
    'no_sizecalc', 'def_sizecalc', 'len_sizecalc',
    'delim_str_sizecalc', 'str_sizecalc',

    # wrapper functions
    'sizecalc_wrapper', 'encoder_wrapper', 'decoder_wrapper',



    # specialized parsers
    'default_parser', 'f_s_data_parser', 'computed_parser',
    'switch_parser', 'while_array_parser',
    'void_parser', 'pad_parser', 'union_parser',
    'stream_adapter_parser', 'quickstruct_parser',

    # specialized serializers
    'computed_serializer',
    'void_serializer', 'pad_serializer', 'union_serializer',
    'stream_adapter_serializer', 'quickstruct_serializer',

    # specialized decoders
    'decode_24bit_numeric', 'decode_decimal', 'decode_bit',
    'decode_timestamp', 'decode_string_hex',

    # specialized encoders
    'encode_24bit_numeric', 'encode_decimal', 'encode_bit', 'encode_raw_string',
    'encode_int_timestamp', 'encode_float_timestamp', 'encode_string_hex',

    # specialized size calculators
    'delim_utf_sizecalc', 'utf_sizecalc', 'array_sizecalc',
    'big_sint_sizecalc', 'big_uint_sizecalc', 'str_hex_sizecalc',
    'bit_sint_sizecalc', 'bit_uint_sizecalc', 'computed_sizecalc',

    # exception string formatters
    'format_parse_error', 'format_serialize_error'
    ]
