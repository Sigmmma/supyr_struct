'''
This module contains descriptor keyword constants, structure
alignment constants, Block printing constants, and a function
for injecting new descriptor keywords into this module.
'''

from string import ascii_letters

# PATHDIV is supyrs path separator constant
from os.path import sep as PATHDIV
from .frozen_dict import FrozenDict

# ##################################################
# ----      Descriptor keyword constants      ---- #
# ##################################################

# These are the most important and most used keywords
NAME = "NAME"  # The given name of an element. This is copied
#                into the NAME_MAP of the parent descriptor.
#                Must be a string.
TYPE = "TYPE"  # The FieldType that describes the data.
#                Must be a FieldType.
SIZE = "SIZE"  # Specifies an arrays entry count, a structs byte size,
#                the length of a string, the length of a bytes object, etc.
#                Must be an int, function, or a nodepath.
SUB_STRUCT = "SUB_STRUCT"  # The descriptor to repeat in an array or the
#                            descriptor that is wrapped in a StreamAdapter.
#                            Must be a descriptor.
CASE = "CASE"  # Specifies which descriptor to use for a Switch field.
#                Must be an int, function, or a nodepath.
#                If used in a WhileArray, this must be a function
#                and must return a bool specifying whether or not
#                another Block should be built.
CASES = "CASES"  # Contains all the different possible descriptors that can
#                  be chosen by the Union/Switch block it is enclosed in.
#                  CASE determines which key to look for the descriptor
#                  under. If the descriptor doesnt exist under that key,
#                  a VoidBlock with a void_desc is built instead.
#                  Must be a dict.
VALUE = "VALUE"  # The value of a specific enumerator/boolean option.
#                  If not specified, one will be deduced. The position 'i'
#                  is the integer key of the option in the descriptor plus
#                  the amount of padding before it. For bools, VALUE will
#                  default to '2**i'. Otherwise it will default to 'i'.
#                  Must be an int, str, or bytes.
DECODER = "DECODER"  # A function used to decode and return a Buffer for
#                      a StreamAdapter field before it is handed off
#                      to be parsed by the StreamAdapter's SUB_STRUCT.
#                      Also returns how much of the input stream was decoded.
#                      Must be a function.


# These are supplementary keywords that give more control
# over creating a structure, how and where to read/write, etc
ALIGN = "ALIGN"  # The byte size to align the offset to before reading or
#                  writing. Alignment is done using this method:
#                      offset += (align - (offset % align)) % align
#                  Must be an int.
INCLUDE = "INCLUDE"  # This one is more of a convience. When a dict is in
#                      a descriptor under this key and the descriptor is
#                      sanitized, all entries in that dict are copied into
#                      the descriptor if the entries dont already exist.
#                      Must be a dict.
DEFAULT = "DEFAULT"  # Used to specify a default node value to use when
#                      a field is being parsed without an input buffer.
#                      Must be an instance of descriptor['TYPE'].node_cls, or
#                      in other words the node_cls attribute of the TYPE entry.
BLOCK_CLS = "BLOCK_CLS"  # Specifies the Block class to be constructed
#                          when this descriptor is used to build a Block.
#                          If not provided, defaults to the node_cls attribute
#                          of the TYPE entry:
#                              descriptor['TYPE'].node_cls
#                          Must be a Block class.
ENDIAN = "ENDIAN"  # Specifies which endianness instance of a FieldType to use.
#                    This is only used by BlockDefs during their sanitization
#                    process. If not given, the FieldType that already exists
#                    in the descriptor will be used. ENDIAN is carried over
#                    into inner descriptors during the sanitization process.
#                    Valid values are '<' for little and '>' for big endian.
#                    Must be a string.
OFFSET = "OFFSET"  # The offset within the structure the data is located at.
#                    Meant specifically for struct elements. When a descriptor
#                    is sanitized, this is removed from the descriptor it is
#                    in and moved into the parent descriptors ATTR_OFFS list.
#                    Must be an int.
POINTER = "POINTER"  # Defines where in the buffer to read or write.
#                      The differences between POINTER and OFFSET are that
#                      POINTER is not removed from the descriptor it's in and
#                      POINTER is used relative to the root_offset whereas
#                      OFFSET is used relative to the offset of the parent.
#                      Must be an int, function or a nodepath.
ENCODER = "ENCODER"  # A function used to encode and return the buffer that was
#                      written to by the StreamAdapter's SUB_STRUCT attribute.
#                      This encoded buffer should be able to be decoded by this
#                      same descriptors DECODE function.
#                      Must be a function.
STEPTREE = "STEPTREE"  # A descriptor of a node which is usually described by
#                      its parent. STEPTREE nodes arent elements of a structure,
#                      but are linked  to it. They are read/written in a
#                      different order than the elements of a structure.
#                      Parsers and serializers finish processing the tree
#                      they are currently in, then proceed to read/write
#                      all steptrees encountered in the order that they
#                      were encountered.
#                      Must be a descriptor.
STEPTREE_ROOT = "STEPTREE_ROOT"  # Whether or not the current node is a root at
#                                  which to build steptrees.
#                                  If True, all nodes with STEPTREE entries
#                                  within this node will be collected and
#                                  their steptrees will be read/written at
#                                  this tree level. This descriptor keyword is
#                                  only valid to use in container FieldTypes.
#                                  Must be a bool.
DECIMAL_EXP = "DECIMAL_EXP"  # The exponent to use for Decimal numbers.
#                              The Decimal number is first read as an
#                              integer and is then converted into a string.
#                              Before the string is converted to a Decimal
#                              object, a period is inserted DECIMAL_EXP number
#                              of places from the right end of the string.
#                              Must be an int, function or a nodepath.


