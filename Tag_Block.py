import sys

from array import array
from copy import copy, deepcopy
from mmap import mmap
from os.path import splitext
from sys import getsizeof
from string import ascii_uppercase, ascii_lowercase
from traceback import format_exc

from supyr_struct.Defs.Constants import *


#Tag_Obj and Tag_Block need to circularly reference each other.
#In order to do this properly, each module tries to import the other.
#If one succeeds then it provides itself as a reference to the other.
'''try to import the Tag_Obj module. if it fails then
its because the Tag_Obj module is already being built'''
try:
    from supyr_struct.Objs import Tag_Obj
    Tag_Obj.Tag_Block = sys.modules[__name__]
except ImportError: pass


'''Code runs slightly faster if these methods are here instead
of having to be called through the list class every time
and it helps to shorten the width of a lot of lines of code'''
_LGI = list.__getitem__
_LSI = list.__setitem__
_LDI = list.__delitem__
_LSO  = list.__sizeof__
_LApp = list.append
_LExt = list.extend
_LIns = list.insert
_LPop = list.pop

_OSA = object.__setattr__
_OGA = object.__getattribute__
_ODA = object.__delattr__


class Tag_Block(object):
    '''
    This class exists to be subclassed in order to let the library
    know that a particular object can be treated as a Tag_Block.

    Tag_Blocks must have:
    
        Properties
        PARENT ------------ Reference to the Tag_Block's parent Tag_Block/Obj
        DESC -------------- A descriptor to define how its data is handeled
        Bin_Size ---------- Returns the serialized byte size of the Tag_Block

    Tag_Blocks must:
        Allow accessing entries in their descriptor as if they were attributes
            i.e. "Tag_Block.SIZE" is the same as "Tag_Block.DESC['SIZE']"

    This class is not intended to be used as is.
    '''

    #EXPAND THE ABOVE DESCRIPTION

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("'Tag_Block' is not a usable class as "+
                                  "is, and is intended to be subclassed.")

    

