"""
This module contains keyword constants which represent certain
attributes in tag descriptors, alignment constants, and other constants.
"""

from string import ascii_letters, digits
from os.path import join


"""##############################################"""
######      Descriptor keyword constants      ######
"""##############################################"""

CASE = "CASE"  #Specifies which descriptor to use for a Switch Field.
               #Can be a function or a path string to a neighboring value
CASES = "CASES"  #Contains all the different possible descriptors that
                 #can be used by the switch block it is enclosed in.
                 #SELECTOR chooses which key to look for the descriptor
                 #under. If the descriptor doesnt exist under that key,
                 #an error is raised. If the key is None, a VoidBlock
                 #with a Void_Desc is built instead.
NAME = "NAME"  #the name that the element is accessed by
SIZE = "SIZE"  #specifies an arrays entry count, a structs byte size, etc
SUB_STRUCT = "SUB_STRUCT"  #the object to repeat in an array
TYPE = "TYPE"  #the type of data that the entry is
VALUE = "VALUE"  #value of a specific enumerator/boolean variable


ALIGN = "ALIGN"  #specifies the alignment size for an element
INCLUDE = "INCLUDE"  #This one's a convience really. When a dict is
                     #included in a descriptor under this key, all the
                     #entries in that dict are copied into the descriptor
CARRY_OFF = "CARRY_OFF" #whether or not to carry the last offset of a block over
                        #to the parent block. used in conjunction with pointers
DEFAULT = "DEFAULT"  #used to specify what the value should be
                     #in a field when a blank structure is created
ENDIAN = "ENDIAN"  #the endianness of the data
MAX = "MAX"  #max integer/float value, array length, string length, etc
MIN = "MIN"  #min integer/float value, array length, string length, etc
OFFSET = "OFFSET"  #the offset within the structure that the data is located
                   #OFFSET is meant specifically for elements of a structure
POINTER = "POINTER"  #defines where in the data buffer to read/write to/from.
                     #The differences between POINTER and OFFSET are that
                     #OFFSET is moved over into the ATTR_OFFS dictionary in
                     #the parent struct's descriptor, whereas POINTER stays
                     #with the original descriptor. POINTER is also used
                     #relative to the Tag_Objects root_offset whereas OFFSET
                     #is used relative to the offset of the parent structure.


ENTRIES = "ENTRIES"  #the number of entries in the structure
NAME_MAP = "NAME_MAP"  #maps each attribute name to the index they are in
VALUE_MAP = "VALUE_MAP"  #need to add a description
ATTR_OFFS = "ATTR_OFFS"  #a list containing the offsets of each attribute
ORIG_DESC = "ORIG_DESC"  #when the descriptor of an object is modified,
                         #that objects descriptor is shallow copied to
                         #be unique. A ref to the original descriptor
                         #is created in the copy with this as the key


'''These next keywords are the names of the attributes in a Block'''
CHILD  = "CHILD"  #a block that is(most of the time) described by its parent.
                  #example: a block with a string CHILD could specify its length
PARENT = "PARENT"  #a reference to a block that holds and/or defines
                   #the Block. If this is the uppermost Block,
                   #then PARENT is a reference to the Tag_Object 
DESC = "DESC"  #The descriptor used to define the Block 


'''These next keywords are used in the gui struct editor that is in planning'''
GUI_NAME = "GUI_NAME"  #the displayed name of the element
EDITABLE = "EDITABLE"  #False = Entry is greyed out and uneditable
VISIBLE = "VISIBLE"  #False = Entry is not rendered when loaded
ORIENT = "ORIENT"  #which way to display the data; vertically of horizontally


#these are the keywords that shouldn't be used
#be used as an attribute name in a descriptor
tag_identifiers = set((#required keywords
                       #(some only required for certain fields)
                       CASE, CASES, NAME, SIZE, SUB_STRUCT, TYPE, VALUE,

                       #optional keywords
                       ALIGN, INCLUDE, CARRY_OFF, DEFAULT,
                       ENDIAN, MAX, MIN, OFFSET, POINTER,

                       #keywords used by the supyrs implementation
                       ENTRIES, NAME_MAP, VALUE_MAP, ATTR_OFFS, ORIG_DESC,

                       #Block attribute names
                       CHILD, PARENT, DESC,

                       #gui editor related keywords
                       GUI_NAME, EDITABLE, VISIBLE, ORIENT))

