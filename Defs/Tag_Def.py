'''docstring'''
import sys

from math import log, ceil
from copy import copy

from supyr_struct.Defs.Constants import *
from supyr_struct.Defs.Common_Structures import *

def Construct():
    '''
    This function exists as a common entry point to
    construct a Tag_Def. All Tag_Def class modules
    should have a 'Construct' function so they can all be
    located by a Tag_Constructors automatic indexing function.
    '''
    
    return Tag_Def


class Tag_Def():
    '''docstring'''
    
    #primarily used for locating tags when indexing a collection of
    #them, but also used as the extension when writing a tag to a file
    Ext = ".tag"
    #used for identifying a tag and for telling the tag
    #constructor which tag you are telling it to build.
    #Each Cls_ID must be unique for each Tag_Def
    Cls_ID = ""
    #used for describing the structure of a tag.
    #this is where everything about the structure is defined.
    Tag_Structure = {}
    #The module to use to build this definitions Tag_Obj from
    Tag_Obj = None
    #specifies that the object is only partially defined and any edits to
    #it must be done to a copy of the original data in order to keep all of
    #the undefined data intact. Structures SHOULD NEVER be added or deleted
    #from an incomplete object, though you are not prevented from doing so.
    Incomplete = False
    #The alignment method to use for aligning structures and
    #their entries to byte boundaries based on each ones size.
    Align_Mode = ALIGN_NONE
    #used for storing individual or supplementary pieces of the structure
    Structures = {}
    #The default endianness to use for every field in the tag
    #This can be overridden by specifying the endianness per field
    Endian = { 'big':'>', 'little':'<' }.get(sys.byteorder.lower(), '<')

    #initialize the class
    def __init__(self, **kwargs):
        '''docstring'''

        if not hasattr(self, "Ext"):
            self.Ext = kwargs.get("Ext", ".tag")
        if not hasattr(self, "Cls_ID"):
            self.Cls_ID = kwargs.get("Cls_ID", "")
        if not hasattr(self, "Tag_Structure"):
            self.Tag_Structure = kwargs.get("Tag_Structure", {})
        if not hasattr(self, "Tag_Obj"):
            self.Tag_Obj = kwargs.get("Tag_Obj", None)
        if not hasattr(self, "Incomplete"):
            self.Incomplete = kwargs.get("Incomplete", False)
        if not hasattr(self, "Align"):
            self.Align_Mode = kwargs.get("Align", ALIGN_NONE)
        if not hasattr(self, "Structures"):
            self.Structures = {}
        if not hasattr(self, "Endian"):
            self.Endian = kwargs.get("Endian", { 'big':'>', 'little':'<' }.\
                                     get(sys.byteorder.lower(), '<'))
        
        #Used to signal to the Sanitize() function that some
        #kind of error was encountered during sanitization.
        self._Bad = False

        #make sure the Endian value is valid
        assert self.Endian in ('<','>')
        
        if self.Tag_Structure:
            self.Tag_Structure = self.Sanitize(self.Tag_Structure)

        if isinstance(self.Structures, dict):
            for key in self.Structures:
                self.Structures[key] = self.Sanitize(self.Structures[key])


    def Decode_Value(self, Value, Key=None, P_Name=None, P_Type=None):
        '''docstring'''
        if isinstance(Value, bytes):
            try:
                if P_Type is not None:
                    Value = P_Type.Decoder(Value)
                elif self.End == '<':
                    Value = int.from_bytes(Value, 'little')
                else:
                    Value = int.from_bytes(Value, 'big')
            except Exception:
                print(("ERROR: UNABLE TO DECODE THE BYTES %s IN '%s' "+
                       "OF '%s' AS '%s'.\n") %(Value, Key, P_Name, P_Type))
                self._Bad = True
        return Value
    

    def Get_Align(self, Dict, key):
        This_Dict = Dict[key]
        Type = This_Dict.get(TYPE)
        Size = Align = 1

        if Type.Is_Raw:
            Size = 1
        elif Type.Is_Data or (Type.Is_Bit_Based and Type.Is_Struct):
            '''if the entry is data(or a bitstruct) then align
            it by its size, or by char size if its a string'''
            if Type.Is_Str:
                Size = Type.Size
            else:
                Size = self.Get_Size(Dict, key)
        elif Type.Is_Array:
            try:
                Align = self.Get_Align(Dict[key], SUB_STRUCT)
            except Exception:
                pass
        elif Type.Is_Struct:
            '''search through all entries in the struct
            to find the largest alignment and use it'''
            Align = 1
            for i in range(This_Dict.get(ENTRIES, 1)):
                A = self.Get_Align(This_Dict, i)
                if A > Align: Align = A
                #early return for speedup
                if Align >= ALIGN_MAX:
                    return ALIGN_MAX
        
        if ALIGN in This_Dict:
            #alignment is specified manually
            Align = This_Dict[ALIGN]
        elif self.Align_Mode == ALIGN_AUTO and Size > 0:
            #automatic alignment is to be used
            Align = 2**int(ceil(log(Size, 2)))
            if Align > ALIGN_MAX:
                Align = ALIGN_MAX

        return Align


    def Get_Size(self, Dict, key):
        '''docstring'''
        This_Dict = Dict[key]
        Type = This_Dict[TYPE]

        #make sure we have names for error reporting
        try:
            P_Name = Dict[GUI_NAME]
        except Exception:
            P_Name = Dict.get(NAME, 'unnamed')
            
        try:
            Name = This_Dict[GUI_NAME]
        except Exception:
            Name = This_Dict.get(NAME, 'unnamed')
            
        if ((Type.Is_Var_Size and Type.Is_Data) or
            (SIZE in This_Dict and  isinstance(This_Dict[SIZE], (int,bytes)))):
            if SIZE not in This_Dict:
                print("ERROR: Var_Size DATA MUST HAVE ITS SIZE SPECIFIED IN "+
                      "ITS DESCRIPTOR.\n    OFFENDING ELEMENT FOUND IN "+
                      "'%s' AND NAMED '%s'.\n" % (P_Name, Name))
                self._Bad = True
                return 0
                
            Size = This_Dict[SIZE] = self.Decode_Value(This_Dict[SIZE],
                                                        SIZE, Name)
        elif Type.Is_Struct:
            self.Include_Attributes(This_Dict)
            self.Set_Entry_Count(This_Dict)
            self.Sanitize_Element_Ordering(This_Dict)
            Size = 0
            try:
                for i in range(This_Dict[ENTRIES]):
                    Size += self.Get_Size(This_Dict, i)
            except Exception: pass
        else:
            Size = Type.Size

        if (Type.Is_Bit_Based and not Type.Is_Struct and not
            Dict[TYPE].Is_Bit_Based):
            Size = int(ceil(Size/8))
            
        return Size


    def Include_Attributes(self, Dict):
        '''docstring'''
        #combine the entries from INCLUDE into the dictionary
        if isinstance(Dict.get(INCLUDE), dict):
            for i in Dict[INCLUDE]:
                #dont replace it if an attribute already exists there
                if i not in Dict:
                    Dict[i] = Dict[INCLUDE][i]
            del Dict[INCLUDE]
            self.Set_Entry_Count(Dict)


    def Sanitize(self, Struct):
        '''Use this to sanitize a descriptor.
        Adds key things to the Tag_Def that may be forgotten,
        mistyped, or simply left out and informs the user of
        potential and definite issues through print().'''

        #reset the error status to normal
        self._Bad = False
        #enclosing the Tag_Structure in a dictionary is necessary for
        #it to properly set up the topmost level of the Tag_Structure
        Struct_Cont = self.Sanitize_Loop({TYPE:Container, NAME:"tmp", 0:Struct},
                                         Key_Name=None, End=self.Endian)

        #if an error occurred while sanitizing, raise an exception
        if self._Bad:
            raise Exception(("The '%s' Tag_Def encountered errors "+
                             "during its construction.") % self.Cls_ID)
        
        return Struct_Cont[0]


    def Sanitize_Loop(self, Dict, **kwargs):
        '''docstring'''
        self.Include_Attributes(Dict)

        if TYPE not in Dict:
            #the type doesnt exist, so nothing needs to be done. quit early
            return Dict
        
        P_Type = Dict.get(TYPE)
        if P_Type not in Field_Types.All_Field_Types:
            self._Bad = True
            raise TypeError("'TYPE' in descriptors must be a valid Field_Type.")

        '''if the block is a List_Block, but the descriptor requires that
        it have a CHILD attribute, set the DEFAULT to a P_List_Block.
        Only do this though, if there isnt already a default set.'''
        if (issubclass(P_Type.Py_Type, Tag_Blocks.List_Block)
            and 'CHILD' in Dict and 'DEFAULT' not in Dict
            and not issubclass(P_Type.Py_Type, Tag_Blocks.P_List_Block)):
            Dict['DEFAULT'] = Tag_Blocks.P_List_Block

        '''if the block is a While_List_Block, but the descriptor requires that
        it have a CHILD attribute, set the DEFAULT to a P_While_List_Block.
        Only do this though, if there isnt already a default set.'''
        if (issubclass(P_Type.Py_Type, Tag_Blocks.While_List_Block)
            and 'CHILD' in Dict and 'DEFAULT' not in Dict
            and not issubclass(P_Type.Py_Type, Tag_Blocks.P_While_List_Block)):
            Dict['DEFAULT'] = Tag_Blocks.P_While_List_Block
        
        PT = kwargs.get('P_Type')
        Error_Str = ''
        
        #series of checks to make sure bit and
        #byte level objects arent mixed improperly
        if (isinstance(PT, Field_Types.Field_Type) and
            PT.Is_Bit_Based and PT.Is_Struct):
            #Parent is a bitstruct
            if not P_Type.Is_Bit_Based:
                #but this is bitbased
                Error_Str += ("ERROR: Bit_Structs MAY ONLY CONTAIN "+
                              "Bit_Based 'Data' Field_Types.\n")
            elif P_Type.Is_Struct:
                Error_Str += "ERROR: Bit_Structs CANNOT CONTAIN Structs.\n"
        elif P_Type.Is_Bit_Based and not P_Type.Is_Struct:
            Error_Str += ("ERROR: Bit_Based Field_Types MUST "+
                          "RESIDE IN A Bit_Based Struct.\n")
    
        #Get the name of this block so it
        #can be used in the below routines
        try:
            P_Name = Dict[NAME]
        except Exception:
            P_Name = Dict.get(GUI_NAME, "unnamed")

        #change the Field_Type to the endianness specified                
        End = kwargs['End'] = Dict.get(ENDIAN, kwargs['End'])
        if End in '><':
            P_Type = Dict[TYPE] = {'>':P_Type.Big, '<':P_Type.Little}[End]
        else:
            raise ValueError("Endianness characters must be either '<' "+
                             "for little endian or '>' for big endian.")
        kwargs['P_Type'] = P_Type
        kwargs['P_Name'] = P_Name
        
        #NAME_MAP is used as a map of the names of
        #the variables to the index they are stored in.
        #ATTR_OFFS stores the offset of each of the
        #attributes. Stores them by both Name and Index
        if P_Type.Is_Hierarchy:
            Dict[NAME_MAP] = {}
            self.Set_Entry_Count(Dict, kwargs["Key_Name"])
            self.Sanitize_Element_Ordering(Dict, **kwargs)
        if P_Type.Is_Array:
            kwargs["Sub_Array"] = True
            
        if P_Type.Is_Struct:
            kwargs["Sub_Struct"], Dict[ATTR_OFFS] = True, {}
        elif kwargs.get('Sub_Struct'):
            '''Check to make sure this data type is valid to be
            inside a structure if it currently is inside one.'''
            if P_Type.Is_Container:
                Error_Str += ("ERROR: Containers CANNOT BE USED IN A "+
                              "Struct.\nStructs ARE REQUIRED TO BE "+
                              "A FIXED SIZE AND Containers ARE NOT.\n")
        
            elif (P_Type.Is_Var_Size and
                  not isinstance(Dict.get(SIZE), (int, bytes))):
                Error_Str += ("ERROR: TO USE Var_Size DATA IN A "+
                              "Struct THE SIZE MUST BE STATICALLY "+
                              "DEFINED WITH AN INTEGER.\n")

        #if any errors occurred, print them
        if Error_Str:
            print((Error_Str + "    NAME OF OFFENDING ELEMENT IS '%s' " +
                  "OF TYPE '%s'") %(P_Name, P_Type.Name) + "\n")
            self._Bad = True
            Error_Str = ''

        #if a default was in the dict then we try to decode it
        #and replace the default value with the decoded version
        if DEFAULT in Dict and Dict[TYPE].Is_Data:
            Dict[DEFAULT] = self.Decode_Value(Dict[DEFAULT], DEFAULT,
                                              P_Name, P_Type)

        #if the descriptor is for a boolean or enumerator, the
        #NAME_MAP needs to be setup and 
        if P_Type.Is_Bool or P_Type.Is_Enum:
            Name_Set = set()
            Dict['NAME_MAP'] = {}
            if P_Type.Is_Enum:
                Dict['VALUE_MAP'] = {}
            
            '''if the Field_Type is an enumerator or booleans then
            we need to make sure there is a value for each element'''
            self.Set_Entry_Count(Dict)
            self.Sanitize_Element_Ordering(Dict)
            self.Sanitize_Option_Values(Dict, P_Type, **kwargs)
                
            for i in range(Dict['ENTRIES']):
                Name = self.Sanitize_Name(Dict, i)
                if Name in Name_Set:                            
                    print(("ERROR: DUPLICATE NAME FOUND IN %s.\n"
                          +"NAME OF OFFENDING ELEMENT IS %s") %
                          (kwargs["Key_Name"], Name))
                    self._Bad = True
                    continue
                Dict['NAME_MAP'][Name] = i
                if P_Type.Is_Enum:
                    Dict['VALUE_MAP'][Dict[i]['VALUE']] = i
                Name_Set.add(Name)
            #the dict needs to not be modified by the below code
            return Dict
        

        #if the descriptor is a switch, things need to be checked and setup
        if P_Type is Switch:
            #make a copy of the Cases so they can be modified
            Cases = Dict['CASES'] = copy(Dict.get('CASES'))
            if Dict.get('CASE') is None:
                print("ERROR: CASE MISSING IN %s OF TYPE %s\n"%(P_Name,P_Type))
                self._Bad = True
            if Cases is None:
                print("ERROR: CASES MISSING IN %s OF TYPE %s\n"%(P_Name,P_Type))
                self._Bad = True

            #make sure there is a default 
            del Dict['NAME_MAP']
            del Dict['ENTRIES']

            kwargs['Key_Name'] = 'CASES'
            for Case in Cases:
                Cases[Case] = self.Sanitize_Loop(copy(Cases[Case]), **kwargs)
                Type = Cases[Case][TYPE]
                if not issubclass(Type.Py_Type, Tag_Blocks.Tag_Block):
                    print("ERROR: CANNOT USE CASES IN A Switch WHOSE "+
                          "Field_Type.Py_Type IS NOT A Tag_Block.\n"+
                          ("OFFENDING ELEMENT IS %s IN '%s' OF '%s' "+
                           "OF TYPE %s.") % (Case, CASES, P_Name, Type) )
                    self._Bad = True
                self.Sanitize_Name(Cases, Case, **kwargs)
                
            kwargs['Key_Name'] = 'DEFAULT'
            Dict['DEFAULT'] = self.Sanitize_Loop(Dict.get('DEFAULT', Void_Desc),
                                                 **kwargs)
            
            #the dict needs to not be modified by the below code
            return Dict
            

        #if a variable doesnt have a specified offset then
        #this will be used as the starting offset and will
        #be incremented by the size of each variable after it
        Default_Offset = 0
        #the largest alignment size requirement of any entry in this block
        L_Align = 1

        '''The non integer entries aren't part of substructs, so
        save the substruct status to a temp var and set it to false'''
        temp1, kwargs['Sub_Struct'] = kwargs.get('Sub_Struct'), False
        temp2, kwargs['Sub_Array']  = kwargs.get('Sub_Array'), False
        
        #loops through the descriptors non-integer keyed sub-sections
        for key in Dict:
            if not isinstance(key, int):
                #replace with a copy so the original is intact
                Dict[key] = copy(Dict[key])
                if key not in Tag_Identifiers:
                    print(("WARNING: FOUND ENTRY IN DESCRIPTOR OF '%s' UNDER "+
                           "UNKNOWN KEY '%s' OF TYPE %s.\n    If this is "+
                           "intentional, add the key to supyr_struct."+
                           "constants.Tag_Ids.\n") %(P_Name, key, type(key)))
                if isinstance(Dict[key], dict):
                    kwargs["Key_Name"] = key
                    Type = Dict[key].get(TYPE)
                    
                    self.Sanitize_Loop(Dict[key], **kwargs)

                    if Type:
                        #if this is the repeated substruct of an array
                        #then we need to calculate and set its alignment
                        if ((key == SUB_STRUCT or Type.Is_Str) and
                            ALIGN not in Dict[key]):
                            Align = self.Get_Align(Dict, key)
                            #if the alignment is 1 then no
                            #adjustments need be made
                            if Align > 1:
                                Dict[key][ALIGN]
                            
                        Sani_Name = self.Sanitize_Name(Dict, key, **kwargs)
                        if key != SUB_STRUCT:
                            Dict[NAME_MAP][Sani_Name] = key
                        
        #restore the Sub_Struct status
        kwargs['Sub_Struct'], kwargs['Sub_Array'] = temp1, temp2

        """Loops through each of the numbered entries in the descriptor.
        This is done separate from the non-integer dict entries because
        a check to sanitize offsets needs to be done from 0 up to ENTRIES.
        Looping over a dictionary by its keys will do them in a non-ordered
        way and the offset sanitization requires them to be done in order."""
        if ENTRIES in Dict:
            Name_Set = set()
            Removed = 0 #number of dict entries removed
            
            '''loops through the entire descriptor
            and finalizes each of the attributes'''
            for key in range(Dict[ENTRIES]):
                #Make sure to shift upper indexes down by how many
                #were removed and make a copy to preserve the original
                Dict[key-Removed] = This_Dict = copy(Dict[key])
                key -= Removed
                
                if isinstance(This_Dict, dict):
                    Type = This_Dict.get(TYPE)
                    if Type is not None:
                        '''make sure the block has an offset if it needs one'''
                        if P_Type.Is_Struct and OFFSET not in This_Dict:
                            This_Dict[OFFSET] = Default_Offset
                    elif P_Type:
                        #if this int keyed dict has no TYPE, but is inside a
                        #dict with a TYPE, then something is probably wrong
                        #OR this dict contains a PAD key:value pair
                        if PAD in This_Dict:
                            '''the dict was found to be padding, so increment
                            the default offset by it, remove the entry from the
                            dict, and adjust the removed and entry counts.'''
                            Default_Offset += This_Dict[PAD]
                                
                            Removed += 1
                            Dict[ENTRIES] -= 1
                            del Dict[key]
                            continue
                        else:
                            #Pad entry doesnt exist. This is an error.
                            try:
                                Name = Dict[GUI_NAME]
                            except Exception:
                                Name = Dict.get(NAME, 'unnamed')
                                
                            if len(This_Dict):
                                raise LookupError(('Non-empty dictionary found'+
                                    ' in "%s" descriptor of type "%s" at index'+
                                    ' "%s".') % (Name, Dict[TYPE], key) )
                            else:
                                raise LookupError('Empty dictionary found in '+
                                   '"%s" descriptor of type "%s" at index "%s".'
                                    % (Name, Dict[TYPE], key) )
                            
                    kwargs["Key_Name"] = key
                    self.Sanitize_Loop(This_Dict, **kwargs)

                    if Type:
                        Sani_Name = self.Sanitize_Name(Dict,key,**kwargs)
                        Dict[NAME_MAP][Sani_Name] = key
                        
                        Name = This_Dict[NAME]
                        if Name in Name_Set:
                            print(("ERROR: DUPLICATE NAME FOUND IN '%s'.\n"
                                  +"    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                                  (P_Name, Name))
                            self._Bad = True
                        Name_Set.add(Name)

                        #get the size of the entry(if the parent dict requires)
                        if ATTR_OFFS in Dict:
                            Size = self.Get_Size(Dict, key)
                            
                        '''add the offset to ATTR_OFFS in the parent dict'''
                        if ATTR_OFFS in Dict and OFFSET in This_Dict:
                            #if bytes were provided as the offset we decode
                            #them and replace it with the decoded version
                            Offset = self.Decode_Value(This_Dict[OFFSET],
                                                        OFFSET, Name)

                            #make sure not to align within bit structs
                            if not(Type.Is_Bit_Based and P_Type.Is_Bit_Based):
                                Align = self.Get_Align(Dict, key)
                            
                                if Align > ALIGN_MAX:
                                    Align = ALIGN_MAX
                                if Align > L_Align:
                                    L_Align = Align
                                if Align > 1:
                                    Offset += (Align-(Offset%Align))%Align
                                    
                            Default_Offset = Offset + Size

                            #set the offset and delete the OFFSET entry
                            Dict[ATTR_OFFS][This_Dict[NAME]] = Offset
                            del This_Dict[OFFSET]
                            
        #Make sure all structs have a defined SIZE
        if P_Type is not None and P_Type.Is_Struct and Dict.get(SIZE) is None:
            if P_Type.Is_Bit_Based:
                Default_Offset = int(ceil(Default_Offset/8))
                
            #calculate the padding based on the largest alignment
            Padding = (L_Align-(Default_Offset%L_Align))%L_Align
            Dict[SIZE] = Default_Offset + Padding
        
        return Dict
        

    def Sanitize_Element_Ordering(self, Dict, **kwargs):
        '''sets the number of entries in a descriptor block'''
        
        if ENTRIES in Dict:
            #because the element count will have already
            #been added, we can use that as our loop count
            Last_Entry = Dict[ENTRIES]
            
            i = 0

            Gap_Size = 0

            Offending_Elements = []
            
            while i < Last_Entry:
                if i not in Dict:
                    '''if we cant find 'i' in the dict it means we need to
                    shift the elements down by at least 1. as such, we
                    need to look at least 1 higher for the next element'''
                    Gap_Size += 1
                    Last_Entry += 1
                else:
                    '''if we DID find the element in the dictionary we need
                    to check if there are any gaps and, if so, shift down'''
                    if Gap_Size > 0:
                        Dict[i-Gap_Size] = Dict[i]
                        Offending_Elements.append(Dict.pop(i))
                i += 1
                
            if Gap_Size > 0:
                print("WARNING: Descriptor element ordering needed to "+
                      "be sanitized.\n   Check '%s' for bad element ordering."
                      % self.Cls_ID)
                
                if GUI_NAME in Dict:
                    print('\n   GUI_NAME of offending block is "'+
                          str(Dict[GUI_NAME]))
                elif NAME in Dict:
                    print('\n   NAME of offending block is "'+
                          str(Dict[NAME]))
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


    def Sanitize_Gui_Name(self, Name_String, **kwargs):
        """docstring"""
        #replace all underscores with spaces and
        #remove all leading and trailing spaces
        try:
            GUI_Name_String = Name_String.replace('_', ' ').strip(' ')
            
            #make sure the string doesnt contain
            #any characters that cant be printed
            for char in '\a\b\f\n\r\t\v':
                if char in GUI_Name_String:
                    print("ERROR: CANNOT USE '%s' AS A GUI_NAME AS "+
                          "IT CONTAINS UNPRINTABLE STRING LITERALS.")
                    self._Bad = True
                    return None
            
            if GUI_Name_String == '':
                print(("ERROR: CANNOT USE '%s' AS A GUI_NAME.\n" % String) +
                       "WHEN SANITIZED IT BECAME AN EMPTY STRING." )
                self._Bad = True
                return None
            return GUI_Name_String
        except Exception:
            return None

    def Sanitize_Name(self, Dict, key=None, Sanitize=True, **kwargs):
        '''docstring'''
        if key is not None:
            Dict = Dict[key]
            
        Name = Gui_Name = None
            
        if NAME in Dict:
            Name = Dict[NAME]
            Gui_Name = Dict.get(GUI_NAME, Name)
        elif GUI_NAME in Dict:
            Gui_Name = Dict[GUI_NAME]
            Name = Dict.get(NAME, Gui_Name)
            
        #sanitize the attribute name string to make it a valid identifier
        if Sanitize:
            Name = self.Sanitize_Name_String(Name)
            Gui_Name = self.Sanitize_Gui_Name(Gui_Name)
        if Name is None:
            Name = "unnamed"
            P_Name = kwargs.get('P_Name')
            P_Type = kwargs.get('P_Type')
            Index = kwargs.get('Key_Name')
            Type = Dict.get(TYPE)
            
            if Type is not None:
                print(('ERROR: NAME MISSING IN FIELD OF TYPE "%s" '+
                       'IN INDEX "%s" OF "%s" OF TYPE "%s"') %
                      (Type, Index, P_Name, P_Type))
            else:
                print(('ERROR: NAME MISSING IN FIELD LOCATED IN INDEX "%s" '+
                       'OF "%s" OF TYPE %s') % (Index, P_Name, P_Type))
            self._Bad = True
        if Gui_Name is None:
            Gui_Name = Name
            
        Dict[NAME] = Name
        Dict[GUI_NAME] = Gui_Name
        return Name


    def Sanitize_Name_String(self, String, **kwargs):
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
            while len(Sanitized_String) == 0 and i < len(String):
                #ignore characters until an alphabetic one is found
                if String[i] in Alpha_IDs:
                    Sanitized_String = String[i]
                    
                i += 1

            #replace all invalid characters with underscores
            for i in range(i, len(String)):
                if String[i] in Alpha_Numeric_IDs:
                    Sanitized_String += String[i]
                    skipped = False
                elif not skipped:
                    #no matter how many invalid characters occur in
                    #a row, replace them all with a single underscore
                    Sanitized_String += '_'
                    skipped = True

            #make sure the string doesnt end with an underscore
            Sanitized_String.rstrip('_')
            
            if Sanitized_String in Tag_Identifiers or Sanitized_String == '':
                print("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE NAME.\nWHEN " +
                      "SANITIZED IT BECAME '%s'\n" % (String,Sanitized_String))
                self._Bad = True
                return None
            return Sanitized_String
        except Exception:
            return None
        

    def Sanitize_Option_Values(self, Dict, Type, **kwargs):
        '''docstring'''
        j = int(Type.Is_Bool)
        for i in range(Dict.get('ENTRIES',0)):
            Opt = Dict[i]
            if isinstance(Opt, dict):
                if VALUE not in Opt:
                    #the way this breaks down is if the Field_Type is a
                    #boolean, the equation simplifies to "2**i", if it
                    #is an enumerator, it simplifies down to just "i"
                    #this is faster than a conditional check
                    Opt[VALUE] = (i+j*(1-i))*2**(j*i)
                if kwargs.get('P_Type'):
                    Opt[VALUE] = self.Decode_Value(Opt[VALUE], i,
                                                    kwargs.get('P_Name'),
                                                    kwargs.get('P_Type'))

    def Set_Entry_Count(self, Dict, Key=None):
        '''sets the number of entries in a descriptor block'''
        if Key not in (NAME_MAP, ATTR_OFFS, INCLUDE):
            Entry_Count = 0
            Largest = 0
            for i in Dict:
                if isinstance(i, int):
                    Entry_Count += 1
                    if i > Largest:
                        Largest = i
                        
            #we dont want to add an entry count to the NAME_MAP
            #dict or the INCLUDE dict since they aren't parsed
            Dict[ENTRIES] = Entry_Count
