'''docstring'''
import sys

from math import log, ceil
from copy import copy

from supyr_struct.defs.descriptor import Descriptor
from supyr_struct.defs.constants import *
from supyr_struct.defs.common_descriptors import *

def get():
    '''
    This function exists as a common entry point to
    construct a Tag_Def. All Tag_Def class modules
    should have a 'Construct' function so they can all be
    located by a Tag_Constructors automatic indexing function.
    '''
    
    return TagDef


class TagDef():
    '''docstring'''
    
    #The alignment method to use for aligning structures and
    #their entries to byte boundaries based on each ones size.
    align = ALIGN_NONE
    
    #used for identifying a tag and for telling the tag
    #constructor which tag you are telling it to build.
    #Each tag_id must be unique for each Tag_Def
    tag_id = ""
    
    #The default endianness to use for every field in the tag
    #This can be overridden by specifying the endianness per field
    endian = { 'big':'>', 'little':'<' }.get(sys.byteorder.lower(), '<')
    
    #primarily used for locating tags when indexing a collection of
    #them, but also used as the extension when writing a tag to a file
    ext = ".tag"
    
    #specifies that the object is only partially defined and any edits to
    #it must be done to a copy of the original data in order to keep all of
    #the undefined data intact. descriptors SHOULD NEVER be added or deleted
    #from an incomplete object, though you are not prevented from doing so.
    incomplete = False
    
    #whether or not to add GUI_NAME entries to each
    #descriptor by converting NAME into a GUI_NAME.
    make_gui_names = False
    
    #used for storing individual or supplementary pieces of the structure
    descriptors = {}
    
    #The class to use to build this definitions Tag from
    tag_cls = None
    
    #used for describing the structure of a tag.
    #this is where everything about the structure is defined.
    descriptor = {}
    
    #whether or not to print sanitization warnings(not errors)
    #to the user when the sanitization routine is run
    sani_warn = True

    #initialize the class
    def __init__(self, **kwargs):
        '''docstring'''

        if not hasattr(self, "ext"):
            self.ext = kwargs.get("ext", ".tag")
        if not hasattr(self, "tag_id"):
            self.tag_id = kwargs.get("tag_id", "")
        if not hasattr(self, "descriptor"):
            self.descriptor = kwargs.get("descriptor", {})
        if not hasattr(self, "tag_cls"):
            self.tag_cls = kwargs.get("tag_cls", None)
        if not hasattr(self, "incomplete"):
            self.incomplete = kwargs.get("incomplete", False)
        if not hasattr(self, "align"):
            self.align = kwargs.get("align", ALIGN_NONE)
        if not hasattr(self, "descriptors"):
            self.descriptors = {}
        if not hasattr(self, "endian"):
            self.endian = kwargs.get("endian", { 'big':'>', 'little':'<' }.\
                                     get(sys.byteorder.lower(), '<'))
        
        #Used to signal to the sanitize() function that some
        #kind of error was encountered during sanitization.
        self._bad = False

        #make sure the endian value is valid
        assert self.endian in ('<','>')
        
        sani = self.sanitize
        
        if self.descriptor:
            self.descriptor = Descriptor(sani(self.descriptor))
            
        if isinstance(self.descriptors, dict):
            for key in self.descriptors:
                self.descriptors[key] = Descriptor(sani(self.descriptors[key]))

    def decode_value(self, value, key=None, p_name=None, p_field=None,**kwargs):
        '''docstring'''
        endian = {'>':'big', '<':'little'}[kwargs.get('end', self.endian)]
        if isinstance(value, bytes):
            try:
                if p_field is not None:
                    value = p_field.decoder(value)
                elif endian == '<':
                    value = int.from_bytes(value, 'little')
                else:
                    value = int.from_bytes(value, 'big')
            except Exception:
                print(("ERROR: UNABLE TO DECODE THE BYTES %s IN '%s' "+
                       "OF '%s' AS '%s'.\n") %(value, key, p_name, p_field))
                self._bad = True
        elif (isinstance(value, str) and (issubclass(p_field.data_type, int) or
              (issubclass(p_field.py_type, int) and
               issubclass(p_field.data_type, type(None))) )):
            #if the value is a string and the field's data_type is an int, or
            #its py_type is an int and its data_type is type(None), then
            #convert the string into bytes and then the bytes into an integer

            if endian == 'little':
                value = ''.join(reversed(value))

            value = int.from_bytes(bytes(value, encoding='latin1'),
                                   byteorder=endian)
        return value

    def find_errors(self, src_dict, **kwargs):
        '''Returns a string textually describing any errors that were found.'''
        #Get the name of this block so it can be used in the below routines
        p_name     = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        p_field    = src_dict.get(TYPE)
        cont_field = kwargs.get('p_field')
            
        error_str = ''
        

        if src_dict.get(ENDIAN, '<') not in '<>':
            error_str += ("ERROR: ENDIANNESS CHARACTERS MUST BE "+
                          "EITHER '<' FOR LITTLE ENDIAN OR '>' FOR "+
                          "BIG ENDIAN. NOT  %s\n" % kwargs.get('end'))
            
        #checks to make sure bit and byte level fields arent mixed improperly
        if (isinstance(cont_field, fields.Field) and
            cont_field.is_bit_based and cont_field.is_struct):
            #Parent is a bitstruct
            if not p_field.is_bit_based:
                #but this is bitbased
                error_str += ("ERROR: Bit_Structs MAY ONLY CONTAIN "+
                              "Bit_Based 'Data' fields.\n")
            elif p_field.is_struct:
                error_str += "ERROR: Bit_Structs CANNOT CONTAIN Structs.\n"
        elif p_field.is_bit_based and not p_field.is_struct:
            error_str += ("ERROR: Bit_Based fields MUST "+
                          "RESIDE IN A Bit_Based Struct.\n")
            
        if not p_field.is_struct and kwargs.get('substruct'):
            '''Check to make sure this data type is valid to be
            inside a structure if it currently is inside one.'''
            if p_field.is_container:
                error_str += ("ERROR: Containers CANNOT BE USED IN A "+
                              "Struct.\nStructs ARE REQUIRED TO BE "+
                              "A FIXED SIZE AND Containers ARE NOT.\n")
        
            elif (p_field.is_var_size and
                  not isinstance(src_dict.get(SIZE), (int, bytes))):
                error_str += ("ERROR: TO USE Var_Size DATA IN A "+
                              "Struct THE SIZE MUST BE STATICALLY "+
                              "DEFINED WITH AN INTEGER.\n")
        if p_field.is_array:
            kwargs["subarray"] = True
            if not(p_field.is_oe_size or SIZE in src_dict):
                error_str += ("ERROR: NON-OPEN ENDED Arrays MUST HAVE "+
                              "A SIZE DEFINED IN THEIR DESCRIPTOR.\n")
        if error_str:
            error_str += ("    NAME OF THE OFFENDING ELEMENT IS " +
                          "'%s' OF TYPE '%s'\n" % (p_name, p_field.name))

        return error_str

    def get_align(self, src_dict, key):
        this_dict = src_dict[key]
        field = this_dict.get(TYPE)
        size = align = 1

        if field.is_raw:
            size = 1
        elif field.is_data or (field.is_bit_based and field.is_struct):
            '''if the entry is data(or a bitstruct) then align
            it by its size, or by char size if its a string'''
            if field.is_str:
                size = field.size
            else:
                size = self.get_size(src_dict, key)
        elif field.is_array:
            try:
                align = self.get_align(src_dict[key], SUB_STRUCT)
            except Exception:
                pass
        elif field.is_struct:
            '''search through all entries in the struct
            to find the largest alignment and use it'''
            align = 1
            for i in range(this_dict.get(ENTRIES, 1)):
                algn = self.get_align(this_dict, i)
                if algn > align: align = algn
                #early return for speedup
                if align >= ALIGN_MAX:
                    return ALIGN_MAX
        
        if ALIGN in this_dict:
            #alignment is specified manually
            align = this_dict[ALIGN]
        elif self.align == ALIGN_AUTO and size > 0:
            #automatic alignment is to be used
            align = 2**int(ceil(log(size, 2)))
            if align > ALIGN_MAX:
                align = ALIGN_MAX

        return align


    def get_endian(self, src_dict, **kwargs):
        '''Returns the proper endianness of the field type'''
        p_field = src_dict[TYPE]
        
        if ENDIAN in src_dict:
            end = src_dict[ENDIAN]
        elif 'end' in kwargs:
            end = kwargs['end']
        else:
            end = self.endian
            
        p_field = {'>':p_field.big, '<':p_field.little}.get(end)
        return p_field, end
    

    def get_size(self, src_dict, key):
        '''docstring'''
        this_dict = src_dict[key]
        field    = this_dict[TYPE]

        #make sure we have names for error reporting
        p_name = src_dict.get(NAME,  src_dict.get(GUI_NAME,  UNNAMED))
        name   = this_dict.get(NAME, this_dict.get(GUI_NAME, UNNAMED))
            
        if ((field.is_var_size and field.is_data) or
            (SIZE in this_dict and isinstance(this_dict[SIZE], int)) ):
            if SIZE not in this_dict:
                print("ERROR: Var_Size DATA MUST HAVE ITS SIZE SPECIFIED IN "+
                      "ITS DESCRIPTOR.\n    OFFENDING ELEMENT FOUND IN "+
                      "'%s' AND NAMED '%s'.\n" % (p_name, name))
                self._bad = True
                return 0
                
            size = this_dict[SIZE]
        elif field.is_struct:
            size = 0
            try:
                for i in range(this_dict[ENTRIES]):
                    size += self.get_size(this_dict, i)
            except Exception:
                pass
        else:
            size = field.size

        if (field.is_bit_based and not field.is_struct and not
            src_dict[TYPE].is_bit_based):
            size = int(ceil(size/8))
            
        return size


    def include_attributes(self, src_dict):
        '''docstring'''
        #combine the entries from INCLUDE into the dictionary
        if isinstance(src_dict.get(INCLUDE), dict):
            for i in src_dict[INCLUDE]:
                #dont replace it if an attribute already exists there
                if i not in src_dict:
                    src_dict[i] = src_dict[INCLUDE][i]
            del src_dict[INCLUDE]
            self.sanitize_entry_count(src_dict)

    def bool_enum_sanitizer(self, src_dict, **kwargs):
        ''''''
        p_field = src_dict[TYPE]
        
        nameset = set()
        src_dict['NAME_MAP'] = {}
        if p_field.is_enum:
            src_dict['VALUE_MAP'] = {}
        
        '''Need to make sure there is a value for each element'''
        self.sanitize_entry_count(src_dict)
        self.sanitize_element_ordering(src_dict)
        self.sanitize_option_values(src_dict, p_field, **kwargs)
            
        for i in range(src_dict['ENTRIES']):
            name = self.sanitize_name(src_dict, i)
            if name in nameset:                            
                print(("ERROR: DUPLICATE NAME FOUND IN %s.\n"
                      +"NAME OF OFFENDING ELEMENT IS %s") %
                      (kwargs["key_name"], name))
                self._bad = True
                continue
            src_dict['NAME_MAP'][name] = i
            if p_field.is_enum:
                src_dict['VALUE_MAP'][src_dict[i]['VALUE']] = i
            nameset.add(name)
        #the dict needs to not be modified by the below code
        return src_dict
    

    def sequence_sanitizer(self, src_dict, **kwargs):
        """Loops through each of the numbered entries in the descriptor.
        This is done separate from the non-integer dict entries because
        a check to sanitize offsets needs to be done from 0 up to ENTRIES.
        Looping over a dictionary by its keys will do them in a non-ordered
        way and the offset sanitization requires them to be done in order."""
        
        #if a variable doesnt have a specified offset then
        #this will be used as the starting offset and will
        #be incremented by the size of each variable after it
        def_offset = 0
        #the largest alignment size requirement of any entry in this block
        l_align = 1
        
        p_field = src_dict[TYPE]
        p_name  = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        
        nameset = set()
        removed = 0 #number of dict entries removed
        key     = 0

        '''if the block is a ListBlock, but the descriptor requires that
        it have a CHILD attribute, set the DEFAULT to a PListBlock.
        Only do this though, if there isnt already a default set.'''
        if (issubclass(p_field.py_type, blocks.ListBlock)
            and 'CHILD' in src_dict and 'DEFAULT' not in src_dict
            and not issubclass(p_field.py_type, blocks.PListBlock)):
            src_dict['DEFAULT'] = blocks.PListBlock

        '''if the block is a WhileBlock, but the descriptor requires that
        it have a CHILD attribute, set the DEFAULT to a PWhileBlock.
        Only do this though, if there isnt already a default set.'''
        if (issubclass(p_field.py_type, blocks.WhileBlock)
            and 'CHILD' in src_dict and 'DEFAULT' not in src_dict
            and not issubclass(p_field.py_type, blocks.PWhileBlock)):
            src_dict['DEFAULT'] = blocks.PWhileBlock
        
        '''loops through the entire descriptor and
        finalizes each of the integer keyed attributes'''
        for key in range(src_dict[ENTRIES]):
            this_dict = src_dict[key]
            
            if isinstance(this_dict, dict):
                #Make sure to shift upper indexes down by how many
                #were removed and make a copy to preserve the original
                this_dict = src_dict[key-removed] = dict(this_dict)
                key -= removed
                
                field = this_dict.get(TYPE)
                
                if field is Pad:
                    '''the dict was found to be padding, so increment
                    the default offset by it, remove the entry from the
                    dict, and adjust the removed and entry counts.'''
                    size = this_dict.get(SIZE)
                    if size is None:
                        self._bad = True
                        print(("ERROR: Pad ENTRY IN '%s' OF TYPE '%s' AT "+
                               "INDEX %s IS MISSING ITS SIZE KEY.")
                               % (p_name, src_dict[TYPE], key) )
                    def_offset += size
                        
                    removed += 1
                    src_dict[ENTRIES] -= 1
                    continue

                if field is not None:
                    '''make sure the block has an offset if it needs one'''
                    if p_field.is_struct and OFFSET not in this_dict:
                        this_dict[OFFSET] = def_offset
                elif p_field:
                    self._bad = True
                    print("ERROR: DESCRIPTOR FOUND THAT IS MISSING ITS "+
                          " TYPE IN '%s' OF TYPE '%s' AT INDEX %s ."
                          % (p_name, src_dict[TYPE], key) )
                        
                kwargs["key_name"] = key
                this_dict = self.sanitize_loop(this_dict, **kwargs)

                if field:
                    sani_name = self.sanitize_name(src_dict, key, **kwargs)
                    src_dict[NAME_MAP][sani_name] = key
                    
                    name = this_dict[NAME]
                    if name in nameset:
                        print(("ERROR: DUPLICATE NAME FOUND IN '%s'.\n"
                              +"    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                              (p_name, name))
                        self._bad = True
                    nameset.add(name)

                    #get the size of the entry(if the parent dict requires)
                    if ATTR_OFFS in src_dict:
                        size = self.get_size(src_dict, key)
                        
                    '''add the offset to ATTR_OFFS in the parent dict'''
                    if ATTR_OFFS in src_dict and OFFSET in this_dict:
                        #if bytes were provided as the offset we decode
                        #them and replace it with the decoded version
                        offset = self.decode_value(this_dict[OFFSET],
                                                   OFFSET, name, field,
                                                   end=kwargs.get('end'))

                        #make sure not to align within bit structs
                        if not(field.is_bit_based and p_field.is_bit_based):
                            align = self.get_align(src_dict, key)
                        
                            if align > ALIGN_MAX:
                                align = ALIGN_MAX
                            if align > l_align:
                                l_align = align
                            if align > 1:
                                offset += (align-(offset%align))%align
                                
                        def_offset = offset + size

                        #set the offset and delete the OFFSET entry
                        src_dict[ATTR_OFFS][key] = offset
                        del this_dict[OFFSET]

        #if there were any removed entries (padding) then the
        #ones above where the last key was need to be deleted
        if removed > 0:
            for i in range(key+1, key+removed+1):
                '''If there is padding on the end then it will
                have already been removed and this will cause
                a keyerror. If that happens, just ignore it.'''
                try:
                    del src_dict[i]
                except KeyError:
                    pass
            
        if ATTR_OFFS in src_dict:
            src_dict[ATTR_OFFS] = src_dict[ATTR_OFFS][:key+1]
                        
        #Make sure all structs have a defined SIZE
        if (p_field is not None and p_field.is_struct and
            src_dict.get(SIZE) is None):
            if p_field.is_bit_based:
                def_offset = int(ceil(def_offset/8))
                
            #calculate the padding based on the largest alignment
            padding = (l_align-(def_offset%l_align))%l_align
            src_dict[SIZE] = def_offset + padding

        return src_dict
    

    def standard_sanitizer(self, src_dict, **kwargs):
        ''''''
        p_field = src_dict[TYPE]
        p_name  = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        
        '''The non integer entries aren't substructs
        or subarrays, so set these both to False.'''
        kwargs['substruct'] = kwargs['subarray'] = False
        
        #loops through the descriptors non-integer keyed sub-sections
        for key in src_dict:
            if not isinstance(key, int):
                if key not in tag_identifiers and self.sani_warn:
                    print(("WARNING: FOUND ENTRY IN DESCRIPTOR OF '%s' UNDER "+
                           "UNKNOWN KEY '%s' OF TYPE %s.\n    If this is "+
                           "intentional, add the key to supyr_struct."+
                           "constants.Tag_Ids.\n") %(p_name, key, type(key)))
                if isinstance(src_dict[key], dict):
                    kwargs["key_name"] = key
                    field = src_dict[key].get(TYPE)
                    
                    #replace with the modified copy so the original is intact
                    src_dict[key] = self.sanitize_loop(src_dict[key], **kwargs)

                    if field:
                        #if this is the repeated substruct of an array
                        #then we need to calculate and set its alignment
                        if ((key == SUB_STRUCT or field.is_str) and
                            ALIGN not in src_dict[key]):
                            align = self.get_align(src_dict, key)
                            #if the alignment is 1 then no
                            #adjustments need be made
                            if align > 1:
                                src_dict[key][ALIGN]
                            
                        sani_name = self.sanitize_name(src_dict, key, **kwargs)
                        if key != SUB_STRUCT:
                            src_dict[NAME_MAP][sani_name] = key
        return src_dict


    def switch_sanitizer(self, src_dict, **kwargs):
        '''if the descriptor is a switch, the individual cases need to
        be checked and setup as well as the pointer and defaults.'''
        p_field = src_dict[TYPE]
        p_name  = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        
        #make a copy of the cases so they can be modified
        cases = src_dict['CASES'] = dict(src_dict.get('CASES',[]))
        
        if src_dict.get('CASE') is None:
            print("ERROR: CASE MISSING IN %s OF TYPE %s\n"%(p_name, p_field))
            self._bad = True
        if cases is None:
            print("ERROR: CASES MISSING IN %s OF TYPE %s\n"%(p_name, p_field))
            self._bad = True

        #make sure there is a default 
        del src_dict['NAME_MAP']
        del src_dict['ENTRIES']

        pointer = src_dict.get('POINTER')

        kwargs['key_name'] = 'CASES'
        for case in cases:
            #copy the case's descriptor so it can be modified
            case_desc = dict(cases[case])
            
            #copy the pointer from the switch into each case's desc
            if pointer is not None:
                case_desc['POINTER'] = pointer
                
            cases[case] = self.sanitize_loop(case_desc, **kwargs)
            field = cases[case][TYPE]
            if not issubclass(field.py_type, blocks.Block):
                print("ERROR: CANNOT USE CASES IN A Switch WHOSE "+
                      "Field.py_type IS NOT A Block.\n"+
                      ("OFFENDING ELEMENT IS %s IN '%s' OF '%s' "+
                       "OF TYPE %s.") % (case, CASES, p_name, field) )
                self._bad = True
            self.sanitize_name(cases, case, **kwargs)
            
        kwargs['key_name'] = 'DEFAULT'
        src_dict['DEFAULT'] = self.sanitize_loop(src_dict.get('DEFAULT',
                                                 void_desc), **kwargs)
        
        #copy the pointer from the switch into the defaults desc
        if pointer is not None:
            src_dict['DEFAULT']['POINTER'] = pointer
        
        #the dict needs to not be modified by the below code
        return src_dict


    def sanitize(self, desc):
        '''Use this to sanitize a descriptor.
        Adds key things to the Tag_Def that may be forgotten,
        mistyped, or simply left out and informs the user of
        potential and definite issues through print().'''

        #reset the error status to normal
        self._bad = False
        #enclosing the descriptor in a dictionary is necessary for
        #it to properly set up the topmost level of the descriptor
        try:
            struct_cont = self.sanitize_loop({TYPE:Container,NAME:"tmp",0:desc},
                                             key_name=None, end=self.endian)
        except Exception:
            raise Exception(("The '%s' Tag_Def encountered the above error "+
                             "during its construction.") % self.tag_id)

        #if an error occurred while sanitizing, raise an exception
        if self._bad:
            raise Exception(("The '%s' Tag_Def encountered errors "+
                             "during its construction.") % self.tag_id)
        
        return struct_cont[0]
        

    def sanitize_loop(self, src_dict, **kwargs):
        '''docstring'''
        #if the src_dict is a Descriptor, assume it is
        #already sanitized, make it mutable, and return it
        if isinstance(src_dict, Descriptor):
            return dict(src_dict)
        
        self.include_attributes(src_dict)

        if TYPE not in src_dict:
            #the type doesnt exist, so nothing needs to be done. quit early
            return src_dict
        
        cont_field = kwargs.get('p_field')
        p_field    = src_dict.get(TYPE)
        if p_field not in fields.all_fields:
            self._bad = True
            raise TypeError("'TYPE' in descriptors must be a valid Field.")

        #Change the Field to the endianness specified.
        endian_vals = self.get_endian(src_dict, **kwargs)
        p_field = src_dict[TYPE] = endian_vals[0]
        kwargs['end'] = endian_vals[1]

        #remove the endian keyword from the dict since its no longer needed
        if ENDIAN in src_dict:
            del src_dict[ENDIAN]
            
        #Get the name of this block so it can be used in the below routines
        p_name = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        #check for any errors with the layout of the descriptor
        error_str = self.find_errors(src_dict, **kwargs)
        
        kwargs['p_field'] = p_field
        kwargs['p_name']  = p_name

        #if any errors occurred, print them
        if error_str:
            print(error_str)
            self._bad = True
            
        if p_field.is_struct:
            kwargs["substruct"] = True
            
        '''NAME_MAP is used as a map of the names of the variables to
        the index they are stored in. ATTR_OFFS stores the offset of
        each of the attributes. Stores them by both name and index.'''
        if p_field.is_hierarchy:
            src_dict[NAME_MAP] = {}
            self.sanitize_entry_count(src_dict, kwargs["key_name"])
            self.sanitize_element_ordering(src_dict, **kwargs)
            if p_field.is_struct:
                src_dict[ATTR_OFFS] = [0]*src_dict.get('ENTRIES')

        '''if a default was in the dict then we try to decode it
        and replace the default value with the decoded version'''
        if DEFAULT in src_dict and src_dict[TYPE].is_data:
            src_dict[DEFAULT] = self.decode_value(src_dict[DEFAULT], DEFAULT,
                                                  p_name, p_field,
                                                  end=kwargs.get('end'))
            
        #Run the sanitization routine specific to this field
        if p_field.is_bool or p_field.is_enum:
            return self.bool_enum_sanitizer(src_dict, **kwargs)
        elif p_field is Switch:
            return self.switch_sanitizer(src_dict)
        else:
            src_dict = self.standard_sanitizer(src_dict, **kwargs)
            
            if ENTRIES in src_dict:
                 src_dict = self.sequence_sanitizer(src_dict, **kwargs)
            return src_dict
        

    def sanitize_element_ordering(self, src_dict, **kwargs):
        '''sets the number of entries in a descriptor block'''
        
        if ENTRIES in src_dict:
            #because the element count will have already
            #been added, we can use that as our loop count
            last_entry = src_dict[ENTRIES]
            i = gap_size = 0
            offenders = []
            
            while i < last_entry:
                if i not in src_dict:
                    '''if we cant find 'i' in the dict it means we need to
                    shift the elements down by at least 1. as such, we
                    need to look at least 1 higher for the next element'''
                    gap_size += 1
                    last_entry += 1
                else:
                    '''if we DID find the element in the dictionary we need
                    to check if there are any gaps and, if so, shift down'''
                    if gap_size > 0:
                        src_dict[i-gap_size] = src_dict[i]
                        offenders.append(src_dict.pop(i))
                i += 1
                
            if gap_size > 0 and self.sani_warn:
                print("WARNING: Descriptor element ordering needed to be "+
                      "sanitized.\n   Check ordering of '%s'" % self.tag_id )
                
                if GUI_NAME in src_dict:
                    print('\n   GUI_NAME of offending block is "'+
                          str(src_dict[GUI_NAME]))
                elif NAME in src_dict:
                    print('\n   NAME of offending block is "'+
                          str(src_dict[NAME]))
                else:
                    print("\n   Offending block is not named.\n")
                
                print('\n   Offending attributes in the block are:')
                for e in offenders:
                    print('      ' + str(e.get(GUI_NAME,
                                         e.get(NAME, UNNAMED))))
                print()

    def sanitize_entry_count(self, src_dict, key=None):
        '''sets the number of entries in a descriptor block'''
        if key not in (NAME_MAP, ATTR_OFFS, INCLUDE):
            entry_count = 0
            largest = 0
            for i in src_dict:
                if isinstance(i, int):
                    entry_count += 1
                    if i > largest:
                        largest = i
                        
            #we dont want to add an entry count to the NAME_MAP
            #dict or the INCLUDE dict since they aren't parsed
            src_dict[ENTRIES] = entry_count


    def sanitize_gui_name(self, name_str, **kwargs):
        """docstring"""
        #replace all underscores with spaces and
        #remove all leading and trailing spaces
        try:
            gui_name_str = name_str.replace('_', ' ').strip(' ')
            
            #make sure the string doesnt contain
            #any characters that cant be printed
            for char in '\a\b\f\n\r\t\v':
                if char in gui_name_str:
                    print("ERROR: CANNOT USE '%s' AS A GUI_NAME AS "+
                          "IT CONTAINS UNPRINTABLE STRING LITERALS.")
                    self._bad = True
                    return None
            
            if gui_name_str == '':
                print(("ERROR: CANNOT USE '%s' AS A GUI_NAME.\n" % string) +
                       "WHEN SANITIZED IT BECAME AN EMPTY STRING." )
                self._bad = True
                return None
            return gui_name_str
        except Exception:
            return None

    def sanitize_name(self, src_dict, key=None, sanitize=True, **kwargs):
        '''docstring'''
        if key is not None:
            src_dict = src_dict[key]
            
        name = gui_name = None
            
        if NAME in src_dict:
            name     = src_dict[NAME]
            gui_name = src_dict.get(GUI_NAME, name)
        elif GUI_NAME in src_dict:
            gui_name = src_dict[GUI_NAME]
            name     = src_dict.get(NAME, gui_name)
            
        #sanitize the attribute name string to make it a valid identifier
        if sanitize:
            name     = self.sanitize_name_string(name)
            gui_name = self.sanitize_gui_name(gui_name)
            
        if name is None:
            name    = "unnamed"
            p_name  = kwargs.get('p_name')
            p_field = kwargs.get('p_field')
            index   = kwargs.get('key_name')
            field   = src_dict.get(TYPE)
            
            if field is not None:
                print(('ERROR: NAME MISSING IN FIELD OF TYPE "%s" '+
                       'IN INDEX "%s" OF "%s" OF TYPE "%s"') %
                      (field, index, p_name, p_field))
            else:
                print(('ERROR: NAME MISSING IN FIELD LOCATED IN INDEX "%s" '+
                       'OF "%s" OF TYPE %s') % (index, p_name, p_field))
            self._bad = True
            
        if gui_name is None:
            gui_name = name
            
        src_dict[NAME] = name
        #if the definition says to make GUI names OR
        #there is already a GUI name in the dictionary,
        #then set GUI_NAME to the sanitized value
        if self.make_gui_names or src_dict.get(GUI_NAME) is not None:
            src_dict[GUI_NAME] = gui_name
        return name


    def sanitize_name_string(self, string, **kwargs):
        '''Converts any string given to it into a usable identifier.
        Converts all spaces and dashes into underscores, and removes all
        invalid characters. If the last character is invalid, it will be
        dropped instead of being replaced with an underscore'''

        """Docstring snippit about commented out code"""
        #and makes sure the string begins with A-Z, a-z, or an underscore.
        #If the string begins with a number, an underscore will be prepended.
        try:
            sanitized_str = ''
            i = 0
            skipped = False

            #make sure the Sanitized_Strings
            #first character is a valid character
            while len(sanitized_str) == 0 and i < len(string):
                #ignore characters until an alphabetic one is found
                if string[i] in alpha_ids:
                    sanitized_str = string[i]
                    
                i += 1

            #replace all invalid characters with underscores
            for i in range(i, len(string)):
                if string[i] in alpha_numeric_ids:
                    sanitized_str += string[i]
                    skipped = False
                elif not skipped:
                    #no matter how many invalid characters occur in
                    #a row, replace them all with a single underscore
                    sanitized_str += '_'
                    skipped = True

            #make sure the string doesnt end with an underscore
            sanitized_str.rstrip('_')
            
            if sanitized_str in tag_identifiers or sanitized_str == '':
                print("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE NAME.\nWHEN " +
                      "SANITIZED IT BECAME '%s'\n" % (string,sanitized_str))
                self._bad = True
                return None
            return sanitized_str
        except Exception:
            return None
        

    def sanitize_option_values(self, src_dict, field, **kwargs):
        '''docstring'''
        j = field.is_bool
        
        for i in range(src_dict.get('ENTRIES',0)):
            opt = src_dict[i]
            if isinstance(opt, dict):
                if VALUE not in opt:
                    if j: opt[VALUE] = 2**i
                    else: opt[VALUE] = i
                if kwargs.get('p_field'):
                    opt[VALUE] = self.decode_value(opt[VALUE], i,
                                                   kwargs.get('p_name'),
                                                   kwargs.get('p_field'),
                                                   end=kwargs.get('end'))
