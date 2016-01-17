import sys

from array import array
from copy import copy, deepcopy
from os import makedirs
from os.path import splitext, dirname, exists
from string import ascii_uppercase, ascii_lowercase
from sys import getsizeof
from traceback import format_exc

from supyr_struct.Defs.Constants import *
from supyr_struct.Buffer import BytesBuffer, BytearrayBuffer, PeekableMmap

__all__ = [ 'Tag_Block', 'Void_Block', 'Data_Block',
            'Bool_Block', 'Enum_Block', 'List_Block', 'While_List_Block',
            'P_List_Block', 'P_While_List_Block',

            'Def_Show', 'All_Show',
            'UNNAMED',   'INVALID', 'UNPRINTABLE',
            'RECURSIVE', 'RAWDATA', 'MISSING_DESC'
            ]

'''Code runs slightly faster if these methods are here instead
of having to be called through the list class every time
and it helps to shorten the width of a lot of lines of code'''
_LGI  = list.__getitem__
_LSI  = list.__setitem__
_LDI  = list.__delitem__
_LSO  = list.__sizeof__
_LApp = list.append
_LExt = list.extend
_LIns = list.insert
_LPop = list.pop

_OSA = object.__setattr__
_OGA = object.__getattribute__
_ODA = object.__delattr__
_OSO = object.__sizeof__

NoneType = type(None)

Def_Show = ('Type', 'Name', 'Value', 'Offset', 'Size', 'Children')
All_Show = ("Name", "Value", "Type", "Offset", "Children",
            "Flags", "Unique", "Size", "Index",
            #"Raw", #raw data can be really bad to show so dont unless specified
            "Py_ID", "Py_Type", "Bin_Size", "Ram_Size")

#reused strings when printing Tag_Blocks
UNNAMED = "<UNNAMED>"
INVALID = '<INVALID>'
RAWDATA = "<RAWDATA>"
UNPRINTABLE = "<UNABLE TO PRINT>"
RECURSIVE = "<RECURSIVE BLOCK '%s'>"
MISSING_DESC = "<NO DESCRIPTOR FOR OBJECT OF TYPE '%s'>"