# These are keywords that are mainly used by supyrs implementation
# and are always autogenerated by sanitization routines.
ENTRIES = "ENTRIES"  # The number of integer keyed entries in the descriptor.
#                      Must be an int.
NAME_MAP = "NAME_MAP"  # Maps the given name of each field to the list index or
#                        __slot__ name that the field is actually stored under.
#                        Must be a dict.
CASE_MAP = "CASE_MAP"  # Maps the given case value of each sub-descriptor
#                        in a Union or Switch descriptor to the index it
#                        is stored under.
#                        Must be a dict.
VALUE_MAP = "VALUE_MAP"  # Maps the given value of each possible enumeration
#                          value to the index that specific options descriptor
#                          is located in. This serves to enable a flat lookup
#                          time when trying to determine which enumerator
#                          option is selected.
#                          Must be a dict.
ATTR_OFFS = "ATTR_OFFS"  # A list containing the offset of each of structs
#                          attributes. Must be a list.
ADDED = "ADDED"  # A freeform entry that is neither expected to exist,
#                  nor have any specific structure. It is ignored by the
#                  sanitizer routine and is primarily meant for allowing
#                  developers to add their own data to a descriptor without
#                  having to make a new descriptor keyword for it.
#                  Can be anything.


# This is a set of all the keywords above, and can be used
# to determine if a string is a valid descriptor keyword.
desc_keywords = set(
    # required keywords
    (NAME, TYPE, SIZE, SUB_STRUCT,
     CASE, CASES, VALUE, DECODER,

     # optional keywords
     ALIGN, INCLUDE, DEFAULT, BLOCK_CLS, ENDIAN, OFFSET,
     POINTER, ENCODER, STEPTREE, STEPTREE_ROOT, DECIMAL_EXP,

     # keywords used by supyrs implementation
     ENTRIES, CASE_MAP, NAME_MAP, VALUE_MAP, ATTR_OFFS, ADDED)
    )

# This set contains all descriptor keys whose key value should never have
# its integer keyed items counted(the key value must be a dict to count them).
# If they are counted, an ENTRIES item will be added whose value is the count.
# Most of these dont key to a dict, but are included anyway for completeness.
uncountable_desc_keys = set(
    (NAME, TYPE, SIZE, CASE, CASES, VALUE, ALIGN,
     INCLUDE, BLOCK_CLS, ENDIAN, OFFSET, POINTER,
     DECODER, ENCODER, STEPTREE_ROOT, DECIMAL_EXP, ENTRIES,
     CASE_MAP, NAME_MAP, VALUE_MAP, ATTR_OFFS, ADDED)
    )

# Shorthand alias for desc_keywords
desc_kw = desc_keywords

# A set of strings that cant be used as a NAME entry
# in a descriptor. These are either descriptor keywords
# themselves, a __slots__ name, or a Block method.
reserved_desc_names = set(desc_kw)

# Pad will use this as its default name when creating an unsanitized descriptor
reserved_desc_names.add("_")

# update with slot names found in Block __slots__ which would cause conflicts
reserved_desc_names.update(('desc', 'parent', 'u_index'))

