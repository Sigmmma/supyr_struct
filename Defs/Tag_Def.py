'''docstring'''
import sys

from math import log, ceil
from copy import copy

from .Constants import *
from supyr_struct.Field_Types import *

class Tag_Def():
    '''docstring'''

    #primarily used for locating tags when indexing a collection of
    #them, but also used as the extension when writing a tag to a file
    Ext = ".tag"

    #used for identifying a tag and for telling the tag
    #constructor which tag you are telling it to build.
    #Each Cls_ID must be unique for each Tag_Def
    Cls_ID = ""

    #The module to use to build this definitions Tag_Obj from
    Tag_Obj = None

    #used for describing the structure of a tag.
    #this is where everything about the structure is defined.
    Tag_Structure = {}

    #used for storing individual or supplementary pieces of the structure
    Structures = {}

    #specifies that the object is only partially defined and any edits to it
    #must be done to a copy of the original file in order to keep all of the
    #undefined data intact. Structures SHOULD NEVER be added or deleted from
    #an incomplete object, though you are not prevented from doing so.
    Incomplete = False

    #The automatic alignment method to use for aligning structures and
    #their entries to boundaries based on each ones size in bytes.
    '''NOT IMPLEMENTED YET'''
    Align_Mode = ALIGN_NONE

    #the default endianness to use for every field in the tag
    #This can be overridden by explicitely specifying an endianness per field
    Endianness = { 'big':'>', 'little':'<' }.get(sys.byteorder.lower(), '<')

    #used to signal to the Sanitize() function that some
    #kind of error was encountered during sanitization.
    _Bad = False

    #initialize the class
    def __init__(self, **kwargs):
        '''docstring'''

        self.Cls_ID = kwargs.get("Cls_ID", self.Cls_ID)
        self.Ext = kwargs.get("Ext", self.Ext)
        self.Tag_Structure = kwargs.get("Structure", self.Tag_Structure)

        if hasattr(self, 'Structures') and isinstance(self.Structures, dict):
            for key in self.Structures:
                self.Structures[key] = self.Sanitize(self.Structures[key])
                
        if hasattr(self, "Tag_Structure") and self.Tag_Structure:
            self.Tag_Structure = self.Sanitize(self.Tag_Structure)


    def Sanitize(self, Structure):
        '''this function is used to add key things to the Tag_Def
        that end up being forgotten, mistyped, or simply left out'''

        #reset the error status to normal
        self._Bad = False
        
        #enclosing the Tag_Structure in a dictionary is necessary for
        #it to properly set up the topmost level of the Tag_Structure
        Struct_Cont = self._Sanitize({TYPE:Container, ATTR_MAP:{},
                                      0:Structure}, Key_Name=None,
                                     Endianness=self.Endianness)

        #if an error occurred while sanitizing, raise an exception
        if self._Bad:
            raise Exception(("The '%s' Tag_Def encountered errors "+
                             "during its construction.") % self.Cls_ID)
        
        return Struct_Cont[0]


    def _Sanitize(self, Dictionary, **kwargs):
        '''docstring'''
        self._Include_Attributes(Dictionary)
        self._Set_Entry_Count(Dictionary, kwargs["Key_Name"])
        self._Sanitize_Element_Ordering(Dictionary, **kwargs)

        if kwargs.get('Key_Name') is not None:
            Name_Set = set()
            
            if kwargs["Key_Name"] in (FLAGS, ELEMENTS):
                if kwargs["Key_Name"] == ELEMENTS:
                    '''if the dict is an enumerator element list then we
                    need to make sure there is a value for each element'''
                    self._Sanitize_Element_Values(Dictionary, **kwargs)
                elif kwargs["Key_Name"] == FLAGS:
                    '''if the dict is an boolean flags list then we
                    need to make sure there is a value for each flag'''
                    self._Sanitize_Flag_Values(Dictionary, **kwargs)
                    
                for i in range(Dictionary[ENTRIES]):
                    Name = self._Sanitize_Name(Dictionary, i)
                    if Name in Name_Set:                            
                        print(("ERROR: DUPLICATE NAME FOUND IN %s.\n"
                              + "NAME OF OFFENDING ELEMENT IS %s") %
                              (kwargs["Key_Name"], Name))
                        self._Bad = True
                    Name_Set.add(Name)
            
        self._Sanitize_Loop(Dictionary, **kwargs)
        
        return Dictionary



    def _Sanitize_Loop(self, Dictionary, **kwargs):
        '''docstring'''
        
        if TYPE in Dictionary:
            #Get the name of this block so it
            #can be used in the below routines
            try:
                Parent_Name = Dictionary[NAME]
            except Exception:
                Parent_Name = Dictionary.get(GUI_NAME, "unnamed")
                
            if ENDIAN in Dictionary:
                kwargs['Endianness'] = Dictionary[ENDIAN]
                
            Parent_Type = Dictionary[TYPE]
            if kwargs['Endianness'] == '>':
                Parent_Type = Dictionary[TYPE] = Parent_Type.Big
            elif kwargs['Endianness'] == '<':
                Parent_Type = Dictionary[TYPE] = Parent_Type.Little
            else:
                raise ValueError("Endianness characters must be either '<' "+
                                 "for little endian or '>' for big endian.")
            kwargs['Parent_Type'] = Parent_Type
            kwargs['Parent_Name'] = Parent_Name
            Error_Str = ''
            
            #ATTR_MAP is used as a map of the names of
            #the variables to the index they are stored in.
            #ATTR_OFFSETS stores the offset of each of the
            #attributes. Stores them by both Name and Index
            if Parent_Type.Is_Hierarchy:
                Dictionary[ATTR_MAP] = {}
                
            if Parent_Type.Is_Array:
                kwargs["Sub_Array"] = True
                
            if Parent_Type.Is_Struct:
                kwargs["Sub_Struct"] = True
                Dictionary[ATTR_OFFSETS] = {}
            else:
                '''Check to make sure this data type is valid to be
                inside a structure if it currently is inside one.'''
                if kwargs.get('Sub_Struct'):
                    if Parent_Type.Is_Container:
                        Error_Str += ("ERROR: Containers CANNOT BE USED IN A "+
                                      "Struct.\nStructs ARE REQUIRED TO BE "+
                                      "A FIXED SIZE AND Containers ARE NOT.\n")
                
                    elif (Parent_Type.Is_Var_Size and
                          not isinstance(Dictionary.get(SIZE), (int, bytes))):
                        Error_Str += ("ERROR: TO USE Var_Size DATA IN A "+
                                      "Struct THE SIZE MUST BE STATICALLY "+
                                      "DEFINED WITH AN INTEGER.\n")

            #series of checks to make sure bit and
            #byte level objects arent mixed improperly
            if (Parent_Type.Is_Bit_Based and
                Parent_Type.Is_Struct == kwargs.get("Sub_Bit_Struct") ):
                
                if Parent_Type.Is_Struct:
                    Error_Str += ("ERROR: Bit_Structs MAY ONLY CONTAIN "+
                                  "Bit_Based 'Data' Field_Types.\n")
                else:
                    Error_Str += ("ERROR: Bit_Based Field_Types MUST RESIDE "+
                                  "IN A Bit_Based Struct.\n")
            elif kwargs.get("Sub_Bit_Struct") and not Parent_Type.Is_Bit_Based:
                Error_Str += ("ERROR: Bit_Structs MAY ONLY CONTAIN "+
                              "Bit_Based 'Data' Field_Types.\n")

            #if any errors occurred, print them
            if Error_Str:
                print((Error_Str + "    NAME OF OFFENDING ELEMENT IS '%s' " +
                      "OF TYPE '%s'") %(Parent_Name, Parent_Type.Name) + "\n")
                self._Bad = True
                Error_Str = ''
                
            kwargs["Sub_Bit_Struct"] = Parent_Type.Is_Bit_Based

            #if bytes were provided as the default value we decode them
            #and replace the default value with the decoded version
            if DEFAULT in Dictionary:
                Def = Dictionary[DEFAULT]
                if Dictionary[TYPE].Is_Data:
                    Dictionary[DEFAULT] = self._Decode_Value(Def, DEFAULT,
                                                     Parent_Name, Parent_Type)
                elif (not isinstance(Def, type) or
                      not issubclass(Def, Tag_Block)):
                    print("ERROR: DEFAULT VALUES FOR Hierarchy Field_Types "+
                          "MUST BE SUBCLASSES OF 'Tag_Block'.\n"+
                          "    EXPECTED '%s', BUT GOT '%s'\n" % (type, Def))
                    self._Bad = True

        #if a variable doesnt have a specified offset then
        #this will be used as the starting offset and will
        #be incremented by the size of each variable after it
        Default_Offset = 0
        #the largest alignment size requirement of any entry in this block
        Largest_Align = 0

        '''The non integer entries aren't part of substructs, so
        save the substruct status to a temp var and set it to false'''
        temp1, kwargs['Sub_Struct']     = kwargs.get('Sub_Struct'), False
        temp2, kwargs['Sub_Bit_Struct'] = kwargs.get('Sub_Bit_Struct'), False
        temp3, kwargs['Sub_Array']      = kwargs.get('Sub_Array'), False
        
        #loops through the descriptors non-integer keyed sub-sections
        for key in Dictionary:
            Dictionary[key] = copy(Dictionary[key])
            if not isinstance(key, int) and isinstance(Dictionary[key], dict):
                Type = None
                if TYPE in Dictionary[key]:
                    Type = Dictionary[key][TYPE]
                    
                kwargs["Key_Name"] = key
                self._Sanitize(Dictionary[key], **kwargs)

                if Type:
                    Sanitized_Name = self._Sanitize_Name(Dictionary, key,
                                                         **kwargs)
                    if key not in (SUB_STRUCT):
                        Dictionary[ATTR_MAP][Sanitized_Name] = key
                        
        #restore the Sub_Struct status
        kwargs['Sub_Struct'] = temp1
        kwargs['Sub_Bit_Struct'] = temp2
        kwargs['Sub_Array'] = temp3

        """Loops through each of the numbered entries in the descriptor.
        This is done separate from the non-integer dict entries because
        a check to sanitize offsets needs to be done from 0 up to ENTRIES.
        Looping over a dictionary by its keys will do them in a non-ordered
        way and the offset sanitization requires them to be done in order."""
        if ENTRIES in Dictionary:
            Name_Set = set()
            Removed = 0 #number of dict entries removed
            
            '''loops through the entire descriptor
            and finalizes each of the attributes'''
            for key in range(Dictionary[ENTRIES]):
                Dictionary[key-Removed] = This_Dict = copy(Dictionary[key])
                key -= Removed
                
                if isinstance(This_Dict, dict):
                    Type = None
                    if TYPE in This_Dict:
                        Type = This_Dict[TYPE]

                        '''make sure the block has an offset if it needs one'''
                        if Parent_Type.Is_Struct and OFFSET not in This_Dict:
                            This_Dict[OFFSET] = Default_Offset
                    elif TYPE in Dictionary:
                        #if this int keyed dict has no TYPE, but is inside a
                        #dict with a TYPE, then something is probably wrong
                        #OR this dict contains a PAD key:value pair
                        if PAD in This_Dict:
                            '''the dict was found to be padding, so increment
                            the default offset by it, remove the entry from the
                            dict, and adjust the removed and entry counts.'''
                            Default_Offset += This_Dict[PAD]
                                
                            Removed += 1
                            Dictionary[ENTRIES] -= 1
                            del Dictionary[key]
                            continue
                        else:
                            #Pad entry doesnt exist. This is an error.
                            try:
                                Name = Dictionary[GUI_NAME]
                            except Exception:
                                Name = Dictionary.get(NAME, 'unnamed')
                                
                            if len(This_Dict):
                                raise LookupError(('Non-empty dictionary found'+
                                    ' in "%s" descriptor of type "%s" at index'+
                                    ' "%s".') % (Name, Dictionary[TYPE], key) )
                            else:
                                raise LookupError('Empty dictionary found in '+
                                   '"%s" descriptor of type "%s" at index "%s".'
                                    % (Name, Dictionary[TYPE], key) )
                            
                    kwargs["Key_Name"] = key
                    self._Sanitize(This_Dict, **kwargs)

                    if Type:                            
                        Sanitized_Name = self._Sanitize_Name(Dictionary,
                                                             key, **kwargs)
                        Dictionary[ATTR_MAP][Sanitized_Name] = key
                        
                        Name = This_Dict[NAME]
                        if Name in Name_Set:
                            print(("ERROR: DUPLICATE NAME FOUND IN '%s'.\n"
                                  +"    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                                  (Parent_Name, Name))
                            self._Bad = True
                        Name_Set.add(Name)

                        #get the size of the entry(if the parent dict requires)
                        if ATTR_OFFSETS in Dictionary:
                            Size = self._Get_Size(Dictionary, key)
                            
                        '''add the offset to ATTR_OFFSETS in the parent dict'''
                        if ATTR_OFFSETS in Dictionary and OFFSET in This_Dict:
                            #if bytes were provided as the offset we decode
                            #them and replace it with the decoded version
                            Offset = self._Decode_Value(This_Dict[OFFSET],
                                                        OFFSET, Name)
                            
                            #ALIGN BITSTRUCTS BY THEIR SIZE
                            #ALIGN STRINGS BY THEIR CHARACTER SIZE
                            #ALIGN TO THE LARGEST SIZED DATA IN A STRUCTURE.
                            #THIS INCLUDES CHECKING ALL ITS SUBSTRUCTURES

                            #RECORD THE LARGEST ALIGNMENT SIZE OF EACH OF
                            #A STRUCTS ELEMENTS AND USE THAT FOR CALCULATING
                            #FINAL PADDING ON THEIR PARENT STRUCTURE.
                            #FOR ARRAYS, INSTEAD SET THEIR "ALIGN" TO THIS

                            '''
                            #make sure not to align within bit structs
                            if not (Type.Is_Bit_Based and
                                    Parent_Type.Is_Bit_Based):
                                if ALIGN in This_Dict:
                                    #alignment is specified manually
                                    Align = This_Dict[ALIGN]
                            
                                elif self.Align_Mode == ALIGN_AUTO and Size > 0:
                                    #automatic alignment is to be used
                                    Align = 2**int(ceil(log(Size, 2)))
                                    if Align > ALIGN_MAX:
                                        Align = ALIGN_MAX
                            
                                if Align > Largest_Align:
                                    Largest_Align = Align
                                if Align > 0:
                                    Offset += (Align-(Offset%Align))%Align
                            '''

                            Default_Offset = Offset + Size
                        
                            Dictionary[ATTR_OFFSETS][This_Dict[NAME]] = Offset
                            del This_Dict[OFFSET]

        #Make sure all structs have a defined SIZE
        if ((TYPE in Dictionary and Dictionary[TYPE].Is_Struct)
            and SIZE not in Dictionary):
            if Dictionary[TYPE].Is_Bit_Based:
                Default_Offset = int(ceil(Default_Offset/8))
            Dictionary[SIZE] = Default_Offset


    def _Get_Size(self, Dictionary, key):
        '''docstring'''
        This_Dict = Dictionary[key]
        Type = This_Dict[TYPE]

        #make sure we have names for error reporting
        try:
            Parent_Name = Dictionary[GUI_NAME]
        except Exception:
            Parent_Name = Dictionary.get(NAME, 'unnamed')
            
        try:
            Name = This_Dict[GUI_NAME]
        except Exception:
            Name = This_Dict.get(NAME, 'unnamed')
            
        if ((Type.Is_Var_Size and Type.Is_Data) or
            (SIZE in This_Dict and  isinstance(This_Dict[SIZE], (int,bytes)))):
            if SIZE not in This_Dict:
                print("ERROR: Var_Size DATA MUST HAVE ITS SIZE SPECIFIED IN "+
                      "ITS DESCRIPTOR.\n    OFFENDING ELEMENT FOUND IN "+
                      "'%s' AND NAMED '%s'.\n" % (Parent_Name, Name))
                self._Bad = True
                return 0
                
            Size = This_Dict[SIZE] = self._Decode_Value(This_Dict[SIZE],
                                                        SIZE, Name)
        elif Type.Is_Struct:
            self._Include_Attributes(This_Dict)
            self._Set_Entry_Count(This_Dict)
            self._Sanitize_Element_Ordering(This_Dict)
            Size = 0
            try:
                for i in range(This_Dict[ENTRIES]):
                    Size += self._Get_Size(This_Dict, i)
            except Exception: pass
        else:
            Size = Type.Size

        if (Type.Is_Bit_Based and not Type.Is_Struct and not
            Dictionary[TYPE].Is_Bit_Based):
            Size = int(ceil(Size/8))
            
        return Size


    def _Include_Attributes(self, Dictionary):
        '''docstring'''
        #combine the entries from ATTRIBUTES into the dictionary
        if isinstance(Dictionary.get(ATTRIBUTES), dict):
            self._Set_Entry_Count(Dictionary[ATTRIBUTES], ATTRIBUTES)
            for i in Dictionary[ATTRIBUTES]:
                #dont replace it if an attribute already exists there
                if i not in Dictionary:
                    Dictionary[i] = Dictionary[ATTRIBUTES][i]
            del Dictionary[ATTRIBUTES]

    def _Set_Entry_Count(self, Dictionary, Key_Name=None):
        '''sets the number of entries in a descriptor block'''
        Entry_Count = 0
        Largest = 0
        for key in Dictionary:
            if isinstance(key, int):
                Entry_Count += 1
                if key > Largest:
                    Largest = key

        if Key_Name in (ELEMENTS, FLAGS):
            for i in range(Largest):
                if i not in Dictionary:
                    Dictionary[i] = {GUI_NAME:'UNUSED_'+str(i), VALUE:i}
                    Entry_Count += 1
                    
        #we dont want to add an entry count to the ATTR_MAP
        #dict or the ATTRIBUTES dict since they aren't parsed
        if Key_Name not in (ATTR_MAP, ATTR_OFFSETS, ATTRIBUTES):
            Dictionary[ENTRIES] = Entry_Count


    def _Decode_Value(self, Value, Key_Name=None,
                      Parent_Name=None, Parent_Type=None):
        '''docstring'''
        if isinstance(Value, bytes):
            try:
                if Parent_Type is not None:
                    Value = Parent_Type.Decoder(Value)
                elif self.Endianness == '>':
                    Value = int.from_bytes(Value, 'big')
                elif self.Endianness == '<':
                    Value = int.from_bytes(Value, 'little')
                else:
                    Value = int.from_bytes(Value, sys.byteorder)
            except Exception:
                print(("ERROR: UNABLE TO DECODE THE BYTES %s IN '%s' "+
                       "OF '%s' AS '%s'.\n")
                      %(Value, Key_Name, Parent_Name, Parent_Type))
                self._Bad = True
        return Value

    def _Sanitize_Element_Values(self, Dictionary, **kwargs):
        '''docstring'''
        for i in range(Dictionary[ENTRIES]):
            Elem = Dictionary[i]
            if isinstance(Elem, dict):
                if VALUE not in Elem:
                    Elem[VALUE] = i
                if kwargs.get('Parent_Type'):
                    Elem[VALUE] = self._Decode_Value(Elem[VALUE], i, ELEMENTS,
                                                     kwargs.get('Parent_Type'))

    def _Sanitize_Flag_Values(self, Dictionary, **kwargs):
        '''docstring'''
        for i in range(Dictionary[ENTRIES]):
            Flag = Dictionary[i]
            if isinstance(Flag, dict):
                if VALUE not in Flag:
                    Flag[VALUE] = 2**i
                if kwargs.get('Parent_Type'):
                    Flag[VALUE] = self._Decode_Value(Flag[VALUE], i, FLAGS,
                                                     kwargs.get('Parent_Type'))

    def _Sanitize_Name(self, Dictionary, key=None, Sanitize=True, **kwargs):
        '''docstring'''
        #if an attribute name has been defined for this variable
        #then use it. otherwise, sanitize the name into an identifier
        if key is not None:
            Dictionary = Dictionary[key]
            
        Name = Gui_Name = None
            
        if NAME in Dictionary:
            Name = Gui_Name = Dictionary[NAME]
            if GUI_NAME in Dictionary:
                Gui_Name = Dictionary[GUI_NAME]
                
        elif GUI_NAME in Dictionary:
            Gui_Name = Name = Dictionary[GUI_NAME]
            if NAME in Dictionary:
                Name = Dictionary[Name]
            
        #sanitize the attribute name string to make it a valid identifier
        if Sanitize:
            Name = self._Sanitize_Attribute_String(Name)
        if Name is None:
            Name = "unnamed"
            P_Name = kwargs.get('Parent_Name')
            P_Type = kwargs.get('Parent_Type')
            Index = kwargs.get('Key_Name')
            Type = Dictionary.get(TYPE)
            
            if Type is not None:
                print(('ERROR: NAME MISSING IN FIELD OF TYPE "%s" '+
                       'IN INDEX "%s" OF "%s" OF TYPE "%s"') %
                      (Type, Index, P_Name, P_Type))
            else:
                print(('ERROR: NAME MISSING IN FIELD LOCATED IN INDEX "%s" '+
                       'OF "%s" OF TYPE %s') % (Index, P_Name, P_Type))
            self._Bad = True
            
        Dictionary[NAME] = Name
        Dictionary[GUI_NAME] = Gui_Name
        return Name


    def _Sanitize_Attribute_String(self, String, **kwargs):
        '''Converts any string given to it into a usable identifier.
        Converts all spaces and dashes into underscores, and removes all
        invalid characters. If the last character is invalid, it will be
        dropped instead of being replaced with an underscore'''

        """Docstring snippit about commented out code"""
        #and makes sure the string begins with A-Z, a-z, or an underscore.
        #If the string begins with a number, an underscore will be prepended.
        try:
            Sanitized_String = ''
            i = 0
            skipped = False

            #make sure the Sanitized_Strings
            #first character is a valid character
            while (len(Sanitized_String) == 0) and (i < len(String)):
                '''The below code will allow a string to begin
                with an integer, but only by prefixing it with an
                underscore
                This is ugly and should be avoided, but it may be useful
                and can probably be fixed, so rather than deleting it,
                it's being commented out'''
                #if String[i] in "0123456789":
                #    Sanitized_String = '_'+String[i]
                '''Same as the above code(and a replacement for the next
                2 lines of code), except it doesnt prefix the name with an
                underscore. This looks better, but it isnt an identifier'''
                #elif String[i] in Alpha_Numeric_IDs and String[i] != "_":
                #    Sanitized_String = String[i]
                
                #ignore characters until an alphabetic one is found
                if String[i] in Alpha_IDs:
                    Sanitized_String = String[i]
                    
                i += 1

            #replace all invalid characters with underscores
            for i in range(i, len(String)):
                if String[i] in Alpha_Numeric_IDs:
                    Sanitized_String = Sanitized_String + String[i]
                    skipped = False
                elif not skipped:
                    Sanitized_String = Sanitized_String + '_'
                    skipped = True

            #make sure the string doesnt end with an underscore
            while len(Sanitized_String) > 0 and Sanitized_String[-1] == '_':
                Sanitized_String = Sanitized_String[:-1]


            if ((Sanitized_String in Tag_Identifiers and not
                Sanitized_String in Overwritable_Tag_Identifiers)
                or Sanitized_String == ''):
                print("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE NAME.\nWHEN " +
                      "SANITIZED IT BECAME '%s'\n" % (String,Sanitized_String))
                self._Bad = True
                return
            return Sanitized_String
        except Exception: pass
        

    def _Sanitize_Element_Ordering(self, Dictionary, **kwargs):
        '''sets the number of entries in a descriptor block'''
        
        if ENTRIES in Dictionary:
            #because the element count will have already
            #been added, we can use that as our loop count
            Last_Entry = Dictionary[ENTRIES]
            
            i = 0

            Gap_Size = 0

            Offending_Elements = []
            
            while i < Last_Entry:
                if i not in Dictionary:
                    '''if we cant find 'i' in the dict it means we need to
                    shift the elements down by at least 1. #as such, we
                    need to look at least 1 higher for the next element'''
                    Gap_Size += 1
                    Last_Entry += 1
                else:
                    '''if we DID find the element in the dictionary we need
                    to check if there are any gaps and, if so, shift down'''
                    if Gap_Size > 0:
                        Dictionary[i-Gap_Size] = Dictionary[i]
                        Offending_Elements.append(Dictionary.pop(i))
                i += 1
                
            if Gap_Size > 0:
                print("WARNING: Descriptor element ordering needed to "+
                      "be sanitized.\n   Check '%s' for bad element ordering."
                      % self.Cls_ID)
                
                if GUI_NAME in Dictionary:
                    print('\n   GUI_NAME of offending block is "'+
                          str(Dictionary[GUI_NAME]))
                elif NAME in Dictionary:
                    print('\n   NAME of offending block is "'+
                          str(Dictionary[NAME]))
                else:
                    print("\n   Offending block is not named.\n")
                
                print('\n   Offending attributes in the block are:')
                for Element in Offending_Elements:
                    if GUI_NAME in Element:
                        print('      ' + str(Element[GUI_NAME]) )
                    elif NAME in Element:
                        print('      ' + str(Element[NAME]) )
                    else:
                        print("      (unnamed)")
                print()


    def Mod_Get_Set(*args, **kwargs):        
        '''Used for getting and setting values in a structure that are
        located at "Path" and must be mod divided by some number "Mod"
        when returned and multiplied by that same number when set.

        This is intended to be used as a SIZE or POINTER function.'''
        
        New_Val = kwargs.get("New_Value")
        Modulus = kwargs.get("Mod", 8)
        Parent  = kwargs.get("Parent")
        Path    = kwargs.get("Path")
        
        if New_Val is None:
            return Parent.Get_Neighbor(Path)//Modulus
        return Parent.Set_Neighbor(Path, New_Val*Modulus)


def Construct():
    '''
    This function exists as a common entry point to
    construct a Tag_Def. All Tag_Def class modules
    should have a 'Construct' function so they can all be
    located by a Tag_Constructors automatic indexing function.
    '''
    
    return Tag_Def
