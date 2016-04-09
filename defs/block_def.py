'''docstring'''
import sys

from math import log, ceil
from copy import copy
from traceback import format_exc

from supyr_struct.defs.descriptor import Descriptor
from supyr_struct.defs.constants import *
from supyr_struct.defs.common_descriptors import *

class BlockDef():
    '''docstring'''

    #The alignment method to use for aligning structures and
    #their entries to byte boundaries based on each ones size.
    align = ALIGN_NONE
    
    #whether or not to add GUI_NAME entries to each
    #descriptor by converting NAME into a GUI_NAME.
    make_gui_names = False
    
    #whether or not to print sanitization warnings(not errors)
    #to the user when the sanitization routine is run
    sani_warn = True
    
    #Used to signal to the sanitize() function that some
    #kind of error was encountered during sanitization.
    _bad = False

    #As errors are found, the string descriptions of them are
    #appended to this string. If errors are encountered while
    #sanitizing, an exception is raised using this string.
    _e_str = ''

    #whether or not the definition has already been built
    _initialized = False

    #The default endianness to use for every field in the tag
    #This can be overridden by specifying the endianness per field
    endian = ''

    #initialize the class
    def __init__(self, *desc_entries, **kwargs):
        '''docstring'''
        
        if self._initialized:
            return
            
        if not hasattr(self, "descriptor"):
            #used for describing the structure of a tag.
            #this is where everything about the structure is defined.
            self.descriptor = {}
        if not hasattr(self, "subdefs"):
            #used for storing individual or extra pieces of the structure
            self.subdefs = {}
        if not hasattr(self, "def_id"):
            #used for identifying a tag and for telling the tag
            #constructor which tag you are telling it to build.
            #Each def_id must be unique for each Tag_Def
            self.def_id = UNNAMED
        
        if 'descriptor' in kwargs:
            self.descriptor = kwargs["descriptor"]
        if 'subdefs' in kwargs:
            self.subdefs = kwargs['subdefs']
        if 'def_id' in kwargs:
            self.def_id = str(kwargs["def_id"])
        if 'endian' in kwargs:
            self.endian = str(kwargs["endian"])
            
        self.align          = kwargs.get("align", self.align)
        self.sani_warn      = bool(kwargs.get("sani_warn", self.sani_warn))
        self.make_gui_names = bool(kwargs.get("make_gui_names",
                                              self.make_gui_names))
                    
        self._initialized = True

        #make sure the endian value is valid
        assert self.endian in '<>',("Invalid endianness character provided."+
                                    "Valid characters are '<' for little, "+
                                    "'>' for big, and '' for none.")

        if self.descriptor and (desc_entries or TYPE in kwargs):
            raise TypeError(("A descriptor already exists or was provided "+
                             "for the '%s' BlockDef, but individual BlockDef "+
                             "arguments were also supplied.\nCannot accept "+
                             "positional arguments when a descriptor exists.")
                            %self.def_id)

        #determine how to get/make this BlockDefs descriptor
        if desc_entries or TYPE in kwargs:
            self.descriptor = self.make_desc(*desc_entries, **kwargs)
            self.descriptor = Descriptor(self.sanitize(self.descriptor))
        elif isinstance(self.descriptor, BlockDef):
            self.subdefs.update(self.descriptor.subdefs)
            self.descriptor = Descriptor(self.descriptor.descriptor)
        elif self.descriptor and kwargs.get('sanitize', True):
            self.descriptor = Descriptor(self.sanitize(self.descriptor))

        self.make_subdefs()


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
            name, _ = self.sanitize_names(src_dict, i)
            if name in nameset:                            
                self._e_str += (("ERROR: DUPLICATE NAME FOUND IN '%s'.\n" +
                                 "NAME OF OFFENDING ELEMENT IS '%s'\n") %
                                (kwargs["key_name"], name))
                self._bad = True
                continue
            src_dict['NAME_MAP'][name] = i
            if p_field.is_enum:
                src_dict['VALUE_MAP'][src_dict[i]['VALUE']] = i
            nameset.add(name)
        #the dict needs to not be modified by the below code
        return src_dict


    def build(self, **kwargs):
        '''builds and returns a block'''

        desc      = self.descriptor
        field     = desc[TYPE]
        
        rawdata  = blocks.Block.get_raw_data(self, **kwargs)
        new_block = desc.get(DEFAULT, field.py_type)(desc, init_attrs=True)
        
        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("int_test", False)

        if kwargs.get("allow_corrupt"):
            try:
                field.reader(desc, new_block, rawdata, None, **kwargs)
            except Exception:
                pass
        else:
            field.reader(desc, new_block, rawdata, None, **kwargs)
        return new_block
        

    def decode_value(self, value, key, p_name, p_field, **kwargs):
        '''docstring'''
        if self.endian == '':
            endian = p_field.endian
        else:
            endian = kwargs.get('end', self.endian)

        endian = {'>':'big', '<':'little'}.get(p_field.endian, 'little')
        
        if isinstance(value, bytes):
            try:
                if p_field is not None:
                    d_value = p_field.decoder_func(p_field, value)
                elif endian == '<':
                    d_value = int.from_bytes(value, 'little')
                else:
                    d_value = int.from_bytes(value, 'big')
            except Exception:
                self._e_str += (("ERROR: UNABLE TO DECODE THE BYTES "+
                                 "%s IN '%s' OF '%s' AS '%s'.\n\n") %
                                (value, key, p_name, p_field))
                self._bad = True
                return
        elif (isinstance(value, str) and (issubclass(p_field.data_type, int) or
              (issubclass(p_field.py_type, int) and
               issubclass(p_field.data_type, type(None))) )):
            '''if the value is a string and the field's data_type is an
            int, or its py_type is an int and its data_type is type(None),
            then convert the string into bytes and then into an integer.'''
            if endian == 'little':
                value = ''.join(reversed(value))

            d_value = int.from_bytes(bytes(value, encoding='latin1'),
                                     byteorder=endian)
        else:
            d_value = value
            
        return d_value
    

    def find_errors(self, src_dict, **kwargs):
        '''Returns a string textually describing any errors that were found.'''
        #Get the name of this block so it can be used in the below routines
        p_name     = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        p_field    = src_dict.get(TYPE, Void)
        substruct  = kwargs.get('substruct')
        cont_field = kwargs.get('p_field')

        e = "ERROR: %s.\n"
        error_str = ''
        
        if src_dict.get(ENDIAN, '') not in '<>':
            error_str += e%(("ENDIANNESS CHARACTERS MUST BE EITHER '<' FOR "+
                             "LITTLE ENDIAN, '>' FOR BIG ENDIAN, OR '' FOR "+
                             "NONE. NOT  %s" % kwargs.get('end')))
            
        #make sure bit and byte level fields arent mixed improperly
        if isinstance(cont_field, fields.Field):
            if cont_field.is_bit_based and cont_field.is_struct:
                #parent is a bitstruct
                if not p_field.is_bit_based:
                    #but this is NOT bitbased
                    error_str += e%("bit_structs MAY ONLY CONTAIN "+
                                    "bit_based data fields")
                elif p_field.is_struct:
                    error_str += "ERROR: bit_structs CANNOT CONTAIN structs.\n"
            elif p_field.is_bit_based and not p_field.is_struct:
                error_str += e%("bit_based fields MUST RESIDE "+
                                "IN A bit_based Struct")
            
        #if the field is inside a struct, make sure its allowed to be
        if substruct:
            #make sure open ended sized data isnt in a struct
            if p_field.is_oe_size:
                error_str += e%"oe_size fields CANNOT BE USED IN A struct"
            #make sure containers aren't inside structs
            if p_field.is_container:
                error_str += e%("containers CANNOT BE USED IN A struct as "+
                                "structs ARE REQUIRED TO BE A FIXED SIZE "+
                                "WHEREAS containers ARE NOT")

        if p_field.is_var_size and p_field.is_data:
            if substruct and not isinstance(src_dict.get(SIZE), int):
                error_str += e%("var_size data WITHIN A STRUCT MUST HAVE "+
                                "ITS SIZE STATICALLY DEFINED WITH AN INTEGER")
            elif SIZE not in src_dict and not p_field.is_oe_size:
                error_str += e%("var_size data MUST HAVE ITS SIZE GIVEN BY "+
                                "EITHER A FUNCTION, PATH STRING, OR INTEGER")
                
        #make sure arrays have a size if they arent open ended
        if p_field.is_array and not(p_field.is_oe_size or SIZE in src_dict):
            error_str += e%("NON-OPEN ENDED arrays MUST HAVE "+
                            "A SIZE DEFINED IN THEIR DESCRIPTOR")
        if error_str:
            error_str += ("    NAME OF THE OFFENDING ELEMENT IS " +
                          "'%s' OF TYPE '%s'\n" % (p_name, p_field.name))

        return error_str
    

    def get_align(self, src_dict, key):
        this_d = src_dict[key]
        if not isinstance(this_d, dict):
            self._e_str += ("ERROR: EXPECTED %s IN %s OF %s, GOT %s\n"%
                               (dict, key, src_dict.get(NAME), type(this_d)))
            self._bad = True
            return 0
        field  = this_d.get(TYPE, Void)
        align  = 1
        size   = 1

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
            if SUB_STRUCT in src_dict[key]:
                #get and use the alignment of the substruct descriptor
                align = self.get_align(src_dict[key], SUB_STRUCT)
        elif field.is_struct:
            '''search through all entries in the struct
            to find the largest alignment and use it'''
            align = 1
            for i in range(this_d.get(ENTRIES, 1)):
                algn = self.get_align(this_d, i)
                if algn > align: align = algn
                #early return for speedup
                if align >= ALIGN_MAX:
                    return ALIGN_MAX
        
        if ALIGN in this_d:
            #alignment is specified manually
            align = this_d[ALIGN]
        elif self.align == ALIGN_AUTO and size > 0:
            #automatic alignment is to be used
            align = 2**int(ceil(log(size, 2)))
            if align > ALIGN_MAX:
                align = ALIGN_MAX

        return align


    def get_endian(self, src_dict, **kwargs):
        '''Returns the proper endianness of the field type'''
        p_field = src_dict.get(TYPE, Void)
        
        if ENDIAN in src_dict:
            end = src_dict[ENDIAN]
        elif kwargs.get('end') in ('<','>'):
            end = kwargs['end']
        elif self.endian != '':
            end = self.endian
        else:
            return p_field, ''
            
        p_field = {'>':p_field.big, '<':p_field.little}.get(end)
        return p_field, end
    

    def get_size(self, src_dict, key):
        '''docstring'''
        this_d = src_dict[key]
        field  = src_dict[key].get(TYPE, Void)

        #make sure we have names for error reporting
        p_name = src_dict.get(NAME,  src_dict.get(GUI_NAME,  UNNAMED))
        name   = this_d.get(NAME, this_d.get(GUI_NAME, UNNAMED))
            
        if ((field.is_var_size and field.is_data) or
            (SIZE in this_d and isinstance(this_d[SIZE], int)) ):
            if SIZE not in this_d:
                self._e_str += ("ERROR: var_size data MUST HAVE ITS "+
                                "SIZE SPECIFIED IN ITS DESCRIPTOR.\n"+
                                "    OFFENDING ELEMENT IS '%s' IN '%s'\n"%
                                (name, p_name))
                self._bad = True
                return 0
                
            size = this_d[SIZE]
        elif field.is_struct:
            #find the size of the struct as a sum of the sizes of its entries
            size = 0
            for i in range(this_d[ENTRIES]):
                size += self.get_size(this_d, i)
        else:
            size = field.size

        if (field.is_bit_based and not field.is_struct and not
            src_dict.get(TYPE, Void).is_bit_based):
            size = int(ceil(size/8))
            
        return size
    
    
    def include_attributes(self, src_dict):
        include = src_dict.get(INCLUDE)
        if isinstance(include, dict):
            del src_dict[INCLUDE]
            
            for i in include:
                #dont replace it if an attribute already exists there
                if i not in src_dict:
                    src_dict[i] = include[i]
                    
                if i == INCLUDE:
                    #if the include has another include in it, rerun this
                    src_dict = self.include_attributes(src_dict)
        return src_dict
    

    def make_desc(self=None, *desc_entries, **desc):
        '''Converts the supplied positional arguments and keyword arguments
        into a dictionary properly formatted to be used as a descriptor.
        Returns the formatted dictionary.'''
        
        #make sure the descriptor has a type and a name.
        desc.setdefault(TYPE, Container)
        if self:
            subdefs = self.subdefs
            desc.setdefault(NAME, self.def_id)
        else:
            subdefs = {}
        
        #remove all keyword arguments that aren't descriptor keywords
        for key in tuple(desc.keys()):
            if key not in desc_keywords:
                del desc[key]
                continue
            elif isinstance(desc[key], BlockDef):
                '''if the entry in desc is a BlockDef, it
                needs to be replaced with its descriptor.'''
                subdefs[key] = desc[key]
                desc[key]    = desc[key].descriptor
                
        #add all the positional arguments to the descriptor
        for i in range(len(desc_entries)):
            desc[i] = desc_entries[i]
            if isinstance(desc[i], BlockDef):
                '''if the entry in desc is a BlockDef, it
                needs to be replaced with its descriptor.'''
                subdefs[i] = desc[i]
                desc[i]    = desc[i].descriptor
                
        return desc
    

    def make_subdefs(self, replace_subdefs=False):
        '''Converts all the entries in self.subdefs into BlockDefs and
        tries to make BlockDefs for all the entries in the descriptor.'''
        desc       = self.descriptor
        entries    = list(range(desc.get(ENTRIES, 0)))
        if CHILD      in desc: entries.append(CHILD)
        if SUB_STRUCT in desc: entries.append(SUB_STRUCT)
        sub_kwargs = { 'align':self.align, 'endian':self.endian,
                       'make_gui_names':self.make_gui_names,
                       'sani_warn':self.sani_warn }
    
        #make sure all the subdefs are BlockDefs
        for i in self.subdefs:
            d = self.subdefs[i]
            if not isinstance(d, BlockDef):
                self.subdefs[i] = BlockDef(descriptor=d, def_id=i, **sub_kwargs)

        #try and make all the entries in this block into their own BlockDefs
        for i in entries:
            #if the key already exists then dont worry about making one
            if i in self.subdefs and not replace_subdefs:
                continue
            d = desc[i]
            if isinstance(d, dict) and TYPE in d and d[TYPE].is_block:
                name = d[NAME]
                try:
                    self.subdefs[name] = BlockDef(descriptor=d,   def_id=name,
                                                  sanitize=False, **sub_kwargs)
                except Exception:
                    pass


    def sanitize(self, desc):
        '''Use this to sanitize a descriptor.
        Adds key things to the Tag_Def that may be forgotten,
        mistyped, or simply left out and informs the user of
        potential and definite issues through print().'''

        #reset the error status to normal
        self._bad = False
        self._e_str = '\n'
        
        try:
            self.sanitize_names(desc)
            struct_cont = self.sanitize_loop(desc, key_name=None,
                                             end=self.endian)
        except Exception:
            self._initialized = True
            raise Exception(self._e_str + "\n'%s' "%self.def_id + "encountered"+
                            " the above errors during its initialization.")

        #if an error occurred while sanitizing, raise an exception
        if self._bad:
            self._initialized = True
            raise Exception(self._e_str + "\n'%s' "%self.def_id + "encountered"+
                            " the above errors during its initialization.")
        
        return struct_cont
        

    def sanitize_loop(self, src_dict, **kwargs):
        '''docstring'''
        #if the src_dict is a Descriptor, make it
        #mutable and assume it's already sanitized
        if isinstance(src_dict, Descriptor):
            return dict(src_dict)
        
        #combine the entries from INCLUDE into the dictionary
        src_dict = self.include_attributes(src_dict)

        #if the type doesnt exist nothing needs to be done, so quit early
        if TYPE not in src_dict:
            return src_dict
        
        cont_field = kwargs.get('p_field')
        p_field    = src_dict[TYPE]
        if p_field not in fields.all_fields:
            self._bad = True
            raise TypeError("'TYPE' in a descriptor must be a valid Field.")

        #Change the Field to the endianness specified.
        endian_vals = self.get_endian(src_dict, **kwargs)
        p_field = src_dict[TYPE] = endian_vals[0]
        p_name  = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        kwargs['end'] = endian_vals[1]

        #remove the endian keyword from the dict since its no longer needed
        if ENDIAN in src_dict:
            del src_dict[ENDIAN]
            
        #check for any errors with the layout of the descriptor
        error_str = self.find_errors(src_dict, **kwargs)
        
        kwargs['p_field'] = p_field
        kwargs['p_name']  = p_name

        #if any errors occurred, print them
        if error_str:
            self._e_str += error_str+'\n'
            self._bad = True

        #let all the sub-descriptors know they are inside a struct
        if p_field.is_struct:
            kwargs["substruct"] = True

        '''if a default was in the dict then we try to decode it
        and replace the default value with the decoded version'''
        if DEFAULT in src_dict and src_dict[TYPE].is_data:
            src_dict[DEFAULT] = self.decode_value(src_dict[DEFAULT], DEFAULT,
                                         p_name, p_field, end=kwargs.get('end'))
            
        #run the sanitization routine specific to this field
        if p_field.is_bool or p_field.is_enum:
            return self.bool_enum_sanitizer(src_dict, **kwargs)
        elif p_field is Switch:
            return self.switch_sanitizer(src_dict)
        elif p_field.is_block:
            return self.sequence_sanitizer(src_dict, **kwargs)
        else:
            return self.standard_sanitizer(src_dict, **kwargs)
        

    def sanitize_element_ordering(self, src_dict, **kwargs):
        '''Sets the number of entries in a descriptor block'''
        
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
                self._e_str += ("WARNING: Descriptor element ordering needed "+
                                "to be sanitized.\n   Check ordering of "+
                                "'%s'\n" % self.def_id )
                
                if GUI_NAME in src_dict:
                    self._e_str += ("\n   GUI_NAME of offending block is "+
                                    "'%s'\n\n" % str(src_dict[GUI_NAME]))
                elif NAME in src_dict:
                    self._e_str += ("\n   NAME of offending block is "+
                                    "'%s'\n\n"% str(src_dict[NAME]))
                else:
                    self._e_str += ("\n   Offending block is not named.\n\n")
                self._e_str += '\n   Offending attributes in the block are:\n'
                for e in offenders:
                    self._e_str += ('      ' + str(e.get(GUI_NAME,
                                    e.get(NAME, UNNAMED))) + '\n')
                self._e_str += '\n'


    def sanitize_names(self, src_dict, key=None, sanitize=True, **kwargs):
        '''Sanitizes the NAME value in src_dict into a usable identifier
        and replaces the old entry with the sanitized value.
        If a NAME value doesnt exist, the GUI_NAME value will be converted.
        If there is also a GUI_NAME value or self.make_gui_names == True
        then the GUI_NAME will be converted into something printable.
        If a GUI_NAME value doesnt exist, it will convert the NAME entry.'''
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
            name     = self.str_to_name(name)
            gui_name = self.str_to_gui_name(gui_name)
            
        if name is None:
            name    = "unnamed"
            p_name  = kwargs.get('p_name')
            p_field = kwargs.get('p_field')
            index   = kwargs.get('key_name')
            field   = src_dict.get(TYPE)
            
            if field is not None:
                self._e_str += (("ERROR: NAME MISSING IN FIELD OF TYPE '%s'\n"+
                                 "    IN INDEX '%s' OF '%s' OF TYPE '%s'\n") %
                                (field, index, p_name, p_field))
            else:
                self._e_str += (("ERROR: NAME MISSING IN FIELD LOCATED "+
                                 "IN INDEX '%s' OF '%s' OF TYPE '%s'\n") %
                                (index, p_name, p_field))
            self._bad = True
            
        if gui_name is None:
            gui_name = name
            
        #if the definition says to make gui names OR there is already
        #a gui name in the dictionary, then set the GUI_NAME value
        if self.make_gui_names or src_dict.get(GUI_NAME) is not None:
            src_dict[GUI_NAME] = gui_name
        src_dict[NAME] = name
        return name, gui_name
    
        
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


    def sanitize_option_values(self, src_dict, field, **kwargs):
        '''docstring'''
        j = field.is_bool
        p_name  = kwargs.get('p_name', UNNAMED)
        p_field = kwargs.get('p_field', None)
        
        for i in range(src_dict.get('ENTRIES', 0)):
            opt = src_dict[i]
            
            if isinstance(opt, dict):
                #make a copy to make sure the original is intact
                opt = dict(opt)
            elif isinstance(opt, (list, tuple, str)):
                if isinstance(opt, str):
                    opt = {NAME:opt}
                elif len(opt) == 1:
                    opt = {NAME:opt[0]}
                elif len(opt) == 2:
                    opt = {NAME:opt[0], VALUE:opt[1]}
                elif len(opt) == 3:
                    opt = {NAME:opt[0], VALUE:opt[1], GUI_NAME:opt[2]}
                else:
                    self._e_str += (("ERROR: EXCEPTED 1 TO 3 ARGUMENTS FOR "+
                                     "OPTION NUMBER %s\nIN FIELD %s OF NAME "+
                                     "'%s', GOT %s ARGUMENTS.\n" ) %
                                    (i, p_field, p_name, len(opt)))
                    self._bad = True
                    continue
            else:
                continue
                
            if VALUE not in opt:
                if j: opt[VALUE] = 2**i
                else: opt[VALUE] = i
            if p_field:
                opt[VALUE] = self.decode_value(opt[VALUE], i, p_name,
                                               p_field, end=kwargs.get('end'))
            src_dict[i] = opt


    def sequence_sanitizer(self, src_dict, **kwargs):
        """Loops through each of the numbered entries in the descriptor.
        This is done separate from the non-integer dict entries because
        a check to sanitize offsets needs to be done from 0 up to ENTRIES.
        Looping over a dictionary by its keys will do them in a non-ordered
        way and the offset sanitization requires them to be done in order."""

        #do the standard sanitization routine on the non-numbered entries
        src_dict = self.standard_sanitizer(src_dict, **kwargs)
        
        #if a variable doesnt have a specified offset then
        #this will be used as the starting offset and will
        #be incremented by the size of each variable after it
        def_offset = 0
        #the largest alignment size requirement of any entry in this block
        l_align = 1
        
        p_field = src_dict[TYPE]
        p_name  = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))

        #ATTR_OFFS stores the offsets of each attribute by index.
        attr_offs = [0]*src_dict.get('ENTRIES',0)
        nameset   = set() #contains the name of each entriy in the desc
        removed   = 0 #number of dict entries removed
        key       = 0

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

        pad_count = 0
        
        '''loops through the entire descriptor and
        finalizes each of the integer keyed attributes'''
        for key in range(src_dict[ENTRIES]):
            this_d = src_dict[key]
            
            if isinstance(this_d, dict):
                #Make sure to shift upper indexes down by how many
                #were removed and make a copy to preserve the original
                this_d = src_dict[key-removed] = dict(this_d)
                key -= removed
                
                field = this_d.get(TYPE)
                
                if field is Pad:
                    '''the dict was found to be padding, so increment
                    the default offset by it, remove the entry from the
                    dict, and adjust the removed and entry counts.'''
                    size = this_d.get(SIZE)
                    
                    if size is not None:
                        def_offset += size
                    else:
                        self._bad = True
                        self._e_str += (("ERROR: Pad ENTRY IN '%s' OF TYPE '%s'"
                                       +" AT INDEX %s IS MISSING A SIZE KEY.\n")
                                        % (p_name,src_dict[TYPE],key+removed) )
                    if p_field.is_struct:
                        if ATTR_OFFS in src_dict:
                            self._e_str += (("ERROR: ATTR_OFFS ALREADY EXISTS "+
                                             "IN '%s' OF TYPE '%s', BUT A Pad "+
                                             "ENTRY WAS FOUND AT INDEX %s.\n"+
                                             "    CANNOT INCLUDE Pad Fields "+
                                             "WHEN ATTR_OFFS ALREADY EXISTS.\n")
                                           %(p_name,src_dict[TYPE],key+removed))
                            self._bad = True
                        removed += 1
                        src_dict[ENTRIES] -= 1
                    else:
                        #if the padding isnt being removed, make
                        #sure it follows convention and has a name
                        this_d.setdefault(NAME, 'pad_entry_%s'%pad_count)
                        if NAME_MAP in src_dict:
                            src_dict[NAME_MAP][this_d[NAME]] = key
                        if self.make_gui_names:
                            this_d.setdefault(GUI_NAME,'pad entry %s'%pad_count)
                        pad_count += 1
                    continue
                elif field is not None:
                    '''make sure the block has an offset if it needs one'''
                    if p_field.is_struct and OFFSET not in this_d:
                        this_d[OFFSET] = def_offset
                elif p_field:
                    self._bad = True
                    self._e_str += (("ERROR: DESCRIPTOR FOUND THAT IS "+
                                     "MISSING ITS TYPE IN '%s' OF TYPE"+
                                     " '%s' AT INDEX %s.\n")
                                     % (p_name, src_dict[TYPE], key+removed) )
                        
                kwargs["key_name"] = key
                this_d = src_dict[key] = self.sanitize_loop(this_d, **kwargs)

                if field:
                    sani_name, _ = self.sanitize_names(src_dict, key, **kwargs)
                    if NAME_MAP in src_dict:
                        src_dict[NAME_MAP][sani_name] = key
                        
                        name = this_d[NAME]
                        if name in nameset:
                            self._e_str += (("ERROR: DUPLICATE NAME FOUND "+
                                             "IN '%s' AT INDEX %s.\n    NAME "+
                                             "OF OFFENDING ELEMENT IS '%s'\n")
                                            % (p_name, key+removed, name))
                            self._bad = True
                        nameset.add(name)

                    #get the size of the entry(if the parent dict requires)
                    if p_field.is_struct and OFFSET in this_d:
                        '''add the offset to ATTR_OFFS in the parent dict'''
                        offset = this_d[OFFSET]
                        size   = self.get_size(src_dict, key)
                        
                        #make sure not to align within bit structs
                        if not(field.is_bit_based and p_field.is_bit_based):
                            align = self.get_align(src_dict, key)
                        
                            if align > ALIGN_MAX:
                                align = l_align = ALIGN_MAX
                            elif align > l_align:
                                l_align = align
                                
                            if align > 1:
                                offset += (align-(offset%align))%align
                                
                        def_offset = offset + size

                        #set the offset and delete the OFFSET entry
                        attr_offs[key] = offset
                        del this_d[OFFSET]

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

        #prune potentially extra entries from the attr_offs list
        attr_offs = attr_offs[:key+1]

        #if the field is a struct and the ATTR_OFFS isnt already in it
        if p_field.is_struct and ATTR_OFFS not in src_dict:
            src_dict[ATTR_OFFS] = attr_offs
                        
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
        
        #NAME_MAP maps the name of each attribute to the index it's stored in
        if p_field.is_block:
            src_dict[NAME_MAP] = {}
            self.sanitize_entry_count(src_dict, kwargs["key_name"])
            self.sanitize_element_ordering(src_dict, **kwargs)
        
        #The non integer entries aren't substructs, so set it to False.
        kwargs['substruct'] = False
        
        #loops through the descriptors non-integer keyed sub-sections
        for key in src_dict:
            if not isinstance(key, int):
                if key not in desc_keywords and self.sani_warn:
                    self._e_str += (("WARNING: FOUND ENTRY IN DESCRIPTOR OF "+
                                     "'%s' UNDER UNKNOWN KEY '%s' OF TYPE %s.\n")
                                    %(p_name, key, type(key)))
                if isinstance(src_dict[key], dict):
                    kwargs["key_name"] = key
                    field = src_dict[key].get(TYPE)
                    this_d = dict(src_dict[key])
                    
                    #replace with the modified copy so the original is intact
                    src_dict[key] = this_d = self.sanitize_loop(this_d,**kwargs)

                    if field:
                        #if this is the repeated substruct of an array
                        #then we need to calculate and set its alignment
                        if ((key == SUB_STRUCT or field.is_str) and
                            ALIGN not in this_d):
                            align = self.get_align(src_dict, key)
                            #if the alignment is 1 then adjustments arent needed
                            if align > 1:
                                this_d[ALIGN]
                            
                        sani_name,_ = self.sanitize_names(src_dict,key,**kwargs)
                        if key != SUB_STRUCT:
                            src_dict[NAME_MAP][sani_name] = key
        return src_dict


    def str_to_gui_name(self, name_str, **kwargs):
        """docstring"""
        #replace all underscores with spaces and
        #remove all leading and trailing spaces
        try:

            if not isinstance(name_str, str):
                self._e_str += (("ERROR: INVALID TYPE FOR GUI_NAME. EXPECTED "+
                                 "%s, GOT %s.\n") % (str, type(name_str)))
                self._bad = True
                return None
            
            gui_name_str = name_str.replace('_', ' ').strip(' ')
            
            #make sure the string doesnt contain
            #any characters that cant be printed
            for char in '\a\b\f\n\r\t\v':
                if char in gui_name_str:
                    try:
                        self._e_str += (("ERROR: CANNOT USE '%s' AS A "+
                                         "GUI_NAME AS IT CONTAINS UNPRINTABLE "+
                                         "STRING LITERALS.\n") % name_str)
                    except Exception:
                        self._e_str += ("ERROR: CANNOT USE A CERTAIN NAME "+
                                        "AS A GUI_NAME AS IT CONTAINS "+
                                        "UNPRINTABLE STRING LITERALS.\n")
                    self._bad = True
                    return None
            
            if gui_name_str == '':
                self._e_str += (("ERROR: CANNOT USE '%s' AS A GUI_NAME.\n" +
                                 "WHEN SANITIZED IT BECAME ''.\n")%string )
                self._bad = True
                return None
            return gui_name_str
        except Exception:
            return None


    def str_to_name(self, string, **kwargs):
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

            if not isinstance(string, str):
                self._e_str += (("ERROR: INVALID TYPE FOR NAME. EXPECTED "+
                                 "%s, GOT %s.\n") % (str, type(string)))
                self._bad = True
                return None

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
            
            if sanitized_str in desc_keywords or sanitized_str == '':
                self._e_str += (("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE "+
                                 "NAME.\nWHEN SANITIZED IT BECAME '%s'\n\n")%
                                 (string, sanitized_str))
                self._bad = True
                return None
            return sanitized_str
        except Exception:
            return None
        

    def switch_sanitizer(self, src_dict, **kwargs):
        '''if the descriptor is a switch, the individual cases need to
        be checked and setup as well as the pointer and defaults.'''
        p_field  = src_dict[TYPE]
        p_name   = src_dict.get(NAME, src_dict.get(GUI_NAME, UNNAMED))
        pointer  = src_dict.get(POINTER)
        case_map = src_dict.get(CASE_MAP, {})
        cases    = src_dict.get(CASES,())
        c_index  = 0

        if src_dict.get(CASE) is None:
            self._e_str += ("ERROR: CASE MISSING IN '%s' OF TYPE '%s'\n"
                            %(p_name, p_field))
            self._bad = True
        if cases is None and CASE_MAP not in src_dict:
            self._e_str += ("ERROR: CASES MISSING IN '%s' OF TYPE '%s'\n"
                            %(p_name, p_field))
            self._bad = True
            

        for case in cases:
            case_map[case] = c_index
            if isinstance(cases[case], BlockDef):
                '''if the entry in desc is a BlockDef, it
                needs to be replaced with its descriptor.'''
                self.subdefs[c_index] = cases[case]
                case_desc = dict(cases[case].descriptor)
            else:
                #copy the case's descriptor so it can be modified
                case_desc = dict(cases[case])
            
            c_field = case_desc.get(TYPE, Void)
            if not issubclass(c_field.py_type, blocks.Block):
                self._e_str += ("ERROR: CANNOT USE CASES IN A Switch WHOSE "+
                                "Field.py_type IS NOT A Block.\n OFFENDING "+
                                "ELEMENT IS '%s' IN '%s' OF '%s' OF TYPE %s.\n"%
                                (case, CASES, p_name, c_field))
                self._bad = True
                
            kwargs['key_name'] = case
            #copy the pointer from the switch into each case
            if pointer is not None:
                case_desc[POINTER] = pointer
                
            src_dict[c_index] = self.sanitize_loop(case_desc, **kwargs)

            c_index += 1
            
        if CASES in src_dict:
            del src_dict[CASES]
        src_dict[CASE_MAP] = case_map

        #make sure there is a default case
        src_dict[DEFAULT] = src_dict.get(DEFAULT, void_desc)
        kwargs['key_name'] = DEFAULT
        
        if pointer is not None:
            src_dict[DEFAULT][POINTER] = pointer
        src_dict[DEFAULT] = self.sanitize_loop(src_dict[DEFAULT], **kwargs)
        
        #the dict needs to not be modified by the below code
        return src_dict