# update with python magic method names
reserved_desc_names.update(
    ('__getitem__', '__setitem__', '__delitem__', '__iter__', '__next__',
     '__missing__', '__reversed__', '__len__', '__contains__', '__index__',
     '__get_attr__', '__set_attr__', '__del_attr__', '__bytes__',
     '__get__', '__set__', '__del__', '__copy__', '__deepcopy__', '__hash__',
     '__instancecheck__', '__subclasscheck__', '__subclasshook__',

     '__init__', '__repr__', '__str__', '__new__', '__dir__', '__call__',
     '__format__', '__main__', '__name__', '__sizeof__',

     '__add__',  '__sub__',  '__mul__',  '__truediv__',  'floordiv__',
     '__radd__', '__rsub__', '__rmul__', '__rtruediv__', '__rfloordiv__',

     '__mod__',  '__divmod__',  '__pow__',  '__lshift__',  '__rshift__',
     '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__',

     '__and__',  '__xor__',  '__or__', '__rand__', '__rxor__', '__ror__',

     '__iadd__', '__isub__', '__imul__', '__itruediv__', '__ifloordiv__',
     '__imod__', '__ipow__', '__ilshift__', '__irshift__',
     '__iand__', '__ixor__', '__ior__', '__neg__', '__pos__',
     '__abs__', '__invert__', '__complex__', '__int__', '__float__',

     '__round__', '__ceil__', '__floor__', '__trunc__',

     '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__', '__bool__',
     '__getstate__', '__setstate__', '__reduce__', '__reduce_ex__',
     '__getnewargs__', '__enter__', '__exit__'))

# update with methods found in Block
reserved_desc_names.update(
    ('__binsize__',  'binsize',
     'attr_to_str', 'validate_name',
     'get_root', 'get_neighbor', 'set_neighbor',
     'get_desc', 'get_meta', 'set_meta',
     'collect_pointers', 'set_pointers',
     'parse', 'serialize', 'pprint'))

# update with methods found in ListBlock
reserved_desc_names.update(
    ('append', 'extend', 'insert', 'pop',
     'index_by_id', 'get_size', 'set_size'))

# update with methods found in UnionBlock
reserved_desc_names.update(('set_active',))

# Characters valid to be used in element names.
# ALPHA_NUMERIC_IDS is used for every character after the
# first since python identifiers cant start with an integer
ALPHA_IDS = frozenset(ascii_letters + '_')
ALPHA_NUMERIC_IDS_STR = ascii_letters + '_' + '0123456789'
ALPHA_NUMERIC_IDS = frozenset(ALPHA_NUMERIC_IDS_STR)


# Strings used when printing Blocks and errors
UNNAMED = "<UNNAMED>"
INVALID = "<INVALID>"
RAWDATA = "<RAWDATA>"
UNPRINTABLE = "<UNABLE TO PRINT LINE>"
SIZE_CALC_FAIL = "<COULD NOT CALCULATE PACKED SIZE>"
RECURSIVE = "<RECURSIVE BLOCK '%s' ID %s>"
MISSING_DESC = "<NO DESCRIPTOR FOR OBJECT OF TYPE %s>"

# for use in union_block.UnionBlock.set_active
NoneType = type(None)

# ###################################################
# ----      Structure alignment constants      ---- #
# ###################################################

# The largest byte alignment the automatic alignment routine will choose
ALIGN_MAX = 8

# The alignment modes available
ALIGN_NONE = 0
ALIGN_AUTO = 1

# The algorithm this library uses for automatic alignment is
# align = 2**int(ceil(log(data_size, 2)))
#
# Because of this, "doubles" must be manually defined as having
# 4-byte alignment if imitating Linux or GCC, "long doubles" must be
# manually defined as having 2-byte alignment if imitating DMC.


# ######################################
# ----       Other constants      ---- #
# ######################################

# This is the default amount of spacing a node
# being printed uses when indenting the nodes
NODE_PRINT_INDENT = BPI = 4


# the minimal things to show in a block
MIN_SHOW = frozenset(('type', 'name', 'value', 'steptrees'))

# The default things to show when printing a Block or Tag
DEF_SHOW = frozenset(('type', 'name', 'value', 'offset',
                      'flags', 'size', 'steptrees', 'trueonly'))

# the most important things to show
MOST_SHOW = frozenset(
    ("name", "value", "type", "offset",
     "steptrees", "flags", "size", "index",
     "filepath", "binsize", "ramsize"))

# The things shown when printing a Block or Tag
# and one of the strings in 'show' is 'all'.
ALL_SHOW = frozenset(
    ("name", "value", "type", "offset", "steptrees",
     "flags", "unique", "size", "index", "raw", "filepath",
     "parent_id", "node_id", "node_cls", "binsize", "ramsize"))

SHOW_SETS = FrozenDict(
    min=MIN_SHOW,
    default=DEF_SHOW,
    most=MOST_SHOW,
    all=ALL_SHOW)


def add_desc_keywords(*keywords):
    '''
    Adds the supplied positional arguments to the desc_keywords and
    reserved_desc_names sets and to this objects global namespace.

    Used for when you need to add new descriptor keywords.
    '''
    g = globals()
    for kw in keywords:
        g[kw] = kw
        desc_keywords.add(kw)
        reserved_desc_names.add(kw)

# cleanup
del ascii_letters