class List_Block(Tag_Block, list):
    """
    List_Block are(currently) the sole method of storing structure data.
    They are comparable to a mutable version of namedtuples.
    They function as a list where each entry can be accessed
    by its attribute name defined in the descriptor.

    For example: If the value in key "0" in the descriptor of the
    object "Block" has a key:value pair of "NAME":"Data", then doing:
    
    Block[0] = "here's a string"
    
    is the same as doing:
    
    Block.Data = "here's a string"
    """
    
    __slots__ = ("DESC", "PARENT")

    def __init__(self, Desc=None, Init_Block=None, Parent=None, **kwargs):
        '''docstring'''
        
        #This section of code might end up being removed or replaced
        '''The Type section of it needs to exist for now though in order
        to allow the default value of Field_Types to be set to Tag_Blocks'''

        if Desc is None:
            try:
                #if there is no descriptor provided, then
                #a unique, bare bones one will be used to
                #make sure the object works properly.
                _OSA(self, "DESC", {'ATTR_MAP':{}, 'ATTR_OFFS':{}, 'SIZE':0,
                                    'ENTRIES':0, 'TYPE':kwargs.get('Type'),
                                    'NAME':kwargs.get('Name', "UNNAMED")})
            except KeyError:
                raise TypeError("Cannot construct List_Block without " +
                                "a descriptor or a valid Type.")
        else:
            _OSA(self, "DESC", Desc)

        _OSA(self, 'PARENT', Parent)
        
        self.Read(Init_Block, **kwargs)
                 

    
    def __str__(self, **kwargs):
        '''docstring'''
        #set the default things to show
        Show = set(['Type', 'Name', 'Value', 'Offset', 'Size', 'Children'])
        
        Seen = kwargs['Seen'] = set(kwargs.get('Seen',()))
        Seen.add(id(self))
        
        if "Show" in kwargs:
            Show = kwargs['Show']
            if isinstance(kwargs["Show"], str):
                Show = set([Show])
            else:
                Show = set(Show)
                
        Level = kwargs.get('Level', 0)
        Indent = kwargs.get('Indent', BLOCK_PRINT_INDENT)
        Block_Index = kwargs.get('Block_Index', None)
        Print_Raw = kwargs.get('Print_Raw', False)
        Precision = kwargs.get('Precision', None)
        Printout = kwargs.get('Printout', False)

        #if the list includes 'All' it means to show everything
        if 'All' in Show:
            Show.remove('All')
            Show.update(("Name", "Value", "Type", "Offset", "Children",
                         "Elements", "Flags", "Unique", "Size", "Index",
                         "Py_ID", "Py_Type", "Bin_Size", "Ram_Size"))

        Print_Ram_Size = "Ram_Size" in Show
        Print_Bin_Size = "Bin_Size" in Show
        Print_Elements = "Elements" in Show
        Print_Children = "Children" in Show
        Print_Py_Type = "Py_Type" in Show
        Print_Py_ID = "Py_ID" in Show
        Print_Offset = "Offset" in Show
        Print_Unique = "Unique" in Show
        Print_Flags = "Flags" in Show
        Print_Value = "Value" in Show
        Print_Type = "Type" in Show
        Print_Name = "Name" in Show
        Print_Size = "Size" in Show
        Print_Index = "Index" in Show
        
        if Print_Ram_Size: Show.remove('Ram_Size')
        if Print_Bin_Size: Show.remove('Bin_Size')

        kwargs['Show'] = Show

        #used to display different levels of indention
        Indent_Str0 = ' '*Indent*Level
        Indent_Str1 = ' '*Indent*(Level+1)
        Indent_Str2 = ' '*Indent*(Level+2)
        
        Tag_String =  Indent_Str0 + '['
        kwargs['Level'] = Level+1
        
        tempstring = ''
        
        if Print_Index and Block_Index is not None:
            tempstring = ', #:%s' % Block_Index
        if Print_Type and hasattr(self, TYPE):
            tempstring += ', %s' % _OGA(self,'DESC')['TYPE'].Name
        if Print_Offset:
            if hasattr(self, POINTER):
                tempstring += ', Pointer:%s' % self.Get_Meta(POINTER)
            else:
                try:
                    tempstring += (', Offset:%s' %
                                   self.PARENT['ATTR_OFFS'][_OGA(self,'DESC')['NAME']])
                except Exception:
                    pass
        if Print_Unique:
            tempstring += ', Unique:%s' % (ORIG_DESC in _OGA(self,'DESC'))
        if Print_Py_ID:
            tempstring += ', Py_ID:%s' % id(self)
        if Print_Py_Type:
            tempstring += ', Py_Type:%s' % _OGA(self,'DESC')['TYPE'].Py_Type
        if Print_Size:
            if hasattr(self, SIZE) and not _OGA(self,'DESC')['TYPE'].Is_Container:
                tempstring += ', Size:%s' % self.Get_Size()
            tempstring += ', Entries:%s' % len(self)
        if Print_Name and hasattr(self, NAME):
            tempstring += ', %s' % _OGA(self,'DESC')['NAME']

        Tag_String += tempstring[1:]
            
        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''
        else:
            Tag_String += '\n'

        #create an Attr_Offsets list for printing attribute offsets
        try:
            Attr_Offsets = _OGA(self,'DESC')['ATTR_OFFS']
        except Exception:
            Attr_Offsets = ()
            
        #Print all this List_Block's indexes
        for i in range(len(self)):
            Data = self[i]
            kwargs['Block_Index'] = i
            
            tempstring = ''
            
            if isinstance(Data, Tag_Block):
                if Print_Index:
                    tempstring = '[ #:%s' % i
                if id(Data) in Seen:
                    Tag_String += (Indent_Str1 + tempstring +
                                   " RECURSIVE BLOCK '%s' ]" % (Data.NAME))
                else:
                    try:
                        Tag_String += Data.__str__(**kwargs)
                    except Exception:
                        Tag_String += '\n' + format_exc()
            else:
                Tag_String += Indent_Str1 + '['
                try:
                    if _OGA(self,'DESC')['TYPE'].Is_Array:
                        Attr_Desc = _OGA(self,'DESC')['SUB_STRUCT']
                    else:
                        Attr_Desc = _OGA(self,'DESC')[i]
                except Exception: 
                    Tag_String += (" NO DESCRIPTOR FOR OBJECT "+
                                   "OF TYPE '%s' ]\n" % type(Data))
                    continue

                Type = Attr_Desc[TYPE]
                if Print_Index:
                    tempstring += ', #:%s' % i
                if Print_Type:
                    tempstring += ', %s' % Attr_Desc[TYPE].Name
                if Print_Offset and Attr_Desc[NAME] in Attr_Offsets:
                    tempstring += ', Offset:%s' % Attr_Offsets[Attr_Desc[NAME]]
                if Print_Unique:
                    tempstring += ', Unique:%s' % (ORIG_DESC in Attr_Desc)
                if Print_Py_ID:
                    tempstring += ', Py_ID:%s' % id(Data)
                if Print_Py_Type:
                    tempstring += ', Py_Type:%s' % Type.Py_Type
                if Print_Size:
                    try:
                        tempstring += ', Size:%s' % self.Get_Size(i)
                    except Exception:
                        pass
                if Print_Name and NAME in Attr_Desc:
                    tempstring += ', %s' % Attr_Desc[NAME]
                    
                if Print_Value:
                    if isinstance(Data, float) and isinstance(Precision, int):
                        tempstring += ', %s'%("{:."+str(Precision)+"f}")\
                                      .format(round(Data, Precision))
                    elif Type.Is_Raw and not Print_Raw:
                        tempstring += ', [ RAWDATA ]'
                    else:
                        tempstring += ', %s' % Data

                '''This has been commented out as it is worthless with
                how I have decided to handle flags and enumerators'''
                #Flag_Element_String = ''
                #
                #if (Print_Elements and ELEMENTS in Attr_Desc):
                #    Flag_Element_String += "\n"
                #    for i in range(Attr_Desc[ELEMENTS][ENTRIES]):
                #        if Attr_Desc[ELEMENTS][i][VALUE] == Data:
                #            Flag_Element_String += (Indent_Str2 + '[ %s ]\n' %
                #                                (Attr_Desc[ELEMENTS][i][NAME]))
                #            
                #    if Flag_Element_String == '\n':
                #        Flag_Element_String += (Indent_Str2 +
                #                            '[ INVALID ENUM SELECTION ]\n')
                #     
                #'''Display the flags and enumerator elements'''
                #if Print_Flags and FLAGS in Attr_Desc:
                #    Flag_Element_String += "\n"
                #    for i in range(Attr_Desc[FLAGS][ENTRIES]):
                #        Flag = Attr_Desc[FLAGS][i][VALUE]
                #        Name = Attr_Desc[FLAGS][i][NAME]
                #        Flag_Element_String += (Indent_Str2+'[ %s, %s, %s ]\n'%
                #                                (bool(Data & Flag), Flag, Name))
                #
                #if Flag_Element_String:
                #    Tag_String += (tempstring[1:] +
                #                   Flag_Element_String +
                #                   Indent_Str2 + ']')
                #else:
                #    Tag_String += tempstring[1:] + ' ]'
                Tag_String += tempstring[1:] + ' ]'
                    
            if Printout:
                if Tag_String:
                    print(Tag_String)
                Tag_String = ''
            else:
                Tag_String += '\n'

        if Printout:
            print(Indent_Str1 + ']')
        else:
            Tag_String += Indent_Str1 + ']'
            
        #Print this List_Block's child if it has one
        if ((hasattr(self, 'CHILD') and
             self.CHILD is not None) and Print_Children):
            Child = self.CHILD
            kwargs['Block_Index'] = None
            
            if Printout:
                print(Indent_Str0 + '[ Child:')
            else:
                Tag_String += '\n' + Indent_Str0 + '[ Child:\n'
            
            tempstring = ''
            tempstring2 = ''
            
            if isinstance(Child, Tag_Block):
                if id(Child) in Seen:
                    Tag_String += (Indent_Str1 +
                                   "[ RECURSIVE BLOCK '%s' ]" % (Child.NAME))
                else:
                    try:
                        Tag_String += Child.__str__(**kwargs)
                    except Exception:
                        Tag_String += '\n' + format_exc()
                    
                if Printout:
                    if Tag_String:
                        print(Tag_String)
                    Tag_String = ''
                else:
                    Tag_String += '\n'
                    
            else:  
                Tag_String += Indent_Str1 + '['
                Child_Desc = _OGA(self,'DESC')['CHILD']
                Child_Type = Child_Desc[TYPE]
                    
                if Print_Type:
                    tempstring += ', %s' % Child_Type.Name
                if Print_Unique:
                    tempstring += (', Unique:%s' % (ORIG_DESC in Child_Desc))
                if Print_Py_ID:
                    tempstring += ', Py_ID:%s' % id(Child)
                if Print_Py_Type:
                    tempstring += ', Py_Type:%s' % Child_Type.Py_Type
                if Print_Size and SIZE in Child_Desc:
                    tempstring += ', Size:%s' % self.Get_Size('CHILD')
                if Print_Name and NAME in Child_Desc:
                    tempstring += ', %s' % Child_Desc[NAME]
                
                if Print_Value:
                    if isinstance(Child, float) and isinstance(Precision, int):
                        tempstring2 += ', %s' %("{:."+str(Precision)+"f}")\
                                       .format(round(Child,Precision))
                    elif Child_Type.Is_Raw and not Print_Raw:
                        tempstring2 += ', [ RAWDATA ]'
                    else:
                        tempstring2 += ', %s' % Child

                if Printout:
                    try:
                        print( Tag_String + (tempstring+tempstring2)[1:] + ' ]')
                    except Exception:
                        print(Tag_String + tempstring[1:] +
                              ', UNABLE TO PRINT THIS DATA ]')
                    Tag_String = ''
                else:
                    Tag_String += (tempstring+tempstring2)[1:] + ' ]\n'
                    
            Tag_String += Indent_Str1 + ']'
                    
        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''
        else:
            Tag_String += '\n'

        if Print_Ram_Size:
            Block_Size = self.__sizeof__()
            Tag_String += (Indent_Str0 + '"In-Memory Tag Block" is %s bytes\n'
                           % Block_Size)
            
        if Print_Bin_Size:
            Block_Bin_Size = self.Bin_Size
            Tag_String += (Indent_Str0 + '"Packed Structure" is %s bytes\n'
                           % Block_Bin_Size)

            if Print_Ram_Size and Print_Bin_Size:
                X_Larger = "∞"
                if Block_Bin_Size:
                    Size_Str = "{:." + str(Precision) + "f}"
                    X_Larger = Block_Size/Block_Bin_Size
                    
                    if Precision:
                        X_Larger = Size_Str.format(round(X_Larger, Precision))
                    
                Tag_String += (Indent_Str0 + '"In-Memory Tag Block" is ' +
                               str(X_Larger) + " times as large.\n")
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        else:
            return Tag_String


    
    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''

        #try to get the new blocks parent
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None
            
        Dup_Block = type(self)(_OGA(self,'DESC'),Init_Block=self,Parent=Parent)

        if hasattr(self, CHILD):
            _OSA(Dup_Block, CHILD, self.CHILD)
        
        return Dup_Block

    
    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the same descriptor.'''
        
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        #if there is a parent, copy it
        try:
            Parent = deepcopy(_OGA(self,'PARENT'), memo)
        except AttributeError:
            Parent = None

        #make a new block object sharing the same descriptor.
        #make sure the attributes arent initialized. it'll just waste time.
        Dup_Block = type(self)(_OGA(self,'DESC'),Parent=Parent,Init_Attrs=False)
        memo[id(self)] = Dup_Block
        
        #clear the block so it can be populated
        _LDI(Dup_Block, slice(None, None, None))
        _LExt(Dup_Block, [None]*len(self))
        
        #populate the duplicate
        for i in range(len(self)):
            _LSI(Dup_Block, i, deepcopy(_LGI(self,i), memo))

        #CHILD has to be done last as its structure
        #likely relies on attributes of this, its parent
        if hasattr(self, 'CHILD'):
            _OSA(Dup_Block, 'CHILD', deepcopy(_OGA(self,'CHILD'), memo))
            
        return Dup_Block

    
    def __sizeof__(self, Seen_Set = None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _LSO(self)+getsizeof(_OGA(self, "__slots__"))

        if hasattr(self, 'CHILD'):
            Child = _OGA(self,'CHILD')
            if isinstance(Child, Tag_Block):
                Bytes_Total += Child.__sizeof__(Seen_Set)
            else:
                Seen_Set.add(id(Child))
                Bytes_Total += getsizeof(Child)
                
        Desc = _OGA(self,'DESC')
        if 'ORIG_DESC' in Desc and id(Desc) not in Seen_Set:
            Seen_Set.add(id(Desc))
            Bytes_Total += getsizeof(Desc)
            for key in Desc:
                item = Desc[key]
                if (not isinstance(key, int) and key != 'ORIG_DESC' and
                    id(item) not in Seen_Set):
                    Seen_Set.add(id(item))
                    Bytes_Total += getsizeof(item)
        
        for i in range(len(self)):
            item = _LGI(self, i)
            if not id(item) in Seen_Set:
                if isinstance(item, Tag_Block):
                    Bytes_Total += item.__sizeof__(Seen_Set)
                else:
                    Seen_Set.add(id(item))
                    Bytes_Total += getsizeof(item)
            
        return Bytes_Total


    def __getitem__(self, Index):
        '''enables getting attributes by providing
        the attribute name string as an index'''
        if isinstance(Index, str):
            return self.__getattr__(Index)
        
        return _LGI(self, Index)


    def __setitem__(self, Index, New_Value):
        '''enables setting attributes by providing
        the attribute name string as an index'''
        if isinstance(Index, int):
            #handle accessing negative indexes
            if Index < 0:
                Index += len(self)
            _LSI(self, Index, New_Value)

            '''if the object being placed in the Tag_Block
            has a 'PARENT' attribute, set this block to it'''
            if hasattr(New_Value, 'PARENT'):
                _OSA(New_Value, 'PARENT', self)
            
            if not _OGA(self,'DESC')['TYPE'].Is_Array:
                Type = _OGA(self,'DESC')[Index]['TYPE']
                if Type.Is_Var_Size and Type.Is_Data:
                    #try to set the size of the attribute
                    try:   self.Set_Size(None, Index)
                    except NotImplementedError: pass
                    except AttributeError: pass
        else:
            self.__setattr__(Index, New_Value)


    def __delitem__(self, Index):
        '''enables deleting attributes by providing
        the attribute name string as an index'''
        
        if isinstance(Index, int):
            #handle accessing negative indexes
            if Index < 0:
                Index += len(self)
            _LDI(self, Index)
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                self.Set_Size(1, None, '-')
            else:
                self.Del_Desc(Index)
                
                try:   self.Set_Size(0, Index)
                except NotImplementedError: pass
                except AttributeError: pass
                
        elif isinstance(Index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Old_Size = len(self)
                _LDI(self, Index)
                self.Set_Size(Old_Size-len(self), None, '-')
            else:
                start, stop, step = Index.indices(len(self))
                if start < stop: start, stop = stop, start
                if step > 0:     step = -step
                    
                for i in range(start-1, stop-1, step):
                    self.Del_Desc(i)
                    _LDI(self, i)
                    
                    try:   self.Set_Size(0, i)
                    except NotImplementedError: pass
                    except AttributeError: pass
        else:
            self.__delattr__(Index)


    def __getattr__(self, Name):
        '''docstring'''
        if Name in _OGA(self, "__slots__"):
            return _OGA(self, Name)
        else:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc['ATTR_MAP']:
                return self[Desc['ATTR_MAP'][Name]]
            elif Name in Desc:
                return Desc[Name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'"
                                     %(Desc.get('NAME','unnamed'),
                                       type(self), Name))


    def __setattr__(self, Name, New_Value):
        '''docstring'''
        if Name in _OGA(self, '__slots__'):
            _OSA(self, Name, New_Value)
        else:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc['ATTR_MAP']:
                self[Desc['ATTR_MAP'][Name]] = New_Value
            elif Name in Desc:
                if Name == 'CHILD':
                    raise AttributeError(("'%s' of type %s has no "+
                                          "slot for a CHILD.") %
                                         (Desc.get('NAME','unnamed'),
                                          type(self)))
                self.Set_Desc(Name, New_Value)
            else:
                raise AttributeError(("'%s' of type %s has no "+
                                      "attribute '%s'") %
                                     (Desc.get('NAME','unnamed'),
                                      type(self), Name))


    def __delattr__(self, Name):
        '''docstring'''
        if Name in _OGA(self, '__slots__'):
            _ODA(self, Name)
            if Name == 'CHILD':
                try:    self.Set_Size(0, 'CHILD')
                except NotImplementedError: pass
                except AttributeError: pass
        else:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc[ATTR_MAP]:
                del self[Desc['ATTR_MAP'][Name]]
                try:   self.Set_Size(Attr_Name=Name)
                except NotImplementedError: pass
                except AttributeError: pass
            elif Name in Desc:
                self.Del_Desc(Name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME','unnamed'),
                                      type(self), Name))

                
    def _validate_name(self, Name, Attr_Map={}, Attr_Index=0):
        '''Checks if "Name" is valid to use for an attrubte in this struct.
        Raises a NameError or TypeError if it isnt. Returns True if it is.
        Attr_Index must be an integer.'''
        assert(isinstance(Attr_Index, int))
        
        if Attr_Map.get(Name,Attr_Index+1) != Attr_Index:
            raise NameError(("'%s' already exists as an attribute in '%s'.\n"+
                           'Duplicate names are not allowed.')%(Name,_OGA(self,'DESC')['NAME']))
        elif not isinstance(Name, str):
            raise TypeError("Attribute names must be of type str, not %s" %
                            type(Name))
        elif Name == '' or Name is None:
            raise NameError("'' and None cannot be used as attribute names.")
        elif Name[0] not in Alpha_IDs:
            raise NameError("The first character of an attribute name must be "+
                            "either an alphabet character or an underscore.")
        elif Name.strip(Alpha_Numeric_IDs):
            #check all the characters to make sure they are valid identifiers
            raise NameError(("'%s' is an invalid identifier as it "+
                             "contains characters other than "+
                             "alphanumeric or underscores.") % Name)
        return True



    def _Bin_Size(self, Block, Sub_Struct=False):
        '''Does NOT protect against recursion'''
        Size = 0
        if isinstance(Block, Tag_Block):
            #get the size of this structure if it's not a substruct
            if _OGA(Block,'DESC')['TYPE'].Is_Struct and not Sub_Struct:
                Size = Block.Get_Size()
                Sub_Struct = True

            #loop for each of the attributes
            for i in range(len(Block)):
                Sub_Block = Block[i]
                if isinstance(Sub_Block, Tag_Block):
                    Size += Sub_Block._Bin_Size(Sub_Block, Sub_Struct)
                elif not Sub_Struct:
                    Size += Block.Get_Size(i)

            #add the size of the child
            if hasattr(Block, 'CHILD'):
                Child = _OGA(Block,'CHILD')
                if isinstance(Child, Tag_Block):
                    Size += Child._Bin_Size(Child)
                else:
                    Size += Block.Get_Size('CHILD')
            
        return Size

    
    @property
    def Bin_Size(self):
        '''Returns the size of this Tag_Block and all Tag_Blocks
        parented to it. This size isn't how much space it takes up
        in RAM, but how much it would take up if written to a buffer'''
        return self._Bin_Size(self)


    def append(self, New_Attr=None, New_Desc=None):
        '''Allows appending objects to this Tag_Block while taking
        care of all descriptor related details.
        Function may be called with no arguments if this block type is
        an Array. Doing so will append a fresh structure to the array
        (as defined by the Array's SUB_STRUCT descriptor value).'''

        #get the index we'll be appending into
        Index = len(self)
        #create a new, empty index
        _LApp(self, None)

        '''if this block is an array and "New_Attr" is None
        then it means to append a new block to the array'''
        if New_Attr is None and _OGA(self,'DESC')['TYPE'].Is_Array:
            Attr_Type = _OGA(self,'DESC')[SUB_STRUCT][TYPE]

            '''if the type of the default object is a type of Tag_Block
            then we can create one and just append it to the array'''
            if issubclass(Attr_Type.Py_Type, Tag_Block):
                Attr_Type.Reader(self, None, Index)

                self.Set_Size(1, None, '+')
                try:   New_Attr.PARENT = self
                except Exception: pass

                #finished, so return
                return

        #if the New_Attr has its own descriptor,
        #use that instead of any provided one
        try: New_Desc = New_Attr.DESC
        except Exception: pass
                
            
        if New_Desc is None and not _OGA(self,'DESC')['TYPE'].Is_Array:
            _LDI(self, Index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(New_Attr)) + "\nCannot append " +
                                 "without a descriptor for the new item.")
        
        '''try and insert the new descriptor
        and set the new attribute value,
        raise the last error if it fails
        and remove the new empty index'''
        try:
            _LSI(self, Index, New_Attr)
            if not _OGA(self,'DESC')['TYPE'].Is_Array:
                self.Ins_Desc(Index, New_Desc)
        except Exception:
            _LDI(self, Index)
            raise

        if _OGA(self,'DESC')['TYPE'].Is_Array:
            #increment the size of the array by 1
            self.Set_Size(1, None, '+')
        elif _OGA(self,'DESC')['TYPE'].Is_Struct:
            #increment the size of the struct
            #by the size of the new attribute
            self.Set_Size(self.Get_Size(Index), None, '+')

        #if the object being placed in the List_Block
        #has a 'PARENT' attribute, set this block to it
        try:   _OSA(New_Attr, 'PARENT', self)
        except Exception: pass

            

    def extend(self, New_Attrs):
        '''Allows extending this List_Block with new attributes.
        Provided argument must be a List_Block so that a descriptor
        can be found for all attributes, whether they carry it or
        the provided block does.
        Provided argument may also be an integer if this block type is an Array.
        Doing so will extend the array with that amount of fresh structures
        (as defined by the Array's SUB_STRUCT descriptor value)'''
        if isinstance(New_Attrs, List_Block):
            Desc = New_Attrs.DESC
            for i in range(Desc[ENTRIES]):
                self.append(New_Attrs[i], Desc[i])
        elif _OGA(self,'DESC')['TYPE'].Is_Array:
            if isinstance(New_Attrs, int):
                #if this block is an array and "New_Attr" is an int it means
                #that we are supposed to append this many of the SUB_STRUCT
                for i in range(New_Attrs):
                    self.append()
            else:
                Desc = New_Attrs.DESC
                for i in range(Desc[ENTRIES]):
                    self.append(New_Attrs[i], Desc[i])
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of List_Block, not %s" % type(New_Attrs))



    def insert(self, Index, New_Attr=None, New_Desc=None):
        '''Allows inserting objects into this List_Block while
        taking care of all descriptor related details.
        Function may be called with only "Index" if this block type is a Array.
        Doing so will insert a fresh structure to the array at "Index"
        (as defined by the Array's SUB_STRUCT descriptor value)'''

        #create a new, empty index
        _LIns(self, Index, None)

        '''if this block is an array and "New_Attr" is None
        then it means to append a new block to the array'''
        if _OGA(self,'DESC')['TYPE'].Is_Array:
            New_Desc = _OGA(self,'DESC')[SUB_STRUCT]
            Attr_Type = New_Desc[TYPE]

            '''if the type of the default object is a type of Tag_Block
            then we can create one and just append it to the array'''
            if New_Attr is None and issubclass(Attr_Type.Py_Type, Tag_Block):
                Attr_Type.Reader(self, None, Index)

                self.Set_Size(1, None, '+')
                try: New_Attr.PARENT = self
                except Exception: pass

                #finished, so return
                return

        #if the New_Attr has its own descriptor,
        #use that instead of any provided one
        try:   New_Desc = New_Attr.DESC
        except Exception: pass
            
        if New_Desc is None:
            _LDI(self, Index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(New_Attr)) + "\nCannot insert " +
                                 "without a descriptor for the new item.")
        if isinstance(Index, str):
            try:Index = _OGA(self,'DESC')[ATTR_MAP][Index]
            except Exception:
                _LDI(self, Index)
                raise AttributeError(("Cannot determine index for attribute "+
                                      "name '%s'. '%s' has no attribute '%s'")%
                                     (Index, _OGA(self,'DESC')[NAME], Index))

        '''try and insert the new descriptor
        and set the new attribute value,
        raise the last error if it fails'''
        try:
            _LSI(self, Index, New_Attr)
            if not _OGA(self,'DESC')['TYPE'].Is_Array:
                self.Ins_Desc(Index, New_Desc)
        except Exception:
            _LDI(self, Index)
            raise

        #increment the size of the array by 1
        if _OGA(self,'DESC')['TYPE'].Is_Array:
            self.Set_Size(1, None, '+')

        #if the object being placed in the List_Block
        #has a 'PARENT' attribute, set this block to it
        try:
            _OSA(New_Attr, 'PARENT', self)
        except Exception:
            pass


    def pop(self, Index=-1):
        '''Pops the attribute at 'Index' out of the List_Block
        and returns a tuple containing it and its descriptor.
        Works properly with CHILD blocks as well.'''
        
        if isinstance(Index, int):
            if Index < 0:
                Index += len(self)
            Attr = _LPop(self, Index)
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Desc = _OGA(self, "DESC")['SUB_STRUCT']
                self.Set_Size(1, None, '-')
            else:
                Desc = self.Get_Desc(Index)
                self.Del_Desc(Index)
        else:
            Desc = _OGA(self, "DESC")
            
            if Index in Desc[ATTR_MAP]:
                Attr = _LPop(self, Desc[ATTR_MAP][Index])
                Desc = self.Get_Desc(Index)
                self.Del_Desc(Index)
            elif Index == 'CHILD' and hasattr(self, 'CHILD'):
                Attr = _OGA(self, 'CHILD')
                Desc = self.Get_Desc('CHILD')
                del self.CHILD
            else:
                if NAME in Desc:
                    raise AttributeError("'%s' of type %s has no attribute '%s'"
                                         % (Desc[NAME], type(self), Index))
                else:
                    raise AttributeError("'%s' has no attribute '%s'"
                                         %(type(self), Index))
            
        return(Attr, Desc)


    def Get_Tag(self):
        '''This function upward navigates the Tag_Block
        structure it is a part of until it finds a block
        with the attribute "Tag_Data", and returns it.

        Raises LookupError if the Tag is not found'''
        Tag = self
        try:
            while True:
                Tag = Tag.PARENT
                
                '''check if the object is a Tag_Obj'''
                if isinstance(Tag, Tag_Obj.Tag_Obj):
                    return Tag
        except AttributeError:
            pass
            
        raise LookupError("Could not locate parent Tag object.")
    

    def Get_Neighbor(self, Path, Block=None, Array_Map=None):
        """Given a path to follow, this function will
        navigate neighboring blocks until the path is
        exhausted and return the last block."""
        if not isinstance(Path, str):
            raise TypeError("'Path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(Path)) )
        
        Path_Fields = Path.split('.')
        
        if Array_Map is None:
            Array_Map = {}

        #if a starting block wasn't provided, or it was
        #and it's not a Tag_Block with a parent reference
        #we need to set it to something we can navigate from
        if not hasattr(Block, 'PARENT'):
            try:
                if Block.TYPE.Is_Array:
                    Array_Map[Block.NAME] = self.index(Block)
            except Exception:
                pass

            if Path_Fields and Path_Fields[0] == "":
                '''If the first direction in the path is
                to go to the parent, set Block to self
                (because Block may not be navigable from)
                and delete the first path direction'''
                Block = self
                del Path_Fields[0]
            else:
                '''if the first path isn't "Go to parent",
                then it means it's not a relative path.
                Thus the path starts at the Tag_Data root'''
                Block = self.Get_Tag().Tag_Data
        try:
                
            for field in Path_Fields:
                if field == '':
                    New_Block = Block.PARENT

                    #if the upper blocks type is an array then
                    #we need to store the index we entered into
                    if New_Block.TYPE.Is_Array:
                        try:
                            Array_Map[Block.NAME] = New_Block.index(Block)
                        except Exception:
                            pass
                else:
                    New_Block = Block.__getattr__(field)

                    #if the upper blocks type is an array then
                    #we need to store the index we entered into
                    if Block.TYPE.Is_Array:
                        try: Array_Map[New_Block.NAME] = Block.index(New_Block)
                        except Exception: pass

                #replace the block to the new
                #block to continue the cycle
                Block = New_Block
        except Exception:
            try:    self_name  = _OGA(self,'DESC')['NAME']
            except Exception: self_name  = type(self)
            try:    block_name = Block.NAME
            except Exception: block_name = type(Block)
            try:    field
            except Exception: field = ''
            
            raise AttributeError(("Path string to neighboring block is " +
                                  "invalid.\nStarting block was '%s'. "+
                                  "Couldnt find '%s' in '%s'.\n" +
                                  "Full path was '%s'") %
                                 (self_name, field, block_name, Path))
        return Block


    def Get_Size(self, Attr_Name=None):
        '''docstring'''

        if isinstance(Attr_Name, int):
            Block = self[Attr_Name]
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Desc = _OGA(self,'DESC')['SUB_STRUCT']
            else:
                Desc = _OGA(self,'DESC')[Attr_Name]
        elif isinstance(Attr_Name, str):
            Block = self.__getattr__(Attr_Name)
            try:
                Desc = _OGA(self,'DESC')['TYPE']
                Desc = Desc[Desc['ATTR_MAP'][Attr_Name]]
            except Exception:
                Desc = _OGA(self,'DESC')[Attr_Name]
        else:
            Block = self
            Desc = _OGA(self,'DESC')
            

        #determine how to get the size
        if SIZE in Desc:
            Size = Desc[SIZE]
            
            if isinstance(Size, int):
                return Size
            elif isinstance(Size, str):
                '''get the pointed to Size data by traversing the tag
                structure along the path specified by the string'''
                return self.Get_Neighbor(Size, Block)
            elif hasattr(Size, "__call__"):
                '''find the pointed to Size data by
                calling the provided function'''
                try:
                    Parent = Block.PARENT
                except AttributeError:
                    Parent = self
                    
                return Size(Attr_Name=Attr_Name, Parent=Parent, Block=Block)
            else:
                Block_Name = _OGA(self,'DESC')['NAME']
                if isinstance(Attr_Name, (int,str)):
                    Block_Name = Attr_Name
                raise TypeError(("Size specified in '%s' is not a valid type. "+
                                 "Expected int, str, or function. Got %s.") %
                                (Block_Name, type(Size)) )
        #use the size calculation routine of the Field_Type
        return Desc[TYPE].Size_Calc(Block)



    def Get_Meta(self, Meta_Name, Attr_Name=None):
        '''docstring'''

        if isinstance(Attr_Name, int):
            Block = self[Attr_Name]
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Desc = _OGA(self,'DESC')[SUB_STRUCT]
            else:
                Desc = _OGA(self,'DESC')[Attr_Name]
        elif isinstance(Attr_Name, str):
            Block = self.__getattr__(Attr_Name)
            try:
                Desc = _OGA(self,'DESC')['TYPE']
                Desc = Desc[Desc[ATTR_MAP][Attr_Name]]
            except Exception:
                Desc = _OGA(self,'DESC')[Attr_Name]
        else:
            Block = self
            Desc = _OGA(self,'DESC')

            
        if Meta_Name in Desc:
            Meta = Desc[Meta_Name]
            
            if isinstance(Meta, int):
                return Meta
            elif isinstance(Meta, str):
                '''get the pointed to meta data by traversing the tag
                structure along the path specified by the string'''
                return self.Get_Neighbor(Meta, Block)
            elif hasattr(Meta, "__call__"):
                '''find the pointed to meta data by
                calling the provided function'''
                if hasattr(Block, PARENT):
                    Parent = Block.PARENT
                else:
                    Parent = self
                    
                return Meta(Attr_Name=Attr_Name,
                            Parent=Parent, Block=Block)
            else:
                raise LookupError("Couldnt locate meta info")
        else:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Name, (int,str)):
                Block_Name = Attr_Name
            raise AttributeError("'%s' does not exist in '%s'."
                                 % (Meta_Name,Block_Name))

        
    def Set_Neighbor(self, Path, New_Value, Block=None,
                     Operator=None, Array_Map=None):
        """Given a path to follow, this function
        will navigate neighboring blocks until the
        path is exhausted and set the last block."""
        if not isinstance(Path, str):
            raise TypeError("'Path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(Path)) )
        
        Path_Fields = Path.split('.')

        if Array_Map is None:
            Array_Map = {}

        #if a starting block wasn't provided, or it was
        #and it's not a Tag_Block with a parent reference
        #we need to set it to something we can navigate from
        if not hasattr(Block, 'PARENT'):
            try:
                if Block.TYPE.Is_Array:
                    Array_Map[Block.NAME] = self.index(Block)
            except Exception:
                pass

            if Path_Fields and Path_Fields[0] == "":
                '''If the first direction in the path is
                to go to the parent, set Block to self
                (because Block may not be navigable from)
                and delete the first path direction'''
                Block = self
                del Path_Fields[0]
            else:
                '''if the first path isn't "Go to parent",
                then it means it's not a relative path.
                Thus the path starts at the Tag_Data root'''
                Block = self.Get_Tag().Tag_Data
        try:
            
            for field in Path_Fields[:-1]:
                if field == '':
                    New_Block = Block.PARENT

                    #if the upper blocks type is an array then
                    #we need to store the index we entered into
                    if New_Block.TYPE.Is_Array:
                        try:
                            Array_Map[Block.NAME] = New_Block.index(Block)
                        except Exception:
                            pass
                else:
                    New_Block = Block.__getattr__(field)

                    #if the upper blocks type is an array then
                    #we need to store the index we entered into
                    if Block.TYPE.Is_Array:
                        try: Array_Map[New_Block.NAME] = Block.index(New_Block)
                        except Exception: pass

                #replace the block to the new
                #block to continue the cycle
                Block = New_Block

        except Exception:
            try:    self_name  = _OGA(self,'DESC')['NAME']
            except Exception: self_name  = type(self)
            try:    block_name = Block.NAME
            except Exception: block_name = type(Block)
            try:    field
            except Exception: field = ''
            
            raise AttributeError(("Path string to neighboring block is " +
                                  "invalid.\nStarting block was '%s'. "+
                                  "Couldnt find '%s' in '%s'.\n" +
                                  "Full path was '%s'") %
                                 (self_name, field, block_name, Path))
        if Operator is None:
            pass
        elif Operator == '+':
            New_Value = Block.__getattr__(Path_Fields[-1]) + New_Value
        elif Operator == '-':
            New_Value = Block.__getattr__(Path_Fields[-1]) - New_Value
        elif Operator == '*':
            New_Value = Block.__getattr__(Path_Fields[-1]) * New_Value
        elif Operator == '/':
            New_Value = Block.__getattr__(Path_Fields[-1]) // New_Value
        else:
            raise TypeError(("Unknown operator type '%s' " +
                             "for setting neighbor.") % Operator)
        
        Block.__setattr__(Path_Fields[-1], New_Value)
        
        return Block


    def Set_Size(self, New_Value=None, Attr_Name=None, Operator=None):
        '''returns the size of self[Attr_Name] or of self if
        Attr_Name == None. Size units are dependent on the data type
        being measured. Structs and variables will be measured in bytes
        and containers/struct_arrays will be measured in entries.
        Checks the data type and descriptor for the size. The descriptor
        may specify the size in terms of already parsed fields.'''
        
        if isinstance(Attr_Name, int):
            Block = self[Attr_Name]
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Size = _OGA(self,'DESC')[SUB_STRUCT].get(SIZE)
            else:
                Size = _OGA(self,'DESC')[Attr_Name].get(SIZE)
            Type = self.Get_Desc(TYPE, Attr_Name)
        elif isinstance(Attr_Name, str):
            Block = self.__getattr__(Attr_Name)

            ErrorNo = 0
            #try to get the size directly from the block
            try:
                Desc = Block.DESC
                Size = Desc[SIZE]
            except Exception:
                #if that fails, try to get it from the descriptor of the parent
                try:
                    Desc = _OGA(self,'DESC')['TYPE']
                    Desc = Desc[Desc[ATTR_MAP][Attr_Name]]
                except Exception:
                    Desc = _OGA(self,'DESC')[Attr_Name]

                try: Size = Desc[SIZE]
                except Exception:
                    #its parent cant tell us the size, raise this error
                    ErrorNo = 1
                    if TYPE in Desc and not Desc['TYPE'].Is_Var_Size:
                        #the size is not variable so it cant be set
                        #without changing the type. raise this error
                        ErrorNo = 2
            
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Name, (int,str)):
                Block_Name = Attr_Name
            if ErrorNo == 1:
                raise AttributeError(("Could not determine size for "+
                                      "attribute '%s' in block '%s'.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME']))
            elif ErrorNo == 2:
                raise AttributeError(("Can not set size for attribute '%s' "+
                                      "in block '%s'.\n'%s' has a fixed size "+
                                      "of '%s'.\nTo change the size of '%s' "+
                                      "you must change its data type.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME'], Desc['TYPE'],
                                      Desc['TYPE'].Size, Block_Name))
            Type = Desc[TYPE]
        else:
            Block = self
            Size = _OGA(self,'DESC').get('SIZE')
            Type = _OGA(self,'DESC')['TYPE']

        #raise exception if the Size is None
        if Size is None:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Name, (int,str)):
                Block_Name = Attr_Name
            raise AttributeError("'SIZE' does not exist in '%s'." % Block_Name)

        #if a new size wasnt provided then it needs to be calculated
        if New_Value is None:
            Operator = None
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
        
            New_Size = Type.Size_Calc(Parent=Parent, Block=Block,
                                      Attr_Name=Attr_Name)
        else:
            New_Size = New_Value


        if isinstance(Size, int):
            '''Because literal descriptor sizes are supposed to be static
            (unless you're changing the structure), we don't change the size
            if the new size is less than the current one. This has the added
            benefit of not having to create a new unique descriptor, thus saving
            RAM. This can be bypassed by explicitely providing the new size.'''
            if New_Value is None and New_Size <= Size:
                return
            
            if Operator is None:
                self.Set_Desc(SIZE, New_Size, Attr_Name)
            elif Operator == '+':
                self.Set_Desc(SIZE, Size+New_Size, Attr_Name)
            elif Operator == '-':
                self.Set_Desc(SIZE, Size-New_Size, Attr_Name)
            elif Operator == '*':
                self.Set_Desc(SIZE, Size*New_Size, Attr_Name)
            elif Operator == '/':
                self.Set_Desc(SIZE, Size//New_Size, Attr_Name)
            else:
                raise TypeError(("Unknown operator type '%s' " +
                                 "for setting 'Size'.") % Operator)
        elif isinstance(Size, str):
            '''set size by traversing the tag structure
            along the path specified by the string'''
            self.Set_Neighbor(Size, New_Size, Block, Operator)
        elif hasattr(Size, "__call__"):
            '''set size by calling the provided function'''
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
            
            Size(Attr_Name=Attr_Name, New_Value=New_Size,
                 Operator=Operator, Parent=Parent, Block=Block)
        else:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Name, (int,str)):
                Block_Name = Attr_Name
            
            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (Block_Name, type(Size)) +
                            "Cannot determine how to set the size." )


    def Set_Meta(self, Meta_Name, New_Value=None,
                 Attr_Name=None, Operator=None):
        '''docstring'''
        if isinstance(Attr_Name, int):
            Block = self[Attr_Name]
            Block_Name = Attr_Name
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                Desc = _OGA(self,'DESC')['SUB_STRUCT']
            else:
                Desc = _OGA(self,'DESC')[Attr_Name]
        elif isinstance(Attr_Name, str):
            Block = self.__getattr__(Attr_Name)
            Block_Name = Attr_Name
            try:
                Desc = _OGA(self,'DESC')['TYPE']
                Desc = Desc[Desc['ATTR_MAP'][Attr_Name]]
            except Exception:
                Desc = _OGA(self,'DESC')[Attr_Name]
        else:
            Block = self
            Block_Name = _OGA(self,'DESC')['NAME']
            Desc = _OGA(self,'DESC')


        Meta_Value = Desc.get(Meta_Name)
        
        #raise exception if the Meta_Value is None
        if Meta_Value is None and Meta_Name not in Desc:
            raise AttributeError("'%s' does not exist in '%s'."
                                 % (Meta_Name,Block_Name))
        elif isinstance(Meta_Value, int):
            if Operator is None:
                self.Set_Desc(Meta_Name, New_Value, Attr_Name)
            elif Operator == '+':
                self.Set_Desc(Meta_Name, Meta_Value+New_Value, Attr_Name)
            elif Operator == '-':
                self.Set_Desc(Meta_Name, Meta_Value-New_Value, Attr_Name)
            elif Operator == '*':
                self.Set_Desc(Meta_Name, Meta_Value*New_Value, Attr_Name)
            elif Operator == '/':
                self.Set_Desc(Meta_Name, Meta_Value//New_Value, Attr_Name)
            else:
                raise TypeError(("Unknown operator type '%s' for " +
                                 "setting '%s'.") % (Operator, Meta_Name))
            self.Set_Desc(Meta_Name, New_Value, Attr_Name)
        elif isinstance(Meta_Value, str):
            '''set meta by traversing the tag structure
            along the path specified by the string'''
            self.Set_Neighbor(Meta_Value, New_Value, Block, Operator)
        elif hasattr(Meta_Value, "__call__"):
            '''set the meta by calling the provided function'''
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
            
            Meta_Value(Attr_Name=Attr_Name, New_Value=New_Value,
                       Operator=Operator, Parent=Parent, Block=Block)
        else:
            raise TypeError(("Meta specified in '%s' is not a valid type." +
                            "Expected int, str, or function. Got %s.\n") %
                            (Block_Name, type(Meta_Value)) +
                            "Cannot determine how to set the meta data." )


    def Get_Desc(self, Desc_Key, Attr_Name=None):
        '''Returns the value in the object's descriptor
        under the key "Desc_Key". If Attr_Name is not None,
        the descriptor being searched for "Desc_Key" will
        instead be the attribute "Attr_Name".'''
        Desc = _OGA(self, "DESC")

        '''if we are getting something in the descriptor
        of one of this List_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            if isinstance(Attr_Name, int) or Attr_Name in Desc:
                Desc = Desc[Attr_Name]
            else:
                try:
                    try:
                        Desc = Desc[Desc['ATTR_MAP'][Attr_Name]]
                    except Exception:
                        Desc = Desc[Attr_Name]
                except Exception:
                    raise KeyError(("Could not locate '%s' in the descriptor "+
                                    "of '%s'.") % (Attr_Name, _OGA(self,'DESC')['NAME']))

        '''Try to return the descriptor value under the key "Desc_Key" '''
        if Desc_Key in Desc:
            return Desc[Desc_Key]
        
        try:
            return Desc[Desc[ATTR_MAP][Desc_Key]]
        except KeyError:
            if Attr_Name is not None:
                raise KeyError(("Could not locate '%s' in the sub-descriptor "+
                                "'%s' in the descriptor of '%s'") %
                               (Desc_Key, Attr_Name, _OGA(self,'DESC')['NAME']))
            else:
                raise KeyError(("Could not locate '%s' in the descriptor " +
                                "of '%s'.") % (Desc_Key, _OGA(self,'DESC')['NAME']))


    def Del_Desc(self, Desc_Key, Attr_Name=None):
        '''Enables clean deletion of attributes from this
        List_Block's descriptor. Takes care of decrementing
        ENTRIES, shifting indexes of attributes, removal from
        ATTR_MAP, and making sure the descriptor is unique.
        DOES NOT shift offsets or change struct size.
        That is something the user must do because any way
        to handle that isn't going to work for everyone.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this List_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[ATTR_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc[ATTR_MAP][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if ORIG_DESC not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
            
        if isinstance(Desc_Key, int):
            #"Desc_Key" must be a string for the
            #below routine to work, so change it
            Desc_Key = Desc[Desc_Key][NAME]
        
        '''Check if the descriptor needs to be made unique'''
        if not Desc.get(ORIG_DESC):
            Desc = self.Make_Unique(Desc)
            
        '''if we are deleting a descriptor based attribute'''
        if ATTR_MAP in Desc and Desc_Key in Desc[ATTR_MAP]:
            Attr_Map = Desc[ATTR_MAP]
            Attr_Index = Attr_Map[Desc_Key]

            #if there is an offset mapping to set,
            #need to get a local reference to it
            try:
                Attr_Offsets = Desc['ATTR_OFFS']
            except Exception:
                Attr_Offsets = None
            
            #delete the name of the attribute from ATTR_MAP
            del Attr_Map[Desc_Key]
            #delete the attribute
            del Desc[Attr_Index]
            #decrement the number of entries
            Desc[ENTRIES] -= 1
            
            '''if an attribute is being deleted,
            then ATTR_MAP needs to be shifted down
            and the key of each attribute needs to be
            shifted down in the descriptor as well'''

            Last_Entry = Desc[ENTRIES]

            #shift all the indexes down by 1
            for i in range(Attr_Index, Last_Entry):
                Desc[i] = Desc[i+1]
                Attr_Map[Desc[i+1][NAME]] = i
                
            if Attr_Offsets is not None: del Attr_Offsets[Desc_Key]

            #now that all the entries have been moved down,
            #delete the topmost entry since it's a copy
            if Attr_Index < Last_Entry:
                del Desc[Last_Entry]
        else:
            '''we are trying to delete something other than an
            attribute. This isn't safe to do, so raise an error.'''
            raise Exception(("It is unsafe to delete '%s' from " +
                            "Tag Object descriptor.") % Desc_Key)

        #replace the old descriptor with the new one
        if Attr_Name is not None:
            Self_Desc[Attr_Name] = Desc
            _OSA(self, "DESC", Self_Desc)
        else:
            _OSA(self, "DESC", Desc)


    def Set_Desc(self, Desc_Key, New_Value, Attr_Name=None):
        '''Enables cleanly changing the attributes in this
        List_Block's descriptor or adding non-attributes.
        Takes care of adding to ATTR_MAP and other stuff.
        DOES NOT shift offsets or change struct size.
        That is something the user must do because any way
        to handle that isn't going to work for everyone.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this List_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[ATTR_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc[ATTR_MAP][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if ORIG_DESC not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
        
        if isinstance(Desc_Key, int):
            #"Desc_Key" must be a string for the
            #below routine to work, so change it
            Desc_Key = Desc[Desc_Key][NAME]

        Desc_Name = Desc_Key
        if ATTR_MAP in Desc and Desc_Name in Desc[ATTR_MAP]:
            Desc_Name = Desc[ATTR_MAP][Desc_Name]

        '''Check if the descriptor needs to be made unique'''
        if not Desc.get(ORIG_DESC) and id(Desc[Desc_Name]) != id(New_Value):
            Desc = self.Make_Unique(Desc)

        if ATTR_MAP in Desc and Desc_Key in Desc[ATTR_MAP]:  
            '''we are setting a descriptor based attribute.
            We might be changing what it's named'''
            
            #if there is an offset mapping to set,
            #need to get a local reference to it
            try:
                Attr_Offsets = Desc['ATTR_OFFS']
            except Exception:
                Attr_Offsets = None
            
            Attr_Map = Desc[ATTR_MAP]
            Attr_Index = Attr_Map[Desc_Key]
                
            '''if the names are different, change the
            ATTR_MAP and ATTR_OFFS mappings'''
            if NAME in New_Value and New_Value[NAME] != Desc_Key:
                New_Name = New_Value[NAME]
                '''Run a series of checks to make
                sure the name in New_Value is valid'''
                self._validate_name(New_Name, Attr_Map, Attr_Index)
            
                #remove the old name from the Attr_Map
                del Attr_Map[Desc_Key]
                #set the name of the attribute in ATTR_MAP
                Attr_Map[New_Name] = Attr_Index
                
                if Attr_Offsets and Desc_Key in Attr_Offsets:
                    Attr_Offsets[New_Name] = Attr_Offsets[Desc_Key]
                    del Attr_Offsets[Desc_Key]
            else:
                #If the New_Value doesn't have a name,
                #give it the old descriptor's name
                New_Value[NAME] = Desc_Key
            
            #set the attribute to the new New_Value
            Desc[Attr_Index] = New_Value

        else:
            '''we are setting something other than an attribute'''
            if Desc_Key == NAME and New_Value != Desc[NAME]:
                '''there are some rules for setting the name '''
                
                Attr_Offsets = None
                Attr_Map = None
                
                '''make sure to change the name in the
                parent's Attr_Map mapping as well'''
                if Attr_Name is not None:
                    Attr_Map = deepcopy(Self_Desc[ATTR_MAP])
                    try:    Attr_Offsets = deepcopy(Self_Desc['ATTR_OFFS'])
                    except Exception: pass
                else:
                    try:    Attr_Map = deepcopy(self.PARENT.ATTR_MAP)
                    except Exception: pass
                    try:    Attr_Offsets = deepcopy(self.PARENT.ATTR_OFFS)
                    except Exception: pass
                    

                '''if the offsets mapping exists,
                change the name that it's mapped to'''
                if Attr_Offsets:
                    Attr_Offsets[New_Value] = Attr_Offsets[Desc[NAME]]
                    del Attr_Offsets[Desc[NAME]]

                '''if the parent name mapping exists,
                change the name that it's mapped to'''
                if Attr_Map is not None:
                    Attr_Index = Attr_Map[Desc[NAME]]
                    '''Run a series of checks to make
                    sure the name in New_Value is valid'''
                    self._validate_name(New_Value, Attr_Map, Attr_Index)
                
                    #set the index of the new name to the index of the old name
                    Attr_Map[New_Value] = Attr_Map[Desc[NAME]]
                    #delete the old name
                    del Attr_Map[Desc[NAME]]


                ''''Now that we've gotten to here,
                it's safe to commit the changes'''
                if Attr_Offsets:
                    #set the parent's ATTR_OFFS to the newly configured one
                    if Attr_Name is not None:
                        Self_Desc['ATTR_OFFS'] = Attr_Offsets
                    else:
                        self.PARENT.Set_Desc('ATTR_OFFS', Attr_Offsets)

                if Attr_Map is not None:
                    #set the parent's ATTR_MAP to the newly configured one
                    if Attr_Name is not None:
                        Self_Desc[ATTR_MAP] = Attr_Map
                    else:
                        self.PARENT.Set_Desc(ATTR_MAP, Attr_Map)
                        
                else:
                    self._validate_name(New_Value)
                
            Desc[Desc_Key] = New_Value

        #replace the old descriptor with the new one
        if Attr_Name is not None:
            Self_Desc[Attr_Name] = Desc
            _OSA(self, "DESC", Self_Desc)
        else:
            _OSA(self, "DESC", Desc)



    def Ins_Desc(self, Desc_Key, New_Value, Attr_Name=None):
        '''Enables clean insertion of attributes into this
        List_Block's descriptor. Takes care of incrementing
        ENTRIES, adding to ATTR_MAP, and shifting indexes.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this List_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[ATTR_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc[ATTR_MAP][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if ORIG_DESC not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
            
        '''Check if the descriptor needs to be made unique'''
        if not Desc.get(ORIG_DESC):
            Desc = self.Make_Unique(Desc)

        #if Desc_Key is an already existing attribute, we are
        #inserting the new descriptor where it currently is.
        #Thus, we need to get what index the attribute is in.
        if ATTR_MAP in Desc and Desc_Key in Desc[ATTR_MAP]:
            Desc_Key = Desc[ATTR_MAP][Desc_Key]

            
        if isinstance(Desc_Key, int):
            '''we are adding an attribute'''
            Attr_Map = Desc[ATTR_MAP]
            Attr_Index = Desc_Key
            Desc_Key = New_Value[NAME]
            
            #before any changes are committed, validate the
            #name to make sure we aren't adding a duplicate
            self._validate_name(Desc_Key, Attr_Map)

            #if there is an offset mapping to set,
            #need to get a local reference to it
            try:
                Attr_Offsets = Desc['ATTR_OFFS']
            except Exception:
                Attr_Offsets = None
            
            '''if an attribute is being added, then
            ATTR_MAP needs to be shifted up and the
            key of each attribute needs to be
            shifted up in the descriptor as well'''
            #shift all the indexes up by 1 in reverse
            for i in range(Desc[ENTRIES], Attr_Index, -1):
                Desc[i] = Desc[i-1]
                Attr_Map[Desc[i-1][NAME]] = i
            
            #add name of the attribute to ATTR_MAP
            Attr_Map[Desc_Key] = Attr_Index
            #add the attribute
            Desc[Attr_Index] = New_Value
            #increment the number of entries
            Desc[ENTRIES] += 1
                    
            if Attr_Offsets is not None:
                try:
                    '''set the offset of the new attribute to
                    the offset of the old one plus its size'''
                    Offset = (Attr_Offsets[Desc[Attr_Index-1][NAME]] +
                              self.Get_Size(Attr_Index-1))
                except Exception:
                    '''If we fail, it means this attribute is the
                    first in the structure, so its offset is 0'''
                    Offset = 0

                '''add the offset of the attribute
                to the offsets map by name and index'''
                Attr_Offsets[Desc_Key] = Offset

        else:
            if isinstance(New_Value, dict):
                raise Exception(("Supplied value was not a valid attribute "+
                                 "descriptor.\nThese are the supplied "+
                                 "descriptor's keys. %s") % New_Value.keys())
            else:
                raise Exception(("Supplied value was not a valid attribute "+
                                 "descriptor.\nThis is what was supplied. %s")%
                                New_Value)

        #replace the old descriptor with the new one
        if Attr_Name is not None:
            Self_Desc[Attr_Name] = Desc
            _OSA(self, "DESC", Self_Desc)
        else:
            _OSA(self, "DESC", Desc)


    def Res_Desc(self, Name=None):
        '''Restores the descriptor of the attribute "Name"
        WITHIN this List_Block's descriptor to its backed up
        original. This is done this way in case the attribute
        doesn't have a descriptor, like strings and integers.
        If Name is None, restores this List_Blocks descriptor.'''
        Desc = _OGA(self, "DESC")
        Attr_Map = Desc[ATTR_MAP]
        
        #if we need to convert Name from an int into a string
        if isinstance(Name, int):
            Name = Attr_Map[NAME]

        if Name is not None:
            '''restoring an attributes descriptor'''
            if Name in Attr_Map:
                Attr_Index = Attr_Map[Name]
                Attr_Desc = Desc[Attr_Index]
                
                if ORIG_DESC in Attr_Desc:
                    #restore the descriptor of this List_Block's attribute
                    Desc[Attr_Index] = Attr_Desc[ORIG_DESC]
            else:
                raise AttributeError(("'%s' is not an attribute in the "+
                                      "List_Block '%s'. Cannot restore " +
                                      "descriptor.") % (Name, _OGA(self,'DESC')['NAME']))
        elif Desc.get(ORIG_DESC):
            '''restore the descriptor of this List_Block'''
            _OSA(self, "DESC", Desc[ORIG_DESC])


    def Make_Unique(self, Desc=None):
        '''Returns a unique copy of the provided descriptor. The
        copy is made unique from the provided one by replacing it
        with a semi-shallow copy and adding a reference to the
        original descriptor under the key "ORIG_DESC". The copy
        is semi-shallow in that the attributes are shallow, but
        entries like ATTR_MAP, ATTR_OFFS, and NAME are deep.
        
        If you use the new, unique, descriptor as this object's
        descriptor, this object will end up using more ram.'''

        if Desc is None:
            Desc = _OGA(self, "DESC")
        
        #make a new descriptor with a reference to the original
        New_Desc = {ORIG_DESC:Desc}
        
        #semi shallow copy all the keys in the descriptor
        for key in Desc:
            if (isinstance(key, int) or
                key in ('CHILD', SUB_STRUCT) ):
                '''if the entry is an attribute then make a reference to it'''
                New_Desc[key] = Desc[key]
            else:
                '''if the entry IS NOT an attribute then full copy it'''
                New_Desc[key] = deepcopy(Desc[key])

        return New_Desc
    

    def Set_Pointers(self, Offset=0):
        '''Scans through this block and sets the pointer of
        each pointer based block in a way that ensures that,
        when written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other block.

        This function is a copy of the Tag_Obj.Set_Pointers_Loop().
        This is ONLY to be called by a List_Block when it is writing
        itself so the pointers can be set as though this is the root.'''
        
        #Keep a set of all seen block IDs to prevent infinite recursion.
        Seen = set()
        PB_Blocks = []

        '''Loop over all the blocks in self and log all blocks that use
        pointers to a list. Any pointer based blocks will NOT be entered.
        
        The size of all non-pointer blocks will be calculated and used
        as the starting offset pointer based blocks.'''
        Offset = self.Set_Pointers_Loop(Offset, Seen, PB_Blocks)

        #Repeat this until there are no longer any pointer
        #based blocks for which to calculate pointers.
        while PB_Blocks:
            New_PB_Blocks = []
            
            '''Iterate over the list of pointer based blocks and set their
            pointers while incrementing the offset by the size of each block.
            
            While doing this, build a new list of all the pointer based
            blocks in all of the blocks currently being iterated over.'''
            for Block in PB_Blocks:
                Attr_Index = Block.get('Attr_Index')
                Block = Block.get('Block')
                
                if Attr_Index is None:
                    Block_Desc = Block.DESC
                else:
                    Block_Desc = Block.Get_Desc(Attr_Index)

                #In binary structs, usually when a block doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if Block.Get_Size(Attr_Index) > 0:
                    Block.Set_Meta('POINTER', Offset, Attr_Index)
                else:
                    Block.Set_Meta('POINTER', 0, Attr_Index)

                Offset = Block.Set_Pointers_Loop(Offset, Seen,
                                            New_PB_Blocks, Root=True)
            #restart the loop using the next level of pointer based blocks
            PB_Blocks = New_PB_Blocks


    def Set_Pointers_Loop(self, Offset=0, Seen=None, Pointed_Blocks=None,
                          Sub_Struct=False, Root=False, Attr_Index=None):
        '''docstring'''        
        if Seen is None:
            Seen = set()
            
        if Attr_Index is None:
            Desc = _OGA(self,'DESC')
            Block = self
        else:
            Desc = self.Get_Desc(Attr_Index)
            Block = self.__getattr__(Attr_Index)
            
        if 'POINTER' in Desc:
            if isinstance(Desc['POINTER'], int) and Desc.get(CARRY_OFF):
                Offset = Desc['POINTER']
            elif not Root:
                Pointed_Blocks.append({'Block':self, 'Attr_Index':Attr_Index})
                return Offset

        if id(Block) in Seen:
            return Offset
        
        Seen.add(id(Block))
                    
        if Desc.get('ALIGN'):
            Align = Desc['ALIGN']
            Offset += (Align-(Offset%Align))%Align

        #if we are setting the pointer of something that
        #isnt a List_Block then do it here and then return
        if Attr_Index is not None:
            return Offset + self.Get_Size(Attr_Index)
            
        #increment the offset by the size of
        #this struct if it isn't a substruct
        if not Sub_Struct and Desc[TYPE].Is_Struct:
            Offset += self.Get_Size()
            Sub_Struct = True
            
        if hasattr(self, 'CHILD'):
            Indexes = list(range(len(self)))
            Indexes.append('CHILD')
        else:
            Indexes = range(len(self))

        for i in Indexes:
            Block = self[i]
            if isinstance(Block, Tag_Block):
                Offset = Block.Set_Pointers_Loop(Offset, Seen, Pointed_Blocks,
                                          (Sub_Struct and Block.TYPE.Is_Struct))
            elif id(Block) not in Seen:
                if _OGA(self,'DESC')['TYPE'].Is_Array:
                    Block_Desc = Desc[SUB_STRUCT]
                else:
                    Block_Desc = Desc[i]
        
                if 'POINTER' in Block_Desc:
                    if not isinstance(Block_Desc.get('POINTER'), int):
                        #if the block has a variable pointer, add it to the
                        #list and break early so its id doesnt get added
                        Pointed_Blocks.append({'Block':self,'Attr_Index':i})
                        continue
                    elif Block_Desc.get(CARRY_OFF):
                        Offset = Block_Desc['POINTER']
                elif Block_Desc.get('ALIGN'):
                    Align = Block_Desc['ALIGN']
                    Offset += (Align-(Offset%Align))%Align
                Offset += self.Get_Size(i)
                Seen.add(id(Block))
                
        return Offset



    def Read(self, Init_Block=None, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An Init_Block
        can be provided with which to initialize the values of the block.'''

        #if an Init_Block was provided, make sure it can be used
        if (Init_Block is not None and
            not (hasattr(Init_Block, '__iter__') and
                 hasattr(Init_Block, '__len__'))):
            raise TypeError("Init_Block must be an iterable with a length.")

        Init_Attrs = kwargs.get('Init_Attrs',True)
        Attr_Name  = kwargs.get('Attr_Name', None)
        Filepath   = kwargs.get('Filepath',  None)
        Raw_Data   = kwargs.get('Raw_Data',  None)

        #figure out what the List_Block is being built from
        if Filepath is not None:
            if Raw_Data is not None:
                raise TypeError("Provide either Raw_Data " +
                                "or a Filepath, but not both.") 

            '''try to open the tag's path as the raw tag data'''
            try:
                with open(Filepath, 'r+b') as Tag_File:
                    Raw_Data = mmap(Tag_File.fileno(), 0)
            except Exception:
                raise IOError('Input filepath for reading List_Block ' +
                              'from was invalid or the file could ' +
                              'not be accessed.\n    ' + Filepath)
            
        if (Raw_Data is not None and
            not(hasattr(Raw_Data, 'read') or hasattr(Raw_Data, 'seek'))):
            raise TypeError('Cannot build a List_Block without either'
                            + ' an input path or a readable buffer')
            
        Desc = _OGA(self, "DESC")
        if Attr_Name is not None and Raw_Data is not None:
            #if we are reading or initializing just one attribute
            if Attr_Name in Desc[ATTR_MAP]:
                Attr_Name = self[Desc[ATTR_MAP][Name]]
            elif isinstance(Attr_Name, int) and Name in Desc:
                Attr_Name = Desc[Name]
            
            Desc = self.Get_Desc(Attr_Name)
        else:
            #if we are reading or initializing EVERY attribute

            #clear the block and set it to the right number of empty indices
            _LDI(self, slice(None, None, None))
                        
            if Desc[TYPE].Is_Array:
                _LExt(self, [None]*self.Get_Size())
            else:
                _LExt(self, [None]*Desc[ENTRIES])

            '''If the Init_Block is not None then try
            to use it to populate the List_Block'''
            if isinstance(Init_Block, dict):
                '''Since dict keys can be strings we assume that the
                reason a dict was provided is to set the attributes
                by name rather than index.
                So call self.__setattr__ instead of self.__setitem__'''
                for Name in Init_Block:
                    self.__setattr__(Name, Init_Block[Name])
            elif Init_Block is not None:
                '''loop over the List_Block and copy the entries
                from Init_Block into the List_Block. Make sure to
                loop as many times as the shortest length of the
                two so as to prevent IndexErrors.'''
                for i in range(min(len(self), len(Init_Block))):
                    self.__setitem__(i, Init_Block[i])
        

        if Raw_Data is not None:
            #build the structure from raw data
            R_Off = kwargs.get('Root_Offset', 0)
            C_Off = kwargs.get('Offset', 0)
            Test = kwargs.get('Test', False)

            try:
                #Figure out if the parent is this List_Block or its parent.
                if Attr_Name is None:
                    Parent = self
                else:
                    Parent = self.PARENT
                
                Desc[TYPE].Reader(Parent, Raw_Data, Attr_Name,
                                  R_Off, C_Off, Test=Test)
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read List_Block from file.')
                
        elif Init_Attrs:
            #initialize the attributes
            
            if Desc[TYPE].Is_Array:
                '''This List_Block is an array, so the type of each
                element should be the same then initialize it'''
                try:
                    Attr_Type = Desc[SUB_STRUCT][TYPE]
                    Py_Type = Attr_Type.Py_Type
                except Exception: 
                    raise TypeError("Could not locate the array element " +
                                    "descriptor.\n Could not initialize array.")

                #loop through each element in the array and initialize it
                for i in range(len(self)):
                    if _LGI(self, i) is None:
                        Attr_Type.Reader(self, Attr_Name, i)
            else:
                for i in range(len(self)):
                    '''Only initialize the attribute
                    if a value doesnt already exist'''
                    if _LGI(self, i) is None:
                        Attr_Desc = Desc[i]
                        #if there is a default value,
                        #but its not a List_Block type
                        if (DEFAULT in Attr_Desc and not
                            isinstance(Attr_Desc[DEFAULT], type)):
                            '''set the value to the default
                            defined in the descriptor'''
                            self.__setitem__(i, deepcopy(Attr_Desc[DEFAULT]))
                        else:
                            Attr_Desc[TYPE].Reader(self, Attr_Index=i)

            '''Only initialize the child if the block has a
            child and a value for it doesnt already exist.'''
            if 'CHILD' in Desc and _OGA(self, CHILD) is None:
                Attr_Desc = Desc['CHILD']
                
                #if there is a default value, but its not a List_Block type
                if (DEFAULT in Attr_Desc and not
                    isinstance(Attr_Desc[DEFAULT], type)):
                    #set the value to the default defined in the descriptor
                    self.__setattr__('CHILD', deepcopy(Attr_Desc[DEFAULT]))
                else:
                    #call the reader of the child type
                    Attr_Desc[TYPE].Reader(self, Attr_Index='CHILD')


    def Write(self, **kwargs):
        """This function will write this List_Block to the provided
        file path/buffer. The name of the block will be used as the
        extension. This function is used ONLY for writing a piece
        of a tag to a file/buffer, not the entire tag. DO NOT CALL
        this function when writing a whole tag at once."""
        
        Mode = 'file'
        Filepath = None
        Block_Buffer = None

        Offset = 0
        
        Tag = None
        Temp = False
        Calc_Pointers = True

        if 'Tag' in kwargs:
            Tag = kwargs["Tag"]
        else:
            try:
                Tag = self.Get_Tag()
            except Exception:
                pass
        if 'Calc_Pointers' in kwargs:
            Calc_Pointers = bool(kwargs["Calc_Pointers"])
        else:
            try:
                Calc_Pointers = Tag.Calc_Pointers
            except Exception:
                pass
        
        if kwargs.get("Filepath"):
            Mode = 'file'
            Filepath = kwargs["Filepath"]
        elif kwargs.get('Buffer'):
            Mode = 'buffer'
            Block_Buffer = kwargs['Buffer']

        #if the filepath wasn't provided, try to use
        #a modified version of the parent tags path 
        if Filepath is None and Block_Buffer is None:
            try:
                Filepath = splitext(Tag.Tag_Path)[0]
            except Exception:
                raise IOError('Output filepath was not provided and could ' +
                              'not generate one from parent tag object.')
        Offset = kwargs.get("Offset", Offset)
        Temp = kwargs.get("Temp", Temp)
            
        
        if Filepath is not None and Block_Buffer is not None:
            raise TypeError("Provide either a Buffer " +
                            "or a Filepath, but not both.") 
            
        if Mode == 'file':
            #if the filepath doesnt have an extension, give it one
            if splitext(Filepath)[-1] == '':
                try:
                    Filepath += '.' + _OGA(self,'DESC')['NAME'] + ".blok"
                except Exception:
                    Filepath += ".unnamed.blok"
            
            if Temp:
                Filepath += ".temp"

            try:
                Block_Buffer = open(Filepath, 'wb')
            except Exception:
                raise IOError('Output filepath for writing block was invalid ' +
                              'or the file could not be created.\n    %s' %
                              Filepath)

        '''make sure the buffer has a valid write and seek routine'''
        if not (hasattr(Block_Buffer,'write') or hasattr(Block_Buffer,'seek')):
            raise TypeError('Cannot write a List_Block without either'
                            + ' an output path or a writable buffer')

        
        '''try to write the block to the buffer'''
        try:
            #if we need to calculate the pointers, do so
            if Calc_Pointers:
                '''Make a copy of this block so any changes
                to pointers dont affect the entire Tag'''
                Block = self.__deepcopy__({})
                Block.Set_Pointers(Offset)
            else:
                Block = self

            #make a file as large as the tag is calculated to fill
            Block_Buffer.write(bytes(self.Bin_Size))
            Block.TYPE.Writer(Block, Block_Buffer, None, 0, Offset)
            
            #return the filepath or the buffer in case
            #the caller wants to do anything with it
            if Mode == 'file':
                try:
                    Block_Buffer.close()
                except Exception:
                    pass
                return Filepath
            else:
                return Block_Buffer
        except Exception:
            if Mode == 'file':
                try:
                    Block_Buffer.close()
                except Exception:
                    pass
            try:
                os.remove(Filepath)
            except Exception:
                pass
            raise IOError("Exception occurred while attempting" +
                          " to write the tag block:\n", Filepath)


class P_List_Block(List_Block):
    '''This block allows a reference to the child
    block it describes to be stored as well as a
    reference to whatever block it is parented to'''
    __slots__ = ("DESC", 'PARENT', 'CHILD')
    
    def __init__(self, Desc=None, Init_Block=None,
                 Child=None, Parent=None, **kwargs):
        _OSA(self, 'CHILD', Child)
        List_Block.__init__(self, Desc, Init_Block, Parent, **kwargs)


    def __setattr__(self, Name, New_Value):
        '''docstring'''
        if Name in _OGA(self, '__slots__'):
            if Name == 'CHILD':
                _OSA(self, 'CHILD', New_Value)

                Type = _OGA(self,'DESC')['CHILD']['TYPE']
                if Type.Is_Var_Size and Type.Is_Data:
                    #try to set the size of the attribute
                    try:
                        self.Set_Size(None, 'CHILD')
                    except NotImplementedError: pass
                    except AttributeError: pass
                    
                #if this object is being given a child then try to
                #automatically give the child this object as a parent
                try:
                    if _OGA(New_Value, 'PARENT') != self:
                        _OSA(New_Value, 'PARENT', self)
                except Exception:
                    pass
            else:
                _OSA(self, Name, New_Value)
        else:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc['ATTR_MAP']:
                self.__setitem__(Desc['ATTR_MAP'][Name], New_Value)
            elif Name in Desc:
                self.Set_Desc(Name, New_Value)
            else:
                raise AttributeError(("'%s' of type %s has no "+
                                      "attribute '%s'") %
                                     (Desc.get('NAME','unnamed'),
                                      type(self), Name))
