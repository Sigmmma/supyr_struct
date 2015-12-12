"""
This module contains keyword constants which represent certain
attributes in tag descriptors, alignment constants, and other constants.
"""

from string import ascii_letters, digits


"""##############################################"""
######      Descriptor keyword constants      ######
"""##############################################"""

TYPE = "TYPE"  #the type of data that the entry is
ENDIAN = "ENDIAN"  #the endianness of the data
ENTRIES = "ENTRIES"  #the number of entries in the structure
NAME = "NAME"  #the name that the element is accessed by
SIZE = "SIZE"  #specifies an arrays entry count, a structs byte size, etc
PAD = "PAD"  #specifies how much padding to put between entries in a structure.
             #if put inside an entry in a struct, the entry's offset will be
             #incremented by the padding amount. if inside a struct, PAD is
             #removed from the entry it is located in. If PAD is in a dictionary
             #by itself the entire dictionary entry will be removed and the
             #next entries in the struct will have their indexes decremented.

OFFSET = "OFFSET"  #the offset within the structure that the data is located
                   #OFFSET is meant specifically for elements of a structure
POINTER = "POINTER"  #defines where in the data buffer to read/write to/from.
                     #The differences between POINTER and OFFSET are that
                     #OFFSET is moved over into the ATTR_OFFSETS dictionary in
                     #the parent struct's descriptor, whereas POINTER stays
                     #with the original descriptor. POINTER is also used
                     #relative to the Tag_Objects Root_Offset whereas OFFSET
                     #is used relative to the offset of the parent structure.
ALIGN = "ALIGN"  #specifies the alignment size for an element
CARRY_OFF = "CARRY_OFF" #whether or not to carry the last offset of a block over
                        #to the parent block. used in conjunction with pointers
SUB_STRUCT = "SUB_STRUCT"  #the object to repeat in an array
CHILD_ROOT = "CHILD_ROOT"  #child blocks will be built from this point if True

ELEMENTS = "ELEMENTS" #a dict that contains the individual enumerator elements
FLAGS = "FLAGS"  #a dict that contains the individual booleans
VALUE = "VALUE"  #value of a specific enumerator/boolean variable
MAX = "MAX"  #max integer/float value, array length, string length, etc
MIN = "MIN"  #min integer/float value, array length, string length, etc
DEFAULT = "DEFAULT"  #used to specify what the value should be
                     #in a field when a blank structure is created

ATTR_MAP = "ATTR_MAP"  #maps each attribute name to the index they are in
ATTR_OFFSETS = "ATTR_OFFSETS"  #a list containing the offsets of each attribute
ATTRIBUTES = "ATTRIBUTES"  #This one's a convience really. When a dict is
                           #included in a descriptor using this key, all the
                           #elements in that dict are copied into the descriptor
ORIG_DESC = "ORIG_DESC"  #when the descriptor of an object is modified,
                         #that objects descriptor is shallow copied to
                         #be unique. A ref to the original descriptor
                         #is created in the copy with this as the key

'''These next keywords are the names of the attributes in a Tag_Block'''
CHILD  = "CHILD" #a block that is(most of the time) described by its parent.
                 #example: a block with a string CHILD could specify its length
PARENT = "PARENT"  #a reference to a block that holds and/or defines
                   #the Tag_Block. If this is the uppermost Tag_Block,
                   #then PARENT is a reference to the Tag_Object 
DESC = "DESC"  #The descriptor used to define the Tag_Block 

'''These next keywords are used in the gui struct editor that is in planning'''
GUI_NAME = "GUI_NAME"  #the displayed name of the element
EDITABLE = "EDITABLE"  #False = Entry is greyed out and uneditable
VISIBLE = "VISIBLE"  #False = Entry is not rendered when loaded
ORIENT = "ORIENT"  #which way to display the data; vertical of horizontal



#these are the keywords that shouldn't be used
#be used as an attribute name in a descriptor
Tag_Identifiers = set([TYPE, ENDIAN, ENTRIES, NAME, SIZE, PAD,
                       OFFSET, POINTER, ALIGN, CARRY_OFF,
                       SUB_STRUCT, CHILD_ROOT,
                       CHILD, PARENT, DESC,
                       GUI_NAME, EDITABLE, VISIBLE, ORIENT,
                       ELEMENTS, FLAGS, VALUE, MAX, MIN, DEFAULT,
                       ATTR_MAP, ATTR_OFFSETS, ATTRIBUTES, ORIG_DESC])

#Characters valid to be used in element names.
#Alpha_Numeric_IDs is used for every character after the
#first since python identifiers cant start with an integer
Alpha_IDs = set(ascii_letters + '_')
Alpha_Numeric_IDs = set(ascii_letters + '_' + digits)


"""###############################################"""
######      Structure alignment constants      ######
"""###############################################"""

#largest byte alignment the automatic alignment routine will choose
ALIGN_MAX = 8

#the alignment modes available
ALIGN_NONE = "ALIGN_NONE"
ALIGN_AUTO = "ALIGN_AUTO"

ALIGN_MODES = ( ALIGN_NONE, ALIGN_AUTO )

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

The method this library uses for automatic alignment is
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

'''This function is in the constants because it is used in
many places within the library(Descriptors, Tag_Types, etc)
so it needs to be in a place that is always available.'''
def Combine(Main_Dict, *Dicts, **kwargs):
    '''Combines multiple nested dicts to re-use common elements.
    If a key in the Main_Dict already exists, it wont be overwritten by
    the ones being combined into it. Infinite recursion is allowed and
    will be handeled properly.
    
    usage = Combine(Main_Dict, *Dicts_with_common_elements)

    Returns the Main_Dict
    '''
    if "Seen" not in kwargs:
        kwargs["Seen"] = list(Main_Dict)
        kwargs["Seen"].extend(Dicts)
        
    for Dict in Dicts:
        for key in Dict:
            #if the key already exists
            if key in Main_Dict:
                #if the entry in both the main dict and the common dict is
                #a dict, then we merge entries from it into the main dict
                if (isinstance(Dict[key], dict) and
                    isinstance(Main_Dict[key], dict) and
                    Dict[key] not in kwargs["Seen"]):
                    
                    kwargs["Seen"].append(Main_Dict[key])
                    kwargs["Seen"].append(Dict[key])
                    Combine(Main_Dict[key], Dict[key], **kwargs)
            else:
                Main_Dict[key] = Dict[key]
                
    return Main_Dict