#shorthand alias
tag_ids = tag_identifiers

#Characters valid to be used in element names.
#Alpha_Numeric_IDs is used for every character after the
#first since python identifiers cant start with an integer
alpha_ids = set(ascii_letters + '_')
alpha_numeric_ids = set(ascii_letters + '_' + digits)
alpha_numeric_ids_str = ascii_letters + '_' + digits

"""###############################################"""
######      Structure alignment constants      ######
"""###############################################"""

#largest byte alignment the automatic alignment routine will choose
ALIGN_MAX = 8

#the alignment modes available
ALIGN_NONE = "ALIGN_NONE"
ALIGN_AUTO = "ALIGN_AUTO"

'''
Below list of alignment sizes was taken from the below url and modified:
    https://en.wikipedia.org/wiki/Data_structure_alignment

when compiling for 32-bit x86:
    A char (1 byte) will be 1-byte aligned.
    A short (2 bytes) will be 2-byte aligned.
    An int (4 bytes) will be 4-byte aligned.
    A long (4 bytes) will be 4-byte aligned.
    A float (4 bytes) will be 4-byte aligned.
    A double (8 bytes) will be
        8-byte aligned on Windows
        4-byte aligned on Linux
        4-byte aligned on GCC
    A long long (8 bytes) will be 8-byte aligned.
    Any pointer (4 bytes) will be 4-byte aligned
    Strings are aligned by their character size
        A char size of 1 byte will be 1-byte aligned.
        A char size of 2 bytes will be 2-byte aligned.
        A char size of 3 bytes will be 4-byte aligned.
        A char size of 4 bytes will be 4-byte aligned.

The method this handler uses for automatic alignment is
Align = 2**int(ceil(log(Size, 2)))

where Size is the byte size of the data being aligned.
If Align > ALIGN_MAX, it will be set to ALIGN_MAX, which is 8

Because of this, "doubles" must be manually specified as having 4-byte
alignment if imitating Linux or GCC, "long doubles" must be manually specified
as having 2-byte alignment if imitating DMC.
'''



"""#################################"""
######      Other constants      ######
"""#################################"""

#This is the default amount of spacing a tag
#being printed uses when indenting the blocks
BLOCK_PRINT_INDENT = BPI = 4


#the character used to divide folders on this operating system
pathdiv = join('a','b')[1:-1]

NoneType = type(None)

def_show = ('field', 'name', 'value', 'offset', 'size', 'children')
all_show = ("name", "value", "field", "offset", "children",
            "flags", "unique", "size", "index",
            #"raw", #raw data can be really bad to show so dont unless specified
            "py_id", "py_type", "binsize", "ramsize")

'''This function is in the constants because it is used in
many places within the handler(Descriptors, Tag_Types, etc)
so it needs to be in a place that is always available.'''
def combine(main_dict, *dicts, **kwargs):
    '''Combines multiple nested dicts to re-use common elements.
    If a key in the main_dict already exists, it wont be overwritten by
    the ones being combined into it. Infinite recursion is allowed and
    is handeled properly.
    
    usage = combine(main_dict, *dicts_with_common_elements)

    Returns the main_dict
    '''
    seen = kwargs.get('seen')
    if seen is None:
        seen = set((id(main_dict),))
        
    for subdict in dicts:
        seen.add(id(subdict))
        for i in subdict:
            #if the key already exists
            if i in main_dict:
                #if the entry in both the main dict and
                #the common dict is a dict, then we merge
                #entries from it into the main dict
                if (isinstance(subdict[i],   dict) and
                    isinstance(main_dict[i], dict) and
                    id(subdict[i]) not in seen):
                    
                    seen.add(id(main_dict[i]))
                    seen.add(id(subdict[i]))
                    combine(main_dict[i], subdict[i], seen = seen)
            else:
                main_dict[i] = subdict[i]
                
    return main_dict