class Tag_Block():

    #an empty slots needs to be here or else all Tag_Blocks will have a dict
    __slots__ = ()

    def __getattr__(self, Attr_Name):
        '''docstring'''
        try:
            return _OGA(self, Attr_Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc['NAME_MAP']:
                return self[Desc['NAME_MAP'][Attr_Name]]
            elif Attr_Name in Desc:
                return Desc[Attr_Name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'"
                                     %(Desc.get('NAME',UNNAMED),
                                       type(self),Attr_Name))


    def __setattr__(self, Attr_Name, New_Value):
        '''docstring'''
        try:
            _OSA(self, Attr_Name, New_Value)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc['NAME_MAP']:
                self[Desc['NAME_MAP'][Attr_Name]] = New_Value
            elif Attr_Name in Desc:
                self.Set_Desc(Attr_Name, New_Value)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")
                                     %(Desc.get('NAME',UNNAMED),
                                      type(self),Attr_Name))


    def __delattr__(self, Attr_Name):
        '''docstring'''
        try:
            _ODA(self, Attr_Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc['NAME_MAP']:
                #set the size of the block to 0 since it's being deleted
                try:   self.Set_Size(0, Attr_Name=Attr_Name)
                except NotImplementedError: pass
                except AttributeError: pass
                self.Del_Desc(Attr_Name)
                _LDI(self, Desc['NAME_MAP'][Attr_Name])
            elif Attr_Name in Desc:
                self.Del_Desc(Attr_Name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'"
                                     %(Desc.get('NAME',UNNAMED),
                                       type(self),Attr_Name))

    def __str__(self, **kwargs):
        '''docstring'''
        #set the default things to show
        Show = set(Def_Show)
        
        Seen = kwargs['Seen'] = set(kwargs.get('Seen',()))
        Seen.add(id(self))
        
        if "Show" in kwargs:
            Show = kwargs['Show']
            if isinstance(kwargs["Show"], str):
                Show = set([Show])
            else:
                Show = set(Show)
                
        Level       = kwargs.get('Level',0)
        Indent      = kwargs.get('Indent', BLOCK_PRINT_INDENT)
        Printout    = kwargs.get('Printout', False)
        Block_Index = kwargs.get('Block_Index', None)

        #if the list includes 'All' it means to show everything
        if 'All' in Show:
            Show.update(All_Show)

        Tag_String = ' '*Indent*Level + '['
        tempstring = ''
        
        Desc = _OGA(self,'DESC')
        
        if "Index" in Show and Block_Index is not None:
            tempstring += ', #:%s' % Block_Index
        if "Type" in Show:
            tempstring += ', %s' % Desc.get('TYPE').Name
        try:
            if "Offset" in Show:
                tempstring += (', Offset:%s' % self.PARENT.DESC['ATTR_OFFS']\
                               [Block_Index])
        except Exception:
            pass
        if "Unique" in Show:  tempstring += ', Unique:%s' %('ORIG_DESC' in Desc)
        if "Py_ID" in Show:   tempstring += ', Py_ID:%s' % id(self)
        if "Py_Type" in Show: tempstring += ', Py_Type:%s'%Desc['TYPE'].Py_Type
        if "Size" in Show:    tempstring += ', Size:%s' % self.Get_Size()
        if "Name" in Show:    tempstring += ', %s' % Desc.get('NAME')

        Tag_String += tempstring + ' ]'
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        return Tag_String
    

    def __sizeof__(self, Seen_Set=None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _OSO(self)
                
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
            
        return Bytes_Total

    def _Bin_Size(self, Block, Sub_Struct=False):
        raise NotImplementedError('Bin_Size calculation must be manually '+
                                  'defined per Tag_Block subclass.')

    @property
    def Bin_Size(self):
        '''Returns the size of this Tag_Block and all Blocks parented to it.
        This size is how many bytes it would take up if written to a buffer.'''
        return self._Bin_Size(self)


    def Get_Desc(self, Desc_Key, Attr_Name=None):
        '''Returns the value in the object's descriptor
        under the key "Desc_Key". If Attr_Name is not None,
        the descriptor being searched for "Desc_Key" will
        instead be the attribute "Attr_Name".'''
        Desc = _OGA(self, "DESC")

        '''if we are getting something in the descriptor
        of one of this Tag_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            if isinstance(Attr_Name, int) or Attr_Name in Desc:
                Desc = Desc[Attr_Name]
            else:
                if Attr_Name in Desc:
                    Desc = Desc[Attr_Name]
                else:
                    try:
                        Desc = Desc[Desc['NAME_MAP'][Attr_Name]]
                    except Exception:
                        raise KeyError(("Could not locate '%s' in the "+
                                        "descriptor of '%s'.") %
                                       (Attr_Name, Desc.get('NAME')))

        '''Try to return the descriptor value under the key "Desc_Key" '''
        if Desc_Key in Desc:
            return Desc[Desc_Key]
        
        try:
            return Desc[Desc['NAME_MAP'][Desc_Key]]
        except KeyError:
            if Attr_Name is not None:
                raise KeyError(("Could not locate '%s' in the sub-descriptor "+
                                "'%s' in the descriptor of '%s'") %
                               (Desc_Key, Attr_Name, Desc.get('NAME')))
            else:
                raise KeyError(("Could not locate '%s' in the descriptor " +
                                "of '%s'.") % (Desc_Key, Desc.get('NAME')))


    def Del_Desc(self, Desc_Key, Attr_Name=None):
        '''Enables clean deletion of attributes from this
        Tag_Block's descriptor. Takes care of decrementing
        ENTRIES, shifting indexes of attributes, removal from
        NAME_MAP, and making sure the descriptor is unique.
        DOES NOT shift offsets or change struct size.
        That is something the user must do because any way
        to handle that isn't going to work for everyone.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this Tag_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[NAME_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc['NAME_MAP'][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if 'ORIG_DESC' not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
            
        if isinstance(Desc_Key, int):
            #"Desc_Key" must be a string for the
            #below routine to work, so change it
            Desc_Key = Desc[Desc_Key]['NAME']
        
        '''Check if the descriptor needs to be made unique'''
        if not Desc.get('ORIG_DESC'):
            Desc = self.Make_Unique(Desc)
            
        Name_Map = Desc.get('NAME_MAP')
            
        '''if we are deleting a descriptor based attribute'''
        if Name_Map and Desc_Key in Desc['NAME_MAP']:
            Attr_Index = Name_Map[Desc_Key]

            #if there is an offset mapping to set,
            #need to get a local reference to it
            Attr_Offsets = Desc.get('ATTR_OFFS')
            
            #delete the name of the attribute from NAME_MAP
            del Name_Map[Desc_Key]
            #delete the attribute
            del Desc[Attr_Index]
            #remove the offset from the list of offsets
            if Attr_Offsets is not None:
                Attr_Offsets.pop(Attr_Index)
            #decrement the number of entries
            Desc['ENTRIES'] -= 1
            
            '''if an attribute is being deleted,
            then NAME_MAP needs to be shifted down
            and the key of each attribute needs to be
            shifted down in the descriptor as well'''

            Last_Entry = Desc['ENTRIES']

            #shift all the indexes down by 1
            for i in range(Attr_Index, Last_Entry):
                Desc[i] = Desc[i+1]
                Name_Map[Desc[i+1]['NAME']] = i

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
        Tag_Block's descriptor or adding non-attributes.
        Takes care of adding to NAME_MAP and other stuff.
        DOES NOT shift offsets or change struct size.
        That is something the user must do because any way
        to handle that isn't going to work for everyone.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this Tag_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[NAME_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc['NAME_MAP'][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if 'ORIG_DESC' not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
        
        if isinstance(Desc_Key, int):
            #"Desc_Key" must be a string for the
            #below routine to work, so change it
            Desc_Key = Desc[Desc_Key]['NAME']

        Desc_Name = Desc_Key
        if 'NAME_MAP' in Desc and Desc_Name in Desc['NAME_MAP']:
            Desc_Name = Desc['NAME_MAP'][Desc_Name]

        '''Check if the descriptor needs to be made unique'''
        if not Desc.get('ORIG_DESC') and id(Desc[Desc_Name]) != id(New_Value):
            Desc = self.Make_Unique(Desc)

        Name_Map = Desc.get('NAME_MAP')
        if Name_Map and Desc_Key in Desc['NAME_MAP']:  
            '''we are setting a descriptor based attribute.
            We might be changing what it's named'''
            
            Attr_Index = Name_Map[Desc_Key]

            #if the New_Value desc doesnt have a NAME entry, the
            #New_Name will be set to the current entry's name
            New_Name = New_Value.get('NAME', Desc_Key)
                
            '''if the names are different, change the
            NAME_MAP and ATTR_OFFS mappings'''
            if New_Name != Desc_Key:
                '''Run a series of checks to make
                sure the name in New_Value is valid'''
                self.Validate_Name(New_Name, Name_Map, Attr_Index)
            
                #remove the old name from the Name_Map
                del Name_Map[Desc_Key]
                #set the name of the attribute in NAME_MAP
                Name_Map[New_Name] = Attr_Index
            else:
                #If the New_Value doesn't have a name,
                #give it the old descriptor's name
                New_Value['NAME'] = Desc_Key
            
            #set the attribute to the new New_Value
            Desc[Attr_Index] = New_Value

        else:
            '''we are setting something other than an attribute'''
            
            '''if setting the Name, there are some rules to follow'''
            if Desc_Key == 'NAME' and New_Value != Desc.get('NAME'):
                Name_Map = None
                try:   Parent = self.PARENT
                except Exception: pass
                
                '''make sure to change the name in the
                parent's Name_Map mapping as well'''
                if Attr_Name is not None:
                    Name_Map = deepcopy(Self_Desc['NAME_MAP'])
                elif Parent:
                    try:   Name_Map = deepcopy(Parent.NAME_MAP)
                    except Exception: pass

                '''if the parent name mapping exists,
                change the name that it's mapped to'''
                if Name_Map is not None:
                    Attr_Index = Name_Map[Desc['NAME']]
                    '''Run a series of checks to make
                    sure the name in New_Value is valid'''
                    self.Validate_Name(New_Value, Name_Map, Attr_Index)
                
                    #set the index of the new name to the index of the old name
                    Name_Map[New_Value] = Attr_Index
                    #delete the old name
                    del Name_Map[Desc['NAME']]


                ''''Now that we've gotten to here,
                it's safe to commit the changes'''
                if Name_Map is not None:
                    #set the parent's NAME_MAP to the newly configured one
                    if Attr_Name is not None:
                        Self_Desc['NAME_MAP'] = Name_Map
                    elif Parent:
                        Parent.Set_Desc('NAME_MAP', Name_Map)
                        
                else:
                    self.Validate_Name(New_Value)
                
            Desc[Desc_Key] = New_Value

        #replace the old descriptor with the new one
        if Attr_Name is not None:
            Self_Desc[Attr_Name] = Desc
            _OSA(self, "DESC", Self_Desc)
        else:
            _OSA(self, "DESC", Desc)



    def Ins_Desc(self, Desc_Key, New_Value, Attr_Name=None):
        '''Enables clean insertion of attributes into this
        Tag_Block's descriptor. Takes care of incrementing
        ENTRIES, adding to NAME_MAP, and shifting indexes.'''
        
        Desc = _OGA(self, "DESC")

        '''if we are setting something in the descriptor
        of one of this Tag_Block's attributes, then we
        need to set Desc to the attributes descriptor'''
        if Attr_Name is not None:
            #if the Attr_Name doesnt exist in the Desc, try to
            #see if it maps to a valid key in Desc[NAME_MAP]
            if not(Attr_Name in Desc or isinstance(Attr_Name, int)):
                Attr_Name = Desc['NAME_MAP'][Attr_Name]
            Self_Desc = Desc
            Desc = Self_Desc[Attr_Name]
            
            '''Check if the descriptor needs to be made unique'''
            if 'ORIG_DESC' not in Self_Desc:
                Self_Desc = self.Make_Unique(Self_Desc)
            
        '''Check if the descriptor needs to be made unique'''
        if not Desc.get('ORIG_DESC'):
            Desc = self.Make_Unique(Desc)

        #if Desc_Key is an already existing attribute, we are
        #inserting the new descriptor where it currently is.
        #Thus, we need to get what index the attribute is in.
        if 'NAME_MAP' in Desc and Desc_Key in Desc['NAME_MAP']:
            Desc_Key = Desc['NAME_MAP'][Desc_Key]

            
        if isinstance(Desc_Key, int):
            '''we are adding an attribute'''
            Name_Map = Desc['NAME_MAP']
            Attr_Index = Desc_Key
            Desc_Key = New_Value['NAME']
            
            #before any changes are committed, validate the
            #name to make sure we aren't adding a duplicate
            self.Validate_Name(Desc_Key, Name_Map)

            #if there is an offset mapping to set,
            #need to get a local reference to it
            Attr_Offsets = Desc.get('ATTR_OFFS')
            
            '''if an attribute is being added, then
            NAME_MAP needs to be shifted up and the
            key of each attribute needs to be
            shifted up in the descriptor as well'''
            #shift all the indexes up by 1 in reverse
            for i in range(Desc['ENTRIES'], Attr_Index, -1):
                Desc[i] = Desc[i-1]
                Name_Map[Desc[i-1]['NAME']] = i
            
            #add name of the attribute to NAME_MAP
            Name_Map[Desc_Key] = Attr_Index
            #add the attribute
            Desc[Attr_Index] = New_Value
            #increment the number of entries
            Desc['ENTRIES'] += 1
                    
            if Attr_Offsets is not None:
                try:
                    '''set the offset of the new attribute to
                    the offset of the old one plus its size'''
                    Offset = (Attr_Offsets[Attr_Index-1] +
                              self.Get_Size(Attr_Index-1))
                except Exception:
                    '''If we fail, it means this attribute is the
                    first in the structure, so its offset is 0'''
                    Offset = 0

                '''add the offset of the attribute
                to the offsets map by name and index'''
                Attr_Offsets.insert(Attr_Index, Offset)

        else:
            if isinstance(New_Value, dict):
                raise Exception(("Supplied value was not a valid attribute "+
                                 "descriptor.\nThese are the supplied "+
                                 "descriptor's keys.\n    %s")%New_Value.keys())
            else:
                raise Exception("Supplied value was not a valid attribute "+
                                 "descriptor.\nGot:\n    %s" % New_Value)

        #replace the old descriptor with the new one
        if Attr_Name is not None:
            Self_Desc[Attr_Name] = Desc
            _OSA(self, "DESC", Self_Desc)
        else:
            _OSA(self, "DESC", Desc)


    def Res_Desc(self, Name=None):
        '''Restores the descriptor of the attribute "Name"
        WITHIN this Tag_Block's descriptor to its backed up
        original. This is done this way in case the attribute
        doesn't have a descriptor, like strings and integers.
        If Name is None, restores this Tag_Blocks descriptor.'''
        Desc = _OGA(self, "DESC")
        Name_Map = Desc['NAME_MAP']
        
        #if we need to convert Name from an int into a string
        if isinstance(Name, int):
            Name = Name_Map['NAME']

        if Name is not None:
            '''restoring an attributes descriptor'''
            if Name in Name_Map:
                Attr_Index = Name_Map[Name]
                Attr_Desc = Desc.get(Attr_Index)
                
                #restore the descriptor of this Tag_Block's
                #attribute is an original exists
                Desc[Attr_Index] = Attr_Desc.get('ORIG_DESC', Attr_Desc)
            else:
                raise AttributeError(("'%s' is not an attribute in the "+
                                      "Tag_Block '%s'. Cannot restore " +
                                      "descriptor.")%(Name,Desc.get('NAME')))
        elif Desc.get('ORIG_DESC'):
            '''restore the descriptor of this Tag_Block'''
            _OSA(self, "DESC", Desc['ORIG_DESC'])


    def Make_Unique(self, Desc=None):
        '''Returns a unique copy of the provided descriptor. The
        copy is made unique from the provided one by replacing it
        with a semi-shallow copy and adding a reference to the
        original descriptor under the key "ORIG_DESC". The copy
        is semi-shallow in that the attributes are shallow, but
        entries like NAME_MAP, ATTR_OFFS, and NAME are deep.
        
        If you use the new, unique, descriptor as this object's
        descriptor, this object will end up using more ram.'''

        if Desc is None:
            Desc = _OGA(self, "DESC")
        
        #make a new descriptor with a reference to the original
        New_Desc = { 'ORIG_DESC':Desc }
        
        #semi shallow copy all the keys in the descriptor
        for key in Desc:
            if isinstance(key, int) or key in ('CHILD', 'SUB_STRUCT', 'CASES'):
                '''if the entry is an attribute then make a reference to it'''
                New_Desc[key] = Desc[key]
            else:
                '''if the entry IS NOT an attribute then full copy it'''
                New_Desc[key] = deepcopy(Desc[key])

        return New_Desc


    def Get_Tag(self):
        '''This function upward navigates the Tag_Block
        structure it is a part of until it finds a block
        with the attribute "Tag_Data", and returns it.

        Raises LookupError if the Tag is not found'''
        Tag_Cls   = Tag.Tag
        Found_Tag = self
        try:
            while True:
                Found_Tag = Found_Tag.PARENT
                
                '''check if the object is a Tag'''
                if isinstance(Found_Tag, Tag_Cls):
                    return Found_Tag
        except AttributeError:
            pass
        raise LookupError("Could not locate parent Tag object.")
    

    def Get_Neighbor(self, Path, Block=None):
        """Given a path to follow, this function will
        navigate neighboring blocks until the path is
        exhausted and return the last block."""
        if not isinstance(Path, str):
            raise TypeError("'Path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(Path)) )
        
        Path_Fields = Path.split('.')

        #if a starting block wasn't provided, or it was
        #and it's not a Tag_Block with a parent reference
        #we need to set it to something we can navigate from
        if not hasattr(Block, 'PARENT'):
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
                else:
                    New_Block = Block.__getattr__(field)
                #replace the block to the new block to continue the cycle
                Block = New_Block
        except Exception:
            self_name  = _OGA(self,'DESC').get('NAME', type(self))
            try:   block_name = Block.NAME
            except Exception: block_name = type(Block)
            try:
                raise AttributeError(("Path string to neighboring block is " +
                                      "invalid.\nStarting block was '%s'. "+
                                      "Couldnt find '%s' in '%s'.\n" +
                                      "Full path was '%s'") %
                                     (self_name, field, block_name, Path))
            except NameError: 
                raise AttributeError(("Path string to neighboring block is " +
                                      "invalid.\nStarting block was '%s'. "+
                                      "Full path was '%s'") % (self_name, Path))
        return Block
    

    def Get_Meta(self, Meta_Name, Attr_Index=None, **kwargs):
        '''docstring'''
        Desc = _OGA(self,'DESC')

        if isinstance(Attr_Index, int):
            Block = self[Attr_Index]
            if Desc['TYPE'].Is_Array:
                Desc = Desc['SUB_STRUCT']
            else:
                Desc = Desc[Attr_Index]
        elif isinstance(Attr_Index, str):
            Block = self.__getattr__(Attr_Index)
            try:
                Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
            except Exception:
                Desc = Desc[Attr_Index]
        else:
            Block = self

            
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
                if hasattr(Block, 'PARENT'):
                    Parent = Block.PARENT
                else:
                    Parent = self
                    
                return Meta(Attr_Index=Attr_Index, Parent=Parent,
                            Block=Block, **kwargs)
            else:
                raise LookupError("Couldnt locate meta info")
        else:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            raise AttributeError("'%s' does not exist in '%s'."
                                 % (Meta_Name,Block_Name))


    def Get_Raw_Data(self, **kwargs):
        '''docstring'''
        Filepath = kwargs.get('Filepath')
        Raw_Data = kwargs.get('Raw_Data')
        
        if Filepath is not None:
            if Raw_Data is not None:
                raise TypeError("Provide either Raw_Data or Filepath, not both")
            
            '''try to open the tag's path as the raw tag data'''
            try:
                with open(Filepath, 'r+b') as Tag_File:
                   Raw_Data = PeekableMmap(Tag_File.fileno(), 0)
            except Exception:
                raise IOError('Input filepath for reading Tag was ' +
                              'invalid or the file could not be ' +
                              'accessed.\n' + ' '*BPI + Filepath)
        
        if Raw_Data is None or (hasattr(Raw_Data, 'read') and
                                hasattr(Raw_Data, 'seek')):
            return Raw_Data
            
        raise TypeError(('Cannot build a %s without either' % type(self))
                        + ' an input path or a readable buffer')

        
    def Set_Neighbor(self, Path, New_Value, Block=None, Op=None):
        """Given a path to follow, this function
        will navigate neighboring blocks until the
        path is exhausted and set the last block."""
        if not isinstance(Path, str):
            raise TypeError("'Path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(Path)) )
        
        Path_Fields = Path.split('.')

        #if a starting block wasn't provided, or it was
        #and it's not a Tag_Block with a parent reference
        #we need to set it to something we can navigate from
        if not hasattr(Block, 'PARENT'):
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
                else:
                    New_Block = Block.__getattr__(field)

                #replace the block to the new block to continue the cycle
                Block = New_Block

        except Exception:
            self_name  = _OGA(self,'DESC').get('NAME', type(self))
            try:   block_name = Block.NAME
            except Exception: block_name = type(Block)
            try:
                raise AttributeError(("Path string to neighboring block is " +
                                      "invalid.\nStarting block was '%s'. "+
                                      "Couldnt find '%s' in '%s'.\n" +
                                      "Full path was '%s'") %
                                     (self_name, field, block_name, Path))
            except NameError: 
                raise AttributeError(("Path string to neighboring block is " +
                                      "invalid.\nStarting block was '%s'. "+
                                      "Full path was '%s'") % (self_name, Path))
            
        if Op is None:
            pass
        elif Op == '+':
            New_Value = Block.__getattr__(Path_Fields[-1]) + New_Value
        elif Op == '-':
            New_Value = Block.__getattr__(Path_Fields[-1]) - New_Value
        elif Op == '*':
            New_Value = Block.__getattr__(Path_Fields[-1]) * New_Value
        elif Op == '/':
            New_Value = Block.__getattr__(Path_Fields[-1]) // New_Value
        else:
            raise TypeError(("Unknown operator type '%s' " +
                             "for setting neighbor.") % Op)
        
        Block.__setattr__(Path_Fields[-1], New_Value)
        
        return Block


    def Set_Meta(self, Meta_Name, New_Value=None,
                 Attr_Index=None, Op=None, **kwargs):
        '''docstring'''
        Desc = _OGA(self,'DESC')
        
        if isinstance(Attr_Index, int):
            Block = self[Attr_Index]
            Block_Name = Attr_Index
            if Desc['TYPE'].Is_Array:
                Desc = Desc['SUB_STRUCT']
            else:
                Desc = Desc[Attr_Index]
        elif isinstance(Attr_Index, str):
            Block = self.__getattr__(Attr_Index)
            Block_Name = Attr_Index
            try:
                Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
            except Exception:
                Desc = Desc[Attr_Index]
        else:
            Block = self
            Block_Name = Desc['NAME']


        Meta_Value = Desc.get(Meta_Name)
        
        #raise exception if the Meta_Value is None
        if Meta_Value is None and Meta_Name not in Desc:
            raise AttributeError("'%s' does not exist in '%s'."
                                 % (Meta_Name,Block_Name))
        elif isinstance(Meta_Value, int):
            if Op is None:
                self.Set_Desc(Meta_Name, New_Value, Attr_Index)
            elif Op == '+':
                self.Set_Desc(Meta_Name, Meta_Value+New_Value, Attr_Index)
            elif Op == '-':
                self.Set_Desc(Meta_Name, Meta_Value-New_Value, Attr_Index)
            elif Op == '*':
                self.Set_Desc(Meta_Name, Meta_Value*New_Value, Attr_Index)
            elif Op == '/':
                self.Set_Desc(Meta_Name, Meta_Value//New_Value, Attr_Index)
            else:
                raise TypeError(("Unknown operator type '%s' for " +
                                 "setting '%s'.") % (Op, Meta_Name))
            self.Set_Desc(Meta_Name, New_Value, Attr_Index)
        elif isinstance(Meta_Value, str):
            '''set meta by traversing the tag structure
            along the path specified by the string'''
            self.Set_Neighbor(Meta_Value, New_Value, Block, Op)
        elif hasattr(Meta_Value, "__call__"):
            '''set the meta by calling the provided function'''
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
            
            Meta_Value(Attr_Index=Attr_Index, New_Value=New_Value,
                       Op=Op, Parent=Parent, Block=Block, **kwargs)
        else:
            raise TypeError(("Meta specified in '%s' is not a valid type." +
                            "Expected int, str, or function. Got %s.\n") %
                            (Block_Name, type(Meta_Value)) +
                            "Cannot determine how to set the meta data." )


    def Collect_Pointers(self, Offset=0, Seen=None, Pointed_Blocks=None,
                         Sub_Struct=False, Root=False, Attr_Index=None):
        if Seen is None:
            Seen = set()
            
        if Attr_Index is None:
            Desc = _OGA(self,'DESC')
            Block = self
        else:
            Desc = self.Get_Desc(Attr_Index)
            Block = self.__getattr__(Attr_Index)

        if 'POINTER' in Desc:
            Pointer = Desc['POINTER']
            if isinstance(Pointer, int):
                #if the next blocks are to be located directly after
                #this one then set the current offset to its location
                if Desc.get('CARRY_OFF', True):
                    Offset = Pointer

            #if this is a block within the root block
            if not Root:
                Pointed_Blocks.append((self, Attr_Index, Sub_Struct))
                return Offset
            
        Seen.add(id(Block))
        
        Type = Desc['TYPE']
            
        if Desc.get('ALIGN'):
            Align = Desc['ALIGN']
            Offset += (Align-(Offset%Align))%Align

        #increment the offset by this blocks size if it isn't a substruct
        if not Sub_Struct and (Type.Is_Struct or Type.Is_Data):
            Offset += self.Get_Size()
            Sub_Struct = True
            
        return Offset


    def Set_Pointers(self, Offset=0):
        '''Scans through this block and sets the pointer of
        each pointer based block in a way that ensures that,
        when written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other block.

        This function is a copy of the Tag.Collect_Pointers().
        This is ONLY to be called by a Tag_Block when it is writing
        itself so the pointers can be set as though this is the root.'''
        
        #Keep a set of all seen block IDs to prevent infinite recursion.
        Seen = set()
        PB_Blocks = []

        '''Loop over all the blocks in self and log all blocks that use
        pointers to a list. Any pointer based blocks will NOT be entered.
        
        The size of all non-pointer blocks will be calculated and used
        as the starting offset pointer based blocks.'''
        Offset = self.Collect_Pointers(Offset, Seen, PB_Blocks)

        #Repeat this until there are no longer any pointer
        #based blocks for which to calculate pointers.
        while PB_Blocks:
            New_PB_Blocks = []
            
            '''Iterate over the list of pointer based blocks and set their
            pointers while incrementing the offset by the size of each block.
            
            While doing this, build a new list of all the pointer based
            blocks in all of the blocks currently being iterated over.'''
            for Block in PB_Blocks:
                Block, Attr_Index, Sub_Struct = Block[0], Block[1], Block[2]
                Block.Set_Meta('POINTER', Offset, Attr_Index)
                Offset = Block.Collect_Pointers(Offset, Seen, New_PB_Blocks,
                                                Sub_Struct, True, Attr_Index)
                #this has been commented out since there will be a routine
                #later that will collect all pointers and if one doesn't
                #have a matching block in the structure somewhere then the
                #pointer will be set to 0 since it doesnt exist.
                '''
                #In binary structs, usually when a block doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if Block.Get_Size(Attr_Index) > 0:
                    Block.Set_Meta('POINTER', Offset, Attr_Index)
                    Offset = Block.Collect_Pointers(Offset, Seen, New_PB_Blocks,
                                                    False, True, Attr_Index)
                else:
                    Block.Set_Meta('POINTER', 0, Attr_Index)'''
                    
            #restart the loop using the next level of pointer based blocks
            PB_Blocks = New_PB_Blocks


    def Read(self, **kwargs):
        raise NotImplementedError('Subclasses of Tag_Block must '+
                                  'define their own Read() method.')


    def Write(self, **kwargs):
        """This function will write this Tag_Block to the provided
        file path/buffer. The name of the block will be used as the
        extension. This function is used ONLY for writing a piece
        of a tag to a file/buffer, not the entire tag. DO NOT CALL
        this function when writing a whole tag at once."""
        
        Mode = 'file'
        Filepath     = kwargs.get("Filepath")
        Block_Buffer = kwargs.get('Buffer')
        Offset = kwargs.get("Offset", 0)
        Temp   = kwargs.get("Temp", False)

        if Filepath:
            Mode = 'file'
        elif Block_Buffer:
            Mode = 'buffer'

        if 'Tag' in kwargs:
            Tag = kwargs["Tag"]
        else:
            try:
                Tag = self.Get_Tag()
            except Exception:
                Tag = None
        if 'Calc_Pointers' in kwargs:
            Calc_Pointers = bool(kwargs["Calc_Pointers"])
        else:
            try:
                Calc_Pointers = Tag.Calc_Pointers
            except Exception:
                Calc_Pointers = True

        #if the filepath wasn't provided, try to use
        #a modified version of the parent tags path 
        if Filepath is None and Block_Buffer is None:
            try:
                Filepath = splitext(Tag.Tag_Path)[0]
            except Exception:
                raise IOError('Output filepath was not provided and could ' +
                              'not generate one from parent tag object.')
            
        if Filepath is not None and Block_Buffer is not None:
            raise IOError("Provide either a Buffer or a Filepath, not both.")
        
        Folderpath = dirname(Filepath)

        #if the filepath ends with the folder path terminator, raise an error
        if Filepath.endswith('\\') or Filepath.endswith('/'):
            raise IOError('Filepath must be a path to a file, not a folder.')

        #if the path doesnt exist, create it
        if not exists(Folderpath):
            makedirs(Folderpath)
            
        if Mode == 'file':
            #if the filepath doesnt have an extension, give it one
            if splitext(Filepath)[-1] == '':
                Filepath += '.'+_OGA(self,'DESC').get('NAME','untitled')+".blok"
            
            if Temp:
                Filepath += ".temp"
            try:
                Block_Buffer = open(Filepath, 'w+b')
            except Exception:
                raise IOError('Output filepath for writing block was invalid ' +
                              'or the file could not be created.\n    %s' %
                              Filepath)

        '''make sure the buffer has a valid write and seek routine'''
        if not (hasattr(Block_Buffer,'write') and hasattr(Block_Buffer,'seek')):
            raise TypeError('Cannot write a Tag_Block without either'
                            + ' an output path or a writable buffer')

        
        Copied = False
        '''try to write the block to the buffer'''
        try:
            #if we need to calculate the pointers, do so
            if Calc_Pointers:
                '''Make a copy of this block so any changes
                to pointers dont affect the entire Tag'''
                try:
                    Block = self.__deepcopy__({})
                    Copied = True
                    Block.Set_Pointers(Offset)
                except NotImplementedError:
                    pass
            else:
                Block = self

            #make a file as large as the block is calculated to fill
            Block_Buffer.seek(self.Bin_Size-1)
            Block_Buffer.write(b'\x00')
            
            #start the writing process
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
                          " to write the tag block:\n    " + Filepath)
        
        #if a copy of the block was made(for changing pointers) delete the copy
        if Copied:
            del Block
    

    def Validate_Name(self, Attr_Name, Name_Map={}, Attr_Index=0):
        '''Checks if "Attr_Name" is valid to use for an attribute string.
        Raises a NameError or TypeError if it isnt. Returns True if it is.
        Attr_Name must be a string.'''
        
        assert isinstance(Attr_Name,str),\
               "'Attr_Name' must be a string, not %s" % type(Attr_Name)
        
        if Name_Map.get(Attr_Name, Attr_Index) != Attr_Index:
            raise NameError(("'%s' already exists as an attribute in '%s'.\n"+
                           'Duplicate names are not allowed.')%
                            (Attr_Name,_OGA(self,'DESC').get('NAME')))
        elif not isinstance(Attr_Name, str):
            raise TypeError("Attribute names must be of type str, not %s" %
                            type(Attr_Name))
        elif Attr_Name == '' or Attr_Name is None:
            raise NameError("'' and None cannot be used as attribute names.")
        elif Attr_Name[0] not in Alpha_IDs:
            raise NameError("The first character of an attribute name must be "+
                            "either an alphabet character or an underscore.")
        elif Attr_Name.strip(Alpha_Numeric_IDs_Str):
            #check all the characters to make sure they are valid identifiers
            raise NameError(("'%s' is an invalid identifier as it "+
                             "contains characters other than "+
                             "alphanumeric or underscores.") % Attr_Name)
        return True

'''For now, this class will be unused as the Void Field_Type will
just use None. This consideration is for saving RAM and CPU cycles.'''
class Void_Block(Tag_Block):
    #DESC = { TYPE:Field_Types.Void, NAME:'Voided', GUI_NAME:'Voided' }
    __slots__ = ('DESC', 'PARENT')

    def __init__(self, Desc=None, Parent=None, **kwargs):
        '''docstring'''
        assert isinstance(Desc, dict) and ('TYPE' in Desc and 'NAME')

        _OSA(self, "DESC",   Desc)
        _OSA(self, "PARENT", Parent)
    
    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''
        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None
        return type(self)(_OGA(self,'DESC'), Parent=Parent)

    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the same descriptor.'''
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None

        #make a new block object sharing the same descriptor.
        Dup_Block = type(self)(_OGA(self,'DESC'), Parent=Parent)
        memo[id(self)] = Dup_Block
        
        return Dup_Block
    
    def __str__(self, **kwargs):
        '''docstring'''
        Printout = kwargs.get('Printout', False)
        kwargs['Printout'] = False
        Tag_String = Tag_Block.__str__(self, **kwargs).replace(',','',1)
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        return Tag_String

    def _Bin_Size(self, Block, Sub_Struct=False):
        '''docstring'''
        return 0
    
    def Get_Size(self, Attr_Index=None, **kwargs):
        '''docstring'''
        return 0
    
    def Read(self, **kwargs):
        '''void blocks have nothing to be read'''
        pass
    
    

class List_Block(list, Tag_Block):
    """
    List_Blocks are the primary method of storing hierarchial
    data, and can be seen as a mutable version of namedtuples.
    They function as a list where each entry can be accessed
    by its attribute name defined in the descriptor.

    For example: If the value in key "0" in the descriptor of the
    object "Block" has a key:value pair of "NAME":"Data", then doing:
    
    Block[0] = "here's a string"
        is the same as doing:
    Block.Data = "here's a string"
        or
    Block['Data'] = "here's a string"
    """
    
    __slots__ = ("DESC", "PARENT")

    def __init__(self, Desc=None, Parent=None, **kwargs):
        '''docstring'''
        assert isinstance(Desc, dict) and ('TYPE' in Desc and 'NAME')
        assert 'NAME_MAP' in Desc and 'ENTRIES' in Desc
        
        _OSA(self, "DESC",   Desc)
        _OSA(self, 'PARENT', Parent)
        
        if kwargs:
            self.Read(**kwargs)

    
    def __str__(self, **kwargs):
        '''docstring'''
        #set the default things to show
        Show = set(Def_Show)
        
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
        Precision = kwargs.get('Precision', None)
        Printout = kwargs.get('Printout', False)

        #if the list includes 'All' it means to show everything
        if 'All' in Show:
            Show.remove('All')
            Show.update(All_Show)

        Print_Ram_Size = "Ram_Size" in Show
        Print_Bin_Size = "Bin_Size" in Show
        Print_Children = "Children" in Show
        Print_Py_Type = "Py_Type" in Show
        Print_Py_ID = "Py_ID" in Show
        Print_Offset = "Offset" in Show
        Print_Unique = "Unique" in Show
        Print_Flags = "Flags" in Show
        Print_Value = "Value" in Show
        Print_Index = "Index" in Show
        Print_Type = "Type" in Show
        Print_Name = "Name" in Show
        Print_Size = "Size" in Show
        Print_Raw = "Raw" in Show
        
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

        Desc = _OGA(self,'DESC')
        
        if Print_Index and Block_Index is not None:
            tempstring = ', #:%s' % Block_Index
        if Print_Type and hasattr(self, 'TYPE'):
            tempstring += ', %s' % Desc['TYPE'].Name
        if Print_Offset:
            if hasattr(self, POINTER):
                tempstring += ', Pointer:%s' % self.Get_Meta('POINTER')
            else:
                try:
                    tempstring += (', Offset:%s' % self.PARENT['ATTR_OFFS']\
                                   [Block_Index])
                except Exception:
                    pass
        if Print_Unique:
            tempstring += ', Unique:%s' % ('ORIG_DESC' in Desc)
        if Print_Py_ID:
            tempstring += ', Py_ID:%s' % id(self)
        if Print_Py_Type:
            tempstring += ', Py_Type:%s' % Desc['TYPE'].Py_Type
        if Print_Size:
            if hasattr(self, 'SIZE') and not Desc['TYPE'].Is_Container:
                tempstring += ', Size:%s' % self.Get_Size()
            tempstring += ', Entries:%s' % len(self)
        if Print_Name and 'NAME' in Desc:
            tempstring += ', %s' % Desc['NAME']

        Tag_String += tempstring.replace(',','',1)
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''
        else:
            Tag_String += '\n'

        #create an Attr_Offsets list for printing attribute offsets
        try:
            Attr_Offsets = Desc['ATTR_OFFS']
        except Exception:
            Attr_Offsets = []

        Is_Array = Desc['TYPE'].Is_Array
            
        #Print all this List_Block's indexes
        for i in range(len(self)):
            Data = self[i]
            kwargs['Block_Index'] = i
            
            tempstring = ''
            
            if isinstance(Data, Tag_Block):
                if id(Data) in Seen:
                    if Print_Index:
                        tempstring = ' #:%s,' % i
                    Tag_String += (Indent_Str1 + tempstring + " " +
                                   RECURSIVE % (Data.NAME))
                else:
                    try:
                        Tag_String += Data.__str__(**kwargs)
                    except Exception:
                        Tag_String += '\n' + format_exc()
            else:
                Tag_String += Indent_Str1 + '['
                try:
                    if Is_Array:
                        Attr_Desc = Desc['SUB_STRUCT']
                    else:
                        Attr_Desc = Desc[i]
                except Exception: 
                    Tag_String = Tag_String[:-1] + MISSING_DESC% type(Data)+"\n"
                    continue

                Type = Attr_Desc['TYPE']
                if Print_Index:
                    tempstring += ', #:%s' % i
                if Print_Type:
                    tempstring += ', %s' % Attr_Desc['TYPE'].Name
                if Print_Offset:
                    try:
                        tempstring += ', Offset:%s'%Attr_Offsets[i]
                    except Exception:
                        pass
                if Print_Unique:
                    tempstring += ', Unique:%s' % ('ORIG_DESC' in Attr_Desc)
                if Print_Py_ID:
                    tempstring += ', Py_ID:%s' % id(Data)
                if Print_Py_Type:
                    tempstring += ', Py_Type:%s' % Type.Py_Type
                if Print_Size:
                    try:
                        tempstring += ', Size:%s' % self.Get_Size(i)
                    except Exception:
                        pass
                if Print_Name:
                    tempstring += ', %s' % Attr_Desc.get('NAME')
                    
                if Print_Value:
                    if isinstance(Data, float) and isinstance(Precision, int):
                        tempstring += ', %s'%("{:."+str(Precision)+"f}")\
                                      .format(round(Data, Precision))
                    elif Type.Is_Raw and not Print_Raw:
                        tempstring += ', ' + RAWDATA
                    else:
                        tempstring += ', %s' % Data
                        
                Tag_String += tempstring.replace(',','',1) + ' ]'
                    
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
        if hasattr(self, 'CHILD') and self.CHILD is not None and Print_Children:
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
                    Tag_String += (Indent_Str1 + RECURSIVE_BLOCK % (Child.NAME))
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
                Child_Desc = Desc['CHILD']
                Child_Type = Child_Desc['TYPE']
                    
                if Print_Type:
                    tempstring += ', %s' % Child_Type.Name
                if Print_Unique:
                    tempstring += (', Unique:%s' % ('ORIG_DESC' in Child_Desc))
                if Print_Py_ID:
                    tempstring += ', Py_ID:%s' % id(Child)
                if Print_Py_Type:
                    tempstring += ', Py_Type:%s' % Child_Type.Py_Type
                if Print_Size and 'SIZE' in Child_Desc:
                    tempstring += ', Size:%s' % self.Get_Size('CHILD')
                if Print_Name and 'NAME' in Child_Desc:
                    tempstring += ', %s' % Child_Desc['NAME']
                
                if Print_Value:
                    if isinstance(Child, float) and isinstance(Precision, int):
                        tempstring2 += ', %s' %("{:."+str(Precision)+"f}")\
                                       .format(round(Child,Precision))
                    elif Child_Type.Is_Raw and not Print_Raw:
                        tempstring2 += ', ' + RAWDATA
                    else:
                        tempstring2 += ', %s' % Child

                if Printout:
                    try:
                        print(Tag_String+(tempstring+tempstring2)\
                              .replace(',','',1) + ' ]')
                    except Exception:
                        print(Tag_String + tempstring.replace(',','',1)+
                              ', %s ]' % UNPRINTABLE)
                    Tag_String = ''
                else:
                    Tag_String += ((tempstring+tempstring2)\
                                  .replace(',','',1) + ' ]\n')
                    
            Tag_String += Indent_Str1 + ']'
                    
        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''

        if Print_Ram_Size:
            if not Printout:
                Tag_String += '\n'
            Block_Size = self.__sizeof__()
            Tag_String += (Indent_Str0 + '"In-Memory Tag Block" is %s bytes'
                           % Block_Size)
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''
            
        if Print_Bin_Size:
            if not Printout:
                Tag_String += '\n'
            Block_Bin_Size = self.Bin_Size
            Tag_String += (Indent_Str0 + '"Packed Structure" is %s bytes'
                           % Block_Bin_Size)

            if Print_Ram_Size:
                X_Larger = "∞"
                if Block_Bin_Size:
                    Size_Str = "{:." + str(Precision) + "f}"
                    X_Larger = Block_Size/Block_Bin_Size
                    
                    if Precision:
                        X_Larger = Size_Str.format(round(X_Larger, Precision))
                    
                Tag_String += ('\n'+Indent_Str0 + '"In-Memory Tag Block" is ' +
                               str(X_Larger) + " times as large.")
        
        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        else:
            return Tag_String


    
    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''
        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None
            
        Dup_Block = type(self)(_OGA(self,'DESC'), Init_Data=self, Parent=Parent)

        if hasattr(self, 'CHILD'):
            _OSA(Dup_Block, 'CHILD', _OGA(self, 'CHILD'))
        
        return Dup_Block

    
    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the same descriptor.'''
        
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None

        #make a new block object sharing the same descriptor.
        #make sure the attributes arent initialized. it'll just waste time.
        memo[id(self)] = Dup_Block = type(self)(_OGA(self,'DESC'),
                                                Parent=Parent, Init_Attrs=False)

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

    
    def __sizeof__(self, Seen_Set=None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _LSO(self)
                
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
                
            Desc = _OGA(self,'DESC')
            if not Desc['TYPE'].Is_Array:
                Type = Desc[Index]['TYPE']
                if Type.Is_Var_Size and Type.Is_Data:
                    #try to set the size of the attribute
                    try:   self.Set_Size(None, Index)
                    except NotImplementedError: pass
                    except AttributeError: pass
                
        elif isinstance(Index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            start, stop, step = Index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step
            
            assert hasattr(New_Value, '__iter__'), ("must assign iterable "+
                                                    "to extended slice")
                
            Slice_Size = (stop-start)//step
            
            if step != -1 and Slice_Size > len(New_Value):
                raise ValueError("attempt to assign sequence of size "+
                                 "%s to extended slice of size %s" %
                                 (len(New_Value), Slice_Size))
            
            _LSI(self, Index, New_Value)
            try: self.Set_Size(Slice_Size-len(New_Value), None, '-')
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
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                self.Set_Size(1, None, '-')
            else:
                #set the size of the block to 0 since it's being deleted
                try:   self.Set_Size(0, Index)
                except NotImplementedError: pass
                except AttributeError: pass
                
                self.Del_Desc(Index)
                
            _LDI(self, Index)
                
        elif isinstance(Index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            start, stop, step = Index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step
            
            if _OGA(self,'DESC')['TYPE'].Is_Array:
                self.Set_Size((stop-start)//step, None, '-')
                _LDI(self, Index)
            else: 
                for i in range(start-1, stop-1, step):
                    #set the size of the block to 0 since it's being deleted
                    try:   self.Set_Size(0, i)
                    except NotImplementedError: pass
                    except AttributeError: pass
                    
                    self.Del_Desc(i)
                    _LDI(self, i)
        else:
            self.__delattr__(Index)


    def _Bin_Size(self, Block, Sub_Struct=False):
        '''Does NOT protect against recursion'''
        Size = 0
        if isinstance(Block, Tag_Block):
            Type = _OGA(Block, 'DESC')['TYPE']
            if Type.Name == 'Void':
                return 0
            
            if Type.Is_Struct:
                if Type.Is_Bit_Based:
                    #return the size of this bit_struct
                    #since the block contains no substructs
                    if Sub_Struct:
                        return 0
                    return Block.Get_Size()
                elif not Sub_Struct:
                    #get the size of this structure if it's not a substruct
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

        Desc = _OGA(self,'DESC')

        try:
            '''if this block is an array and "New_Attr" is None
            then it means to append a new block to the array'''
            if New_Attr is None and Desc['TYPE'].Is_Array:
                Attr_Desc = Desc['SUB_STRUCT']
                Attr_Type = Attr_Desc['TYPE']

                '''if the type of the default object is a type of Tag_Block
                then we can create one and just append it to the array'''
                if issubclass(Attr_Type.Py_Type, Tag_Block):
                    Attr_Type.Reader(Attr_Desc, self, None, Index)

                    self.Set_Size(1, None, '+')
                    #finished, so return
                    return
        except Exception:
            _LDI(self, Index)
            raise

        #if the New_Attr has its own descriptor,
        #use that instead of any provided one
        try:
            New_Desc = New_Attr.DESC
        except Exception:
            pass
            
        if New_Desc is None and not Desc['TYPE'].Is_Array:
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
            if not Desc['TYPE'].Is_Array:
                self.Ins_Desc(Index, New_Desc)
        except Exception:
            _LDI(self, Index)
            raise

        if Desc['TYPE'].Is_Array:
            #increment the size of the array by 1
            self.Set_Size(1, None, '+')
        elif Desc['TYPE'].Is_Struct:
            #increment the size of the struct
            #by the size of the new attribute
            self.Set_Size(self.Get_Size(Index), None, '+')

        #if the object being placed in the List_Block
        #has a 'PARENT' attribute, set this block to it
        try:
            _OSA(New_Attr, 'PARENT', self)
        except Exception:
            pass

            

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
            for i in range(Desc['ENTRIES']):
                self.append(New_Attrs[i], Desc[i])
        elif _OGA(self,'DESC')['TYPE'].Is_Array and isinstance(New_Attrs, int):
            #if this block is an array and "New_Attr" is an int it means
            #that we are supposed to append this many of the SUB_STRUCT
            for i in range(New_Attrs):
                self.append()
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of List_Block or int, not %s" %
                            type(New_Attrs))



    def insert(self, Index, New_Attr=None, New_Desc=None):
        '''Allows inserting objects into this List_Block while
        taking care of all descriptor related details.
        Function may be called with only "Index" if this block type is a Array.
        Doing so will insert a fresh structure to the array at "Index"
        (as defined by the Array's SUB_STRUCT descriptor value)'''

        #create a new, empty index
        _LIns(self, Index, None)
        Desc = _OGA(self,'DESC')

        '''if this block is an array and "New_Attr" is None
        then it means to append a new block to the array'''
        if Desc['TYPE'].Is_Array:
            New_Desc = Desc['SUB_STRUCT']
            New_Type = New_Desc['TYPE']

            '''if the type of the default object is a type of Tag_Block
            then we can create one and just append it to the array'''
            if New_Attr is None and issubclass(New_Type.Py_Type, Tag_Block):
                New_Type.Reader(New_Desc, self, None, Index)

                self.Set_Size(1, None, '+')
                #finished, so return
                return

        #if the New_Attr has its own descriptor,
        #use that instead of any provided one
        try:
            New_Desc = New_Attr.DESC
        except Exception:
            pass
            
        if New_Desc is None:
            _LDI(self, Index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(New_Attr)) + "\nCannot insert " +
                                 "without a descriptor for the new item.")

        '''try and insert the new descriptor
        and set the new attribute value,
        raise the last error if it fails'''
        try:
            _LSI(self, Index, New_Attr)
            if not Desc['TYPE'].Is_Array:
                self.Ins_Desc(Index, New_Desc)
        except Exception:
            _LDI(self, Index)
            raise

        #increment the size of the array by 1
        if Desc['TYPE'].Is_Array:
            self.Set_Size(1, None, '+')

        #if the object being placed in the List_Block
        #has a 'PARENT' attribute, set this block to it
        try:
            _OSA(New_Attr, 'PARENT', self)
        except Exception:
            pass


    def pop(self, Index=-1):
        '''Pops the attribute at 'Index' out of the List_Block
        and returns a tuple containing it and its descriptor.'''
        
        Desc = _OGA(self, "DESC")
        
        if isinstance(Index, int):
            if Index < 0:
                Index += len(self)
            Attr = _LPop(self, Index)
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if Desc['TYPE'].Is_Array:
                Desc = Desc['SUB_STRUCT']
                self.Set_Size(1, None, '-')
            else:
                Desc = self.Get_Desc(Index)
                self.Del_Desc(Index)
        elif Index in Desc['NAME_MAP']:
            Attr = _LPop(self, Desc['NAME_MAP'][Index])
            Desc = self.Get_Desc(Index)
            self.Del_Desc(Index)
        elif 'NAME' in Desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'"
                                 % (Desc['NAME'], type(self), Index))
        else:
            raise AttributeError("'%s' has no attribute '%s'"
                                 %(type(self), Index))
            
        return(Attr, Desc)


    def Get_Size(self, Attr_Index=None, **kwargs):
        '''Returns the size of self[Attr_Index] or self if Attr_Index == None.
        Size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''
        Desc = _OGA(self,'DESC')

        if isinstance(Attr_Index, int):
            Block = self[Attr_Index]
            if Desc['TYPE'].Is_Array:
                Desc = Desc['SUB_STRUCT']
            else:
                Desc = Desc[Attr_Index]
        elif isinstance(Attr_Index, str):
            Block = self.__getattr__(Attr_Index)
            try:
                Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
            except Exception:
                Desc = Desc[Attr_Index]
        else:
            Block = self
            

        #determine how to get the size
        if 'SIZE' in Desc:
            Size = Desc['SIZE']
            
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
                return Size(Attr_Index=Attr_Index, Parent=Parent,
                            Block=Block, **kwargs)
            else:
                Block_Name = _OGA(self,'DESC')['NAME']
                if isinstance(Attr_Index, (int,str)):
                    Block_Name = Attr_Index
                raise TypeError(("Size specified in '%s' is not a valid type."+
                                 "\nExpected int, str, or function. Got %s.") %
                                (Block_Name, type(Size)) )
        #use the size calculation routine of the Field_Type
        return Desc['TYPE'].Size_Calc(Block)



    def Set_Size(self, New_Value=None, Attr_Index=None, Op=None, **kwargs):
        '''Sets the size of self[Attr_Index] or self if Attr_Index == None.
        Size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''
        
        Desc = _OGA(self,'DESC')
        
        if isinstance(Attr_Index, int):
            Block = self[Attr_Index]
            if Desc['TYPE'].Is_Array:
                Size = Desc['SUB_STRUCT'].get('SIZE')
            else:
                Size = Desc[Attr_Index].get('SIZE')
            Type = self.Get_Desc(TYPE, Attr_Index)
        elif isinstance(Attr_Index, str):
            Block = self.__getattr__(Attr_Index)

            ErrorNo = 0
            #try to get the size directly from the block
            try:
                #do it in this order so Desc doesnt get
                #overwritten if SIZE can't be found in Desc
                Size = Block.DESC['SIZE']
                Desc = Block.DESC
            except Exception:
                #if that fails, try to get it from the descriptor of the parent
                try:
                    Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
                except Exception:
                    Desc = Desc[Attr_Index]

                try:
                    Size = Desc['SIZE']
                except Exception:
                    #its parent cant tell us the size, raise this error
                    ErrorNo = 1
                    if 'TYPE' in Desc and not Desc['TYPE'].Is_Var_Size:
                        #the size is not variable so it cant be set
                        #without changing the type. raise this error
                        ErrorNo = 2
            
            Block_Name = Desc.get('NAME')
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            if ErrorNo == 1:
                raise AttributeError(("Could not determine size for "+
                                      "attribute '%s' in block '%s'.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME']))
            elif ErrorNo == 2:
                raise AttributeError(("Can not set size for attribute '%s' "+
                                      "in block '%s'.\n'%s' has a fixed size "+
                                      "of '%s'.\nTo change the size of '%s' "+
                                      "you must change its data type.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME'],
                                   Desc['TYPE'], Desc['TYPE'].Size, Block_Name))
            Type = Desc['TYPE']
        else:
            Block = self
            Size = Desc.get('SIZE')
            Type = Desc['TYPE']

        #raise exception if the Size is None
        if Size is None:
            Block_Name = Desc['NAME']
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            raise AttributeError("'SIZE' does not exist in '%s'." % Block_Name)

        #if a new size wasnt provided then it needs to be calculated
        if New_Value is None:
            Op = None
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
        
            New_Size = Type.Size_Calc(Parent=Parent, Block=Block,
                                      Attr_Index=Attr_Index)
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

            #if the size if being automatically set and it SHOULD
            #be a fixed size, then try to raise a UserWarning
            '''Enable this code when necessary'''
            #if kwargs.get('Warn', True):
            #    raise UserWarning('Cannot change a fixed size.')
            
            if Op is None:
                self.Set_Desc('SIZE', New_Size, Attr_Index)
            elif Op == '+':
                self.Set_Desc('SIZE', Size+New_Size, Attr_Index)
            elif Op == '-':
                self.Set_Desc('SIZE', Size-New_Size, Attr_Index)
            elif Op == '*':
                self.Set_Desc('SIZE', Size*New_Size, Attr_Index)
            elif Op == '/':
                self.Set_Desc('SIZE', Size//New_Size, Attr_Index)
            else:
                raise TypeError(("Unknown operator type '%s' " +
                                 "for setting 'Size'.") % Op)
        elif isinstance(Size, str):
            '''set size by traversing the tag structure
            along the path specified by the string'''
            self.Set_Neighbor(Size, New_Size, Block, Op)
        elif hasattr(Size, "__call__"):
            '''set size by calling the provided function'''
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
            
            Size(Attr_Index=Attr_Index, New_Value=New_Size,
                 Op=Op, Parent=Parent, Block=Block, **kwargs)
        else:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            
            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (Block_Name, type(Size)) +
                            "Cannot determine how to set the size." )


    def Collect_Pointers(self, Offset=0, Seen=None, Pointed_Blocks=None,
                         Sub_Struct=False, Root=False, Attr_Index=None):
        '''docstring'''
        if Seen is None:
            Seen = set()
            
        if Attr_Index is None:
            Desc = _OGA(self,'DESC')
            Block = self
        else:
            Desc = self.Get_Desc(Attr_Index)
            Block = self.__getitem__(Attr_Index)
            
        if id(Block) in Seen:
            return Offset

        if 'POINTER' in Desc:
            Pointer = Desc['POINTER']
            if isinstance(Pointer, int) and Desc.get('CARRY_OFF', True):
                #if the next blocks are to be located directly after
                #this one then set the current offset to its location
                Offset = Pointer

            #if this is a block within the root block
            if not Root:
                Pointed_Blocks.append((self, Attr_Index, Sub_Struct))
                return Offset

        Is_Tag_Block = isinstance(Block, Tag_Block)

        if Is_Tag_Block:
            Seen.add(id(Block))

        Type = Desc['TYPE']
        if Type.Is_Array:
            Block_Desc = Desc['SUB_STRUCT']
            
            #align the start of the array of structs
            Align = Desc.get('ALIGN', 1)
            Offset += (Align-(Offset%Align))%Align
            
            #dont align within the array of structs
            Align = None
        elif Desc.get('ALIGN'):
            Align = Desc['ALIGN']
            Offset += (Align-(Offset%Align))%Align
            
        #increment the offset by this blocks size if it isn't a substruct
        if not Sub_Struct and (Type.Is_Struct or Type.Is_Data):
            Offset += self.Get_Size(Attr_Index)
            Sub_Struct = True

        '''If the block isn't a Tag_Block it means that this is being run
        on a non-Tag_Block that happens to have its location specified by
        pointer. The offset must still be incremented by the size of this
        block, but the block can't contain other blocks, so return early.'''
        if not Is_Tag_Block:
            return Offset
            
        if hasattr(self, 'CHILD'):
            Indexes = list(range(len(self)))
            Indexes.append('CHILD')
        else:
            Indexes = range(len(self))

        Align = 0
        
        for i in Indexes:
            Block = self[i]
            if isinstance(Block, Tag_Block):
                #if "i" is an integer it means this object still
                #exists within the structure, or is "Sub_Struct".
                #If it isn't it means its a linked block, which
                #(as of writing this) means its a child block.
                Offset = Block.Collect_Pointers(Offset, Seen, Pointed_Blocks,
                                    (isinstance(i, int) and Sub_Struct), False)
            elif not Sub_Struct and isinstance(i, int):
                '''It's pointless to check if this block is in Seen
                or not because the block may be an integer, float,
                or string that is shared across multiple blocks.
                The check would succeed or fail at random.'''
                if not Type.Is_Array:
                    Block_Desc = Desc[i]
                    Align = Block_Desc.get('ALIGN')
                    
                Pointer = Block_Desc.get('POINTER')
                if Pointer is not None:
                    if not isinstance(Pointer, int):
                        #if the block has a variable pointer, add it to the
                        #list and break early so its id doesnt get added
                        Pointed_Blocks.append((self, i, Sub_Struct))
                        continue
                    elif Block_Desc.get('CARRY_OFF'):
                        Offset = Pointer
                elif Align:
                    #align the block
                    Offset += (Align-(Offset%Align))%Align
                    
                #add the size of the block to the current offset
                Offset += self.Get_Size(i)
                Seen.add(id(Block))
            
        return Offset



    def Read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An Init_Data
        can be provided with which to initialize the values of the block.'''

        Attr_Index = kwargs.get('Attr_Index',None)
        Init_Attrs = kwargs.get('Init_Attrs',True)
        Init_Data  = kwargs.get('Init_Data', None)

        #if an Init_Data was provided, make sure it can be used
        if (Init_Data is not None and
            not (hasattr(Init_Data, '__iter__') and
                 hasattr(Init_Data, '__len__'))):
            raise TypeError("Init_Data must be an iterable with a length")

        Raw_Data = self.Get_Raw_Data(**kwargs)
            
        Desc = _OGA(self, "DESC")
        if Attr_Index is not None and Raw_Data is not None:
            #if we are reading or initializing just one attribute
            if Attr_Index in Desc['NAME_MAP']:
                Attr_Index = self[Desc['NAME_MAP'][Name]]
            elif isinstance(Attr_Index, int) and Name in Desc:
                Attr_Index = Desc[Name]
            
            Desc = self.Get_Desc(Attr_Index)
        else:
            #if we are reading or initializing EVERY attribute

            #clear the block and set it to the right number of empty indices
            _LDI(self, slice(None, None, None))
                        
            if Desc['TYPE'].Is_Array:
                _LExt(self, [None]*self.Get_Size())
            else:
                _LExt(self, [None]*Desc['ENTRIES'])

            '''If the Init_Data is not None then try
            to use it to populate the List_Block'''
            if isinstance(Init_Data, dict):
                '''Since dict keys can be strings we assume that the
                reason a dict was provided is to set the attributes
                by name rather than index.
                So call self.__setattr__ instead of self.__setitem__'''
                for Name in Init_Data:
                    self.__setitem__(Name, Init_Data[Name])
            elif Init_Data is not None:
                '''loop over the List_Block and copy the entries
                from Init_Data into the List_Block. Make sure to
                loop as many times as the shortest length of the
                two so as to prevent IndexErrors.'''
                for i in range(min(len(self), len(Init_Data))):
                    self.__setitem__(i, Init_Data[i])
        

        if Raw_Data is not None:
            #build the structure from raw data
            try:
                #Figure out if the parent is this List_Block or its parent.
                if Attr_Index is None:
                    Parent = self
                else:
                    try:
                        Parent = self.PARENT
                    except AttributeError:
                        Parent = None
                
                Desc['TYPE'].Reader(Desc, Parent, Raw_Data, Attr_Index,
                                    kwargs.get('Root_Offset',0),
                                    kwargs.get('Offset',0),
                                    Test = kwargs.get('Test',False))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read List_Block from file')
                
        elif Init_Attrs:
            #initialize the attributes
            
            if Desc['TYPE'].Is_Array:
                '''This List_Block is an array, so the type of each
                element should be the same then initialize it'''
                try:
                    Attr_Desc = Desc['SUB_STRUCT']
                    Attr_Type = Attr_Desc['TYPE']
                    Py_Type = Attr_Type.Py_Type
                except Exception: 
                    raise TypeError("Could not locate the array element " +
                                    "descriptor.\nCould not initialize array")

                #loop through each element in the array and initialize it
                for i in range(len(self)):
                    if _LGI(self, i) is None:
                        Attr_Type.Reader(Attr_Desc, self, None, i)
            else:
                for i in range(len(self)):
                    '''Only initialize the attribute
                    if a value doesnt already exist'''
                    if _LGI(self, i) is None:
                        Block_Desc = Desc[i]
                        Block_Desc['TYPE'].Reader(Block_Desc, self, None, i)

            '''Only initialize the child if the block has a
            child and a value for it doesnt already exist.'''
            Child_Desc = Desc.get('CHILD')
            if Child_Desc and _OGA(self, 'CHILD') is None:
                Child_Desc['TYPE'].Reader(Child_Desc, self, None, 'CHILD')
        

class P_List_Block(List_Block):
    '''This List_Block allows a reference to the child
    block it describes to be stored as well as a
    reference to whatever block it is parented to'''
    __slots__ = ("DESC", 'PARENT', 'CHILD')
    
    def __init__(self, Desc, Child=None, Parent=None,**kwargs):
        '''docstring'''
        assert isinstance(Desc, dict) and ('TYPE' in Desc and 'NAME')
        assert 'CHILD' in Desc and 'NAME_MAP' in Desc and 'ENTRIES' in Desc
        
        _OSA(self, 'CHILD',  Child)
        _OSA(self, 'DESC',   Desc)
        _OSA(self, 'PARENT', Parent)
        
        self.Read(**kwargs)

    
    def __sizeof__(self, Seen_Set=None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _LSO(self)

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


    def __setattr__(self, Attr_Name, New_Value):
        '''docstring'''
        try:
            _OSA(self, Attr_Name, New_Value)
            if Attr_Name == 'CHILD':
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
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc['NAME_MAP']:
                self.__setitem__(Desc['NAME_MAP'][Attr_Name], New_Value)
            elif Attr_Name in Desc:
                self.Set_Desc(Attr_Name, New_Value)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (Desc.get('NAME',UNNAMED),
                                      type(self), Attr_Name))

    def __delattr__(self, Attr_Name):
        '''docstring'''
        try:
            _ODA(self, Attr_Name)
            if Attr_Name == 'CHILD':
                #set the size of the block to 0 since it's being deleted
                try:   self.Set_Size(0, 'CHILD')
                except NotImplementedError: pass
                except AttributeError: pass
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc['NAME_MAP']:
                #set the size of the block to 0 since it's being deleted
                try:   self.Set_Size(0, Attr_Name=Attr_Name)
                except NotImplementedError: pass
                except AttributeError: pass
                self.Del_Desc(Attr_Name)
                _LDI(self, Desc['NAME_MAP'][Attr_Name])
            elif Attr_Name in Desc:
                self.Del_Desc(Attr_Name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME',UNNAMED),
                                     type(self),Attr_Name))

    

class While_List_Block(List_Block):
    '''docstring'''
    __slots__ = ('DESC', 'PARENT')

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
                
        elif isinstance(Index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            start, stop, step = Index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step
            
            assert hasattr(New_Value, '__iter__'), ("must assign iterable "+
                                                    "to extended slice")
                
            Slice_Size = (stop-start)//step
            
            if step != -1 and Slice_Size > len(New_Value):
                raise ValueError("attempt to assign sequence of size "+
                                 "%s to extended slice of size %s" %
                                 (len(New_Value), Slice_Size))
            
            _LSI(self, Index, New_Value)
        else:
            self.__setattr__(Index, New_Value)


    def __delitem__(self, Index):
        '''enables deleting attributes by providing
        the attribute name string as an index'''
        if isinstance(Index, str):
            self.__delattr__(Index)
        else:
            if Index < 0:
                Index += len(self)
            _LDI(self, Index)
            

    def append(self, New_Attr=None, New_Desc=None):
        '''Allows appending objects to this Tag_Block while taking
        care of all descriptor related details.
        Function may be called with no arguments if this block type is
        an Array. Doing so will append a fresh structure to the array
        (as defined by the Array's SUB_STRUCT descriptor value).'''

        #create a new, empty index
        _LApp(self, None)

        try:
            Desc = _OGA(self,'DESC')

            '''if this block is an array and "New_Attr" is None
            then it means to append a new block to the array'''
            if New_Attr is None:
                Attr_Desc = Desc['SUB_STRUCT']
                Attr_Type = Attr_Desc['TYPE']

                '''if the type of the default object is a type of Tag_Block
                then we can create one and just append it to the array'''
                if issubclass(Attr_Type.Py_Type, Tag_Block):
                    Attr_Type.Reader(Attr_Desc, self, None, len(self)-1)
                    return
        
            _LSI(self, -1, New_Attr)
        except Exception:
            _LDI(self, -1)
            raise
        try:
            _OSA(New_Attr, 'PARENT', self)
        except Exception:
            pass
            

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
            for i in range(len(List_Block)):
                self.append(New_Attrs[i], Desc[i])
        elif isinstance(New_Attrs, int):
            #if this block is an array and "New_Attr" is an int it means
            #that we are supposed to append this many of the SUB_STRUCT
            for i in range(New_Attrs):
                self.append()
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of List_Block or int, not %s" %
                            type(New_Attrs))


    def insert(self, Index, New_Attr=None, New_Desc=None):
        '''Allows inserting objects into this List_Block while
        taking care of all descriptor related details.
        Function may be called with only "Index" if this block type is a Array.
        Doing so will insert a fresh structure to the array at "Index"
        (as defined by the Array's SUB_STRUCT descriptor value)'''

        #create a new, empty index
        _LIns(self, Index, None)

        New_Desc = _OGA(self,'DESC')['SUB_STRUCT']
        New_Type = New_Desc['TYPE']

        try:
            '''if the type of the default object is a type of Tag_Block
            then we can create one and just append it to the array'''
            if New_Attr is None and issubclass(New_Type.Py_Type, Tag_Block):
                New_Type.Reader(New_Desc, self, None, Index)
                #finished, so return
                return
        except Exception:
            _LDI(self, Index)
            raise

        #if the New_Attr has its own descriptor,
        #use that instead of any provided one
        try:
            New_Desc = New_Attr.DESC
        except Exception:
            pass
            
        if New_Desc is None:
            _LDI(self, Index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(New_Attr)) + "\nCannot insert " +
                                 "without a descriptor for the new item.")
        try:
            _LSI(self, Index, New_Attr)
        except Exception:
            _LDI(self, Index)
            raise
        try:
            _OSA(New_Attr, 'PARENT', self)
        except Exception:
            pass


    def pop(self, Index=-1):
        '''Pops the attribute at 'Index' out of the List_Block
        and returns a tuple containing it and its descriptor.'''
        
        Desc = _OGA(self, "DESC")
        
        if isinstance(Index, int):
            if Index < 0:
                return (_LPop(self, Index + len(self)), Desc['SUB_STRUCT'])
            return (_LPop(self, Index), Desc['SUB_STRUCT'])
        elif 'NAME' in Desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'"
                                 % (Desc['NAME'], type(self), Index))
        else:
            raise AttributeError("'%s' has no attribute '%s'"
                                 %(type(self), Index))
            
        return(Attr, Desc)


    def Get_Size(self, Attr_Index=None, **kwargs):
        '''Returns the size of self[Attr_Index] or self if Attr_Index == None.
        Size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''

        if isinstance(Attr_Index, int):
            Desc = _OGA(self,'DESC')
            Block = self[Attr_Index]
            Desc = Desc['SUB_STRUCT']
        elif isinstance(Attr_Index, str):
            Desc = _OGA(self,'DESC')
            Block = self.__getattr__(Attr_Index)
            try:
                Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
            except Exception:
                Desc = Desc[Attr_Index]
        else:
            return len(self)
            

        #determine how to get the size
        if 'SIZE' in Desc:
            Size = Desc['SIZE']
            
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
                    
                return Size(Attr_Index=Attr_Index, Parent=Parent,
                            Block=Block, **kwargs)
            else:
                Block_Name = _OGA(self,'DESC')['NAME']
                if isinstance(Attr_Index, (int,str)):
                    Block_Name = Attr_Index
                raise TypeError(("Size specified in '%s' is not a valid type."+
                                 "\nExpected int, str, or function. Got %s.") %
                                (Block_Name, type(Size)) )
        #use the size calculation routine of the Field_Type
        return Desc['TYPE'].Size_Calc(Block)



    def Set_Size(self, New_Value=None, Attr_Index=None, Op=None, **kwargs):
        '''Sets the size of self[Attr_Index] or self if Attr_Index == None.
        Size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''
        
        Desc = _OGA(self,'DESC')
        
        if isinstance(Attr_Index, int):
            Block = self[Attr_Index]
            Size = Desc['SUB_STRUCT'].get('SIZE')
            Type = self.Get_Desc(TYPE, Attr_Index)
        elif isinstance(Attr_Index, str):
            Block = self.__getattr__(Attr_Index)

            ErrorNo = 0
            #try to get the size directly from the block
            try:
                #do it in this order so Desc doesnt get
                #overwritten if SIZE can't be found in Desc
                Size = Block.DESC['SIZE']
                Desc = Block.DESC
            except Exception:
                #if that fails, try to get it from the descriptor of the parent
                try:
                    Desc = Desc[Desc['NAME_MAP'][Attr_Index]]
                except Exception:
                    Desc = Desc[Attr_Index]

                try:
                    Size = Desc['SIZE']
                except Exception:
                    #its parent cant tell us the size, raise this error
                    ErrorNo = 1
                    if 'TYPE' in Desc and not Desc['TYPE'].Is_Var_Size:
                        #the size is not variable so it cant be set
                        #without changing the type. raise this error
                        ErrorNo = 2
            
            Block_Name = Desc.get('NAME')
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            if ErrorNo == 1:
                raise AttributeError(("Could not determine size for "+
                                      "attribute '%s' in block '%s'.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME']))
            elif ErrorNo == 2:
                raise AttributeError(("Can not set size for attribute '%s' "+
                                      "in block '%s'.\n'%s' has a fixed size "+
                                      "of '%s'.\nTo change the size of '%s' "+
                                      "you must change its data type.") %
                                     (Block_Name, _OGA(self,'DESC')['NAME'],
                                   Desc['TYPE'], Desc['TYPE'].Size, Block_Name))
            Type = Desc['TYPE']
        else:
            #cant set size of While_Arrays
            return

        #raise exception if the Size is None
        if Size is None:
            Block_Name = Desc['NAME']
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            raise AttributeError("'SIZE' does not exist in '%s'." % Block_Name)

        #if a new size wasnt provided then it needs to be calculated
        if New_Value is None:
            Op = None
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
        
            New_Size = Type.Size_Calc(Parent=Parent, Block=Block,
                                      Attr_Index=Attr_Index)
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

            #if the size if being automatically set and it SHOULD
            #be a fixed size, then try to raise a UserWarning
            '''Enable this code when necessary'''
            #if kwargs.get('Warn', True):
            #    raise UserWarning('Cannot change a fixed size.')
            
            if Op is None:
                self.Set_Desc('SIZE', New_Size, Attr_Index)
            elif Op == '+':
                self.Set_Desc('SIZE', Size+New_Size, Attr_Index)
            elif Op == '-':
                self.Set_Desc('SIZE', Size-New_Size, Attr_Index)
            elif Op == '*':
                self.Set_Desc('SIZE', Size*New_Size, Attr_Index)
            elif Op == '/':
                self.Set_Desc('SIZE', Size//New_Size, Attr_Index)
            else:
                raise TypeError(("Unknown operator type '%s' " +
                                 "for setting 'Size'.") % Op)
        elif isinstance(Size, str):
            '''set size by traversing the tag structure
            along the path specified by the string'''
            self.Set_Neighbor(Size, New_Size, Block, Op)
        elif hasattr(Size, "__call__"):
            '''set size by calling the provided function'''
            if hasattr(Block, 'PARENT'):
                Parent = Block.PARENT
            else:
                Parent = self
            
            Size(Attr_Index=Attr_Index, New_Value=New_Size,
                 Op=Op, Parent=Parent, Block=Block, **kwargs)
        else:
            Block_Name = _OGA(self,'DESC')['NAME']
            if isinstance(Attr_Index, (int,str)):
                Block_Name = Attr_Index
            
            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (Block_Name, type(Size)) +
                            "Cannot determine how to set the size." )


    def Read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An Init_Data
        can be provided with which to initialize the values of the block.'''

        Attr_Index = kwargs.get('Attr_Index',None)
        Init_Attrs = kwargs.get('Init_Attrs',True)
        Init_Data  = kwargs.get('Init_Data', None)

        #if an Init_Data was provided, make sure it can be used
        if (Init_Data is not None and
            not (hasattr(Init_Data, '__iter__') and
                 hasattr(Init_Data, '__len__'))):
            raise TypeError("Init_Data must be an iterable with a length")
        
        Raw_Data = self.Get_Raw_Data(**kwargs)
            
        Desc = _OGA(self, "DESC")
        if Attr_Index is not None and Raw_Data is not None:
            #if we are reading or initializing just one attribute
            if Attr_Index in Desc['NAME_MAP']:
                Attr_Index = self[Desc['NAME_MAP'][Name]]
            elif isinstance(Attr_Index, int) and Name in Desc:
                Attr_Index = Desc[Name]
            
            Desc = self.Get_Desc(Attr_Index)
        else:
            #if we are reading or initializing EVERY attribute
            _LDI(self, slice(None, None, None))

            '''If the Init_Data is not None then try
            to use it to populate the List_Block'''
            if Init_Data is not None:
                _LExt(self, [None]*len(Init_Data[i]))
                for i in range(len(Init_Data)):
                    self.__setitem__(i, Init_Data[i])
        

        #initialize the attributes
        if Raw_Data is not None:
            #build the structure from raw data
            try:
                #Figure out if the parent is this List_Block or its parent.
                if Attr_Index is None:
                    Parent = self
                else:
                    try:
                        Parent = self.PARENT
                    except AttributeError:
                        Parent = None
                
                Desc['TYPE'].Reader(Desc, Parent, Raw_Data, Attr_Index,
                                    kwargs.get('Root_Offset',0),
                                    kwargs.get('Offset',0),
                                    Test = kwargs.get('Test',False))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read %s from file' % type(self))
                
        elif Init_Attrs:
            '''This List_Block is an array, so the type of each
            element should be the same then initialize it'''
            try:
                Attr_Desc = Desc['SUB_STRUCT']
                Attr_Type = Attr_Desc['TYPE']
            except Exception: 
                raise TypeError("Could not locate the array element " +
                                "descriptor.\nCould not initialize array")

            #loop through each element in the array and initialize it
            for i in range(len(self)):
                if _LGI(self, i) is None:
                    Attr_Type.Reader(Attr_Desc, self, None, i)

            '''Only initialize the child if the block has a
            child and a value for it doesnt already exist.'''
            Child_Desc = Desc.get('CHILD')
            if Child_Desc and _OGA(self, 'CHILD') is None:
                Child_Desc['TYPE'].Reader(Child_Desc, self, None, 'CHILD')



class P_While_List_Block(While_List_Block):
    '''docstring'''
    __slots__ = ('DESC', 'PARENT', 'CHILD')
    
    def __init__(self, Desc, Child=None, Parent=None,**kwargs):
        '''docstring'''
        assert isinstance(Desc, dict) and ('TYPE' in Desc and 'NAME')
        assert 'CHILD' in Desc and 'NAME_MAP' in Desc and 'ENTRIES' in Desc
        
        _OSA(self, 'CHILD',  Child)
        _OSA(self, 'DESC',   Desc)
        _OSA(self, 'PARENT', Parent)
        
        self.Read(**kwargs)
    
    def __sizeof__(self, Seen_Set=None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _LSO(self)

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
                Bytes_Total += item.__sizeof__(Seen_Set)
            
        return Bytes_Total


    def __setattr__(self, Attr_Name, New_Value):
        '''docstring'''
        try:
            _OSA(self, Attr_Name, New_Value)
            if Attr_Name == 'CHILD':
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
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc:
                self.Set_Desc(Attr_Name, New_Value)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (Desc.get('NAME',UNNAMED),
                                      type(self), Attr_Name))

    def __delattr__(self, Attr_Name):
        '''docstring'''
        try:
            _ODA(self, Attr_Name)
            if Attr_Name == 'CHILD':
                #set the size of the block to 0 since it's being deleted
                try:   self.Set_Size(0, 'CHILD')
                except NotImplementedError: pass
                except AttributeError: pass
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Attr_Name in Desc:
                self.Del_Desc(Attr_Name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME',UNNAMED),
                                     type(self),Attr_Name))
    

class Data_Block(Tag_Block):
    '''Does not allow specifying a size as anything other than an
    int literal in the descriptor/Field_Type. Specifying size as
    a string path or a function was deemed to be unlikely to ever
    be required and is faster without having to acount for it.'''
    
    __slots__ = ("DESC", "PARENT", "Data")

    def __init__(self, Desc, Parent=None, **kwargs):
        '''docstring'''
        assert isinstance(Desc, dict) and ('TYPE' in Desc and 'NAME')
        
        _OSA(self, "DESC",   Desc)
        _OSA(self, 'PARENT', Parent)

        self.Data = Desc['TYPE'].Data_Type()
        
        if kwargs:
            self.Read(**kwargs)
    

    def __str__(self, **kwargs):
        '''docstring'''
        Printout = kwargs.get('Printout', False)
        Show = kwargs.get('Show', Def_Show)
        if isinstance(Show, str):
            Show = set([Show])
        else:
            Show = set(Show)
            
        kwargs['Printout'] = False
        Tag_String = Tag_Block.__str__(self, **kwargs)[:-2]
        
        if "Value" in Show or 'All' in Show:
            Tag_String += ', %s' % self.Data
            
        #remove the first comma
        Tag_String = Tag_String.replace(',','',1) + ' ]'
        
        if Printout:
            print(Tag_String)
            return ''
        return Tag_String



    def __sizeof__(self, Seen_Set=None):
        '''docstring'''
        if Seen_Set is None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0

        Seen_Set.add(id(self))
        Bytes_Total = _OSO(self) + getsizeof(self.Data)
        
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
            
        return Bytes_Total
    

    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''
        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None
        return type(self)(_OGA(self,'DESC'), Parent=Parent, Init_Data=self.Data)

    
    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the same descriptor.'''
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        #if there is a parent, use it
        try:
            Parent = _OGA(self,'PARENT')
        except AttributeError:
            Parent = None

        #make a new block object sharing the same descriptor.
        Dup_Block = type(self)(_OGA(self,'DESC'), Parent=Parent,
                               Init_Data=self.Data)
        memo[id(self)] = Dup_Block
        
        return Dup_Block
       

    def _Bin_Size(self, Block, Sub_Struct=False):
        '''Returns the size of this Bool_Block.
        This size is how many bytes it would take up if written to a buffer.'''
        if Sub_Struct:
            return 0
        return self.Get_Size()

    @property
    def Bin_Size(self):
        '''Returns the size of this Bool_Block.
        This size is how many bytes it would take up if written to a buffer.'''
        return self.Get_Size()

        
    def Get_Size(self, Attr_Index=None, **kwargs):
        '''docstring'''
        Desc = _OGA(self,'DESC')

        #determine how to get the size
        if 'SIZE' in Desc:
            Size = Desc['SIZE']
            '''It's faster to try to add zero to Size and return it than
            to try and check if it's an int using isinstance(Size, int)'''
            try:
                return Size+0
            except TypeError:
                raise TypeError(("Size specified in '%s' is not a valid type. "+
                             "Expected int, got %s.")%(Desc['NAME'],type(Size)))
        #use the size calculation routine of the Field_Type
        return Desc['TYPE'].Size_Calc(self)
    

    def Set_Size(self, New_Value=None, **kwargs):
        '''docstring.'''
        Desc = _OGA(self,'DESC')
        Size = Desc.get('SIZE')

        #raise exception if the Size is None
        if Size is None:
            raise AttributeError("'SIZE' does not exist in '%s'." %Desc['NAME'])

        #if a new size wasnt provided then it needs to be calculated
        if New_Value is None:
            New_Size = Desc['TYPE'].Size_Calc(Block=self.Data)
        else:
            New_Size = New_Value

        '''It's faster to try to add zero to Size and return it than
        to try and check if it's an int using isinstance(Size, int)'''
        try:
            '''Because literal descriptor sizes are supposed to be
            static(unless you're changing the structure), we don't change
            the size if the new size is less than the current one.'''
            if New_Size <= Size+0 and New_Value is None:
                return
        except TypeError:
            raise TypeError(("Size specified in '%s' is not a valid type." +
                            "Expected int, got %s.")%(Desc['NAME'],type(Size))+
                            "\nCannot determine how to set the size." )
        
        self.Set_Desc('SIZE', New_Size)


    def Read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and add in ones that dont exist. An Init_Data
        can be provided with which to initialize the values of the block.'''

        Init_Data = kwargs.get('Init_Data', None)
        
        Raw_Data = self.Get_Raw_Data(**kwargs)
            
        Desc = _OGA(self, "DESC")
        if Init_Data is not None:
            try:
                self.Data = Desc.get('TYPE').Data_Type(Init_Data)
            except ValueError:
                Data_Type = Desc.get('TYPE').Data_Type
                raise ValueError("'Init_Data' must be a value able to be "+
                                 "cast to a %s. Got %s" % (Data_Type,Init_Data))
            except TypeError:
                Data_Type = Desc.get('TYPE').Data_Type
                raise ValueError("Invalid type for 'Init_Data'. Must be a "+
                                 "%s, not %s" % (Data_Type, type(Init_Data)))
        elif Raw_Data is not None:
            if not(hasattr(Raw_Data, 'read') and hasattr(Raw_Data, 'seek')):
                raise TypeError(('Cannot build %s without either an input ' +
                                 'path or a readable buffer') % type(self))
            #build the block from raw data
            try:
                try:
                    Parent = _OGA(self, "PARENT")
                except AttributeError:
                    Parent = None
                    
                Desc['TYPE'].Reader(Desc, Parent, Raw_Data, None,
                                    kwargs.get('Root_Offset', 0),
                                    kwargs.get('Offset', 0) )
            except Exception:
                raise IOError('Error occurred while trying to read '+
                              '%s from file.' % type(self))
        else:
            #Initialize self.Data to its default value
            self.Data = Desc.get('DEFAULT', Desc.get('TYPE').Data_Type())


class Bool_Block(Data_Block):
    
    __slots__ = ("DESC", "PARENT", "Data")

    def __str__(self, **kwargs):
        '''docstring'''
        
        Printout = kwargs.get('Printout', False)
        Show = kwargs.get('Show', Def_Show)
        if isinstance(Show, str):
            Show = set([Show])
        else:
            Show = set(Show)
            
        #if the list includes 'All' it means to show everything
        if 'All' in Show:
            Show.update(All_Show)

        #used to display different levels of indention
        Indent_Str = (' '*kwargs.get('Indent', BLOCK_PRINT_INDENT)*
                         (kwargs.get('Level',0)+1))
        
        Desc = _OGA(self,'DESC')

        #build the main part of the string
        kwargs['Printout'] = False
        Tag_String = Data_Block.__str__(self, **kwargs)[:-2]
        
        if "Flags" in Show:
            if Printout:
                if Tag_String:
                    print(Tag_String)
                Tag_String = ''
            else:
                Tag_String += '\n'

            N_Spc, M_Spc, Name, Mask_Str = 0, 0, '', ''
            if "Name" in Show:
                for i in range(Desc['ENTRIES']):
                    Name_Len = len(Desc[i]['NAME'])
                    if Name_Len > N_Spc:
                       N_Spc = Name_Len
            if "Offset" in Show:
                for i in range(Desc['ENTRIES']):
                    Mask_Len = len(str(hex(Desc[i]['VALUE'])))
                    if Mask_Len > M_Spc:
                       M_Spc = Mask_Len
                   
            #print each of the booleans
            for i in range(Desc['ENTRIES']):
                tempstring = Indent_Str + '['
                Mask = Desc[i].get('VALUE')
                Spc = ''
                
                if "Offset" in Show:
                    Mask_Str = str(hex(Mask))
                    tempstring += ', Mask:' + Mask_Str
                    Spc = ' '*(M_Spc-len(Mask_Str))
                if "Name" in Show:
                    Name = Desc[i].get('NAME')
                    tempstring += ', ' + Spc + Name
                    Spc = ' '*(N_Spc-len(Name))
                if "Value" in Show:
                    tempstring += ', ' + Spc + str(bool(self.Data&Mask))
                
                Tag_String += tempstring.replace(',','',1) + ' ]'
                
                if Printout:
                    if Tag_String:
                        print(Tag_String)
                    Tag_String = ''
                else:
                    Tag_String += '\n'
            Tag_String += Indent_Str + ']'
        else:
            Tag_String += ' ]'

        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        return Tag_String


    def __getitem__(self, Attr_Index):
        '''docstring'''
        if not isinstance(Name, int):
            raise TypeError("'Attr_Index' must be an int, not %s" % type(Name))
        
        return self.Data & _OGA(self, "DESC")[Attr_Index]['VALUE']

    def __setitem__(self, Attr_Index, New_Val):
        '''docstring'''
        if not isinstance(Name, int):
            raise TypeError("'Attr_Index' must be an int, not %s" % type(Name))
        
        Mask = _OGA(self,"DESC")[Attr_Index]['VALUE']
        self.Data = self.Data - (self.Data&Mask) + (Mask)*bool(New_Val)

    def __delitem__(self, Attr_Index):
        '''docstring'''
        if not isinstance(Name, int):
            raise TypeError("'Attr_Index' must be an int, not %s" % type(Name))
        
        self.Data -= self.Data & _OGA(self,"DESC")[Attr_Index]['VALUE']

    def __getattr__(self, Name):
        '''docstring'''
        try:
            return _OGA(self, Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc['NAME_MAP']:
                return self.Data & Desc[Desc['NAME_MAP'][Name]]['VALUE']
            elif Name in Desc:
                return Desc[Name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'"
                                     %(Desc.get('NAME',UNNAMED),
                                       type(self),Name))


    def __setattr__(self, Name, New_Val):
        '''docstring'''
        try:
            _OSA(self, Name, New_Val)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            Attr_Index = Desc['NAME_MAP'].get(Name)
            if Attr_Index is not None:
                Mask = Desc[Attr_Index]['VALUE']
                self.Data = self.Data - (self.Data&Mask) + (Mask)*bool(New_Val)
            elif Name in Desc:
                self.Set_Desc(Name)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (Desc.get('NAME',UNNAMED),
                                      type(self),Name))

    def __delattr__(self, Name):
        '''docstring'''
        try:
            _ODA(self, Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")

            Attr_Index = Desc['NAME_MAP'].get(Name)
            if Attr_Index is not None:
                #unset the flag and remove the option from the descriptor
                self.Data -= self.Data & Desc[Attr_Index]['VALUE']
                self.Del_Desc(Attr_Index)
            elif Name in Desc:
                self.Del_Desc(Name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME',UNNAMED),
                                      type(self),Name))
        
    def Set(self, Name):
        '''docstring'''
        if not isinstance(Name, str):
            raise TypeError("'Name' must be a string, not %s"%type(Name))
        Desc = _OGA(self, "DESC")
        Mask = Desc[Desc['NAME_MAP'][Name]]['VALUE']
        self.Data = (self.Data-(self.Data&Mask))+Mask

    
    def Set_To(self, Name, Value):
        '''docstring'''
        if not isinstance(Name, str):
            raise TypeError("'Name' must be a string, not %s"%type(Name))
        Desc = _OGA(self, "DESC")
        Mask = Desc[Desc['NAME_MAP'][Name]]['VALUE']
        self.Data = self.Data - (self.Data&Mask) + (Mask)*bool(Value)
    

    def Unset(self, Name):
        '''docstring'''
        if not isinstance(Name, str):
            raise TypeError("'Name' must be a string, not %s"%type(Name))
        Desc = _OGA(self, "DESC")
        self.Data -= self.Data & Desc[Desc['NAME_MAP'][Name]]['VALUE']

        
    def Read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An Init_Data
        can be provided with which to initialize the values of the block.'''

        Attr_Index = kwargs.get('Attr_Index',None)
        Init_Data  = kwargs.get('Init_Data', None)
        
        Raw_Data = self.Get_Raw_Data(**kwargs)
            
        if Init_Data is not None:
            try:
                self.Data = int(Init_Data)
            except ValueError:
                raise ValueError("'Init_Data' must be a value able to be "+
                                 "converted to an integer. Got %s"%Init_Data)
            except TypeError:
                raise ValueError("Invalid type for 'Init_Data'. Must be a "+
                                 "string or a number, not %s"%type(Init_Data))
        elif kwargs.get('Init_Attrs', True):
            Desc = _OGA(self, "DESC")
            New_Val = 0
            for i in range(Desc['ENTRIES']):
                Opt = Desc[i]
                New_Val += bool(Opt.get('VALUE') & Opt.get('DEFAULT', 0))
                    
            self.Data = New_Val
                
        elif Raw_Data is not None:
            #build the block from raw data
            try:
                Desc = _OGA(self, "DESC")
                Desc['TYPE'].Reader(Desc, self, Raw_Data, None,
                                    kwargs.get('Root_Offset', 0),
                                    kwargs.get('Offset', 0))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read Bool_Block from file.')
            

class Enum_Block(Data_Block):
    
    __slots__ = ("DESC", "PARENT", "Data")

    
    def __str__(self, **kwargs):
        '''docstring'''
        
        Printout = kwargs.get('Printout', False)
        Show = kwargs.get('Show', Def_Show)
        if isinstance(Show, str):
            Show = set([Show])
        else:
            Show = set(Show)
            
        #if the list includes 'All' it means to show everything
        if 'All' in Show:
            Show.update(All_Show)

        #used to display different levels of indention
        Indent_Str = (' '*kwargs.get('Indent', BLOCK_PRINT_INDENT)*
                         (kwargs.get('Level',0)+1))
        
        Desc = _OGA(self,'DESC')

        #build the main part of the string
        kwargs['Printout'] = False
        Tag_String = Data_Block.__str__(self, **kwargs)[:-2]

        if Printout:
            if Tag_String:
                print(Tag_String)
            Tag_String = ''
        else:
            Tag_String += '\n'

        #find which index the string matches to
        try:
            index = self.Get_Index(self.Data)
        except AttributeError:
            index = None
        
        Opt = Desc.get(index, {})
        Tag_String += Indent_Str + ' %s ]' % Opt.get('NAME',INVALID)

        if Printout:
            if Tag_String:
                print(Tag_String)
            return ''
        return Tag_String


    def __getattr__(self, Name):
        '''docstring'''
        try:
            return _OGA(self, Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc:
                return Desc[Name]
            elif Name in Desc['NAME_MAP']:
                raise AttributeError("Cannot get enumerator option as an "+
                                     "attribute. Use Get() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME',UNNAMED),
                                      type(self),Name))
            

    def __setattr__(self, Name, New_Value):
        '''docstring'''
        try:
            _OSA(self, Name, New_Value)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc:
                if Name == 'CHILD':
                    raise AttributeError(("'%s' of type %s has no slot for a "+
                            "CHILD.")%(Desc.get('NAME',UNNAMED),type(self)))
                self.Set_Desc(Name, New_Value)
            elif Name in Desc['NAME_MAP']:
                raise AttributeError("Cannot set enumerator option as an "+
                                     "attribute. Use Set() instead.")
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (Desc.get('NAME',UNNAMED),
                                      type(self),Name))


    def __delattr__(self, Name):
        '''docstring'''
        try:
            _ODA(self, Name)
        except AttributeError:
            Desc = _OGA(self, "DESC")
            
            if Name in Desc:
                self.Del_Desc(Name)
            elif Name in Desc['NAME_MAP']:
                raise AttributeError("Cannot delete enumerator option as "+
                                     "an attribute. Use Del_Desc() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (Desc.get('NAME',UNNAMED),
                                      type(self),Name))
        

    def Get_Index(self, Value):
        '''docstring'''
        Index = _OGA(self, "DESC")['VALUE_MAP'].get(Value)
        if Index is not None:
            return Index
        Desc = _OGA(self, "DESC")
        raise AttributeError("'%s' of type %s has no option value matching '%s'"
                             % (Desc.get('NAME',UNNAMED),type(self),Value))

    def Get_Name(self, Value):
        '''docstring'''
        Desc = _OGA(self, "DESC")
        Index = Desc['VALUE_MAP'].get(Value)
        if Index is not None:
            return Desc[Index]['NAME']
        
        raise AttributeError("'%s' of type %s has no option value matching '%s'"
                             % (Desc.get('NAME',UNNAMED),type(self),Value))

    
    def Get_Data(self, Name):
        '''docstring'''
        Desc = _OGA(self, "DESC")
        if isinstance(Name, int):
            Option = Desc.get(Name)
        else:
            Option = Desc.get(Desc['NAME_MAP'].get(Name))
        
        if Option is None:
            raise AttributeError("'%s' of type %s has no enumerator option '%s'"
                                %(Desc.get('NAME',UNNAMED),type(self),Name))
        Data = Option['VALUE']
        return (self.Data == Data) and (type(self.Data) == type(Data))

        
    def Set_Data(self, Name):
        '''docstring'''
        Desc = _OGA(self, "DESC")
        if isinstance(Name, int):
            Option = Desc.get(Name)
        else:
            Option = Desc.get(Desc['NAME_MAP'].get(Name))
        
        if Option is None:
            raise AttributeError("'%s' of type %s has no enumerator option '%s'"
                                %(Desc.get('NAME',UNNAMED),type(self),Name))
        self.Data = Option['VALUE']

    @property
    def Data_Name(self):
        '''Exists as a property based way of determining
        the option name of the current value of self.Data'''
        Desc = _OGA(self, "DESC")
        return Desc.get(Desc['VALUE_MAP'].get(self.Data),{NAME:INVALID})[NAME]
