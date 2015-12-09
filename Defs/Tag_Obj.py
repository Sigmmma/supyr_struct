import os
import sys
import shutil

from array import array
from copy import deepcopy
from mmap import mmap
from traceback import format_exc
from sys import getsizeof
from time import time

from supyr_struct.Defs.Constants import *

#Tag_Objs and Tag_Blocks need to circularly reference each other.
#In order to do this properly, each module tries to import the other.
#If one succeeds then it provides itself as a reference to the other.
'''try to import the Tag_Blocks module. if it fails then
its because the Tag_Blocks module is already being built'''
try:
    from supyr_struct import Tag_Blocks
    Tag_Blocks.Tag_Obj = sys.modules[__name__]
except ImportError: pass


class Tag_Obj():
    '''docstring'''
    
    #the tag handler which this tag belongs to.
    Handler = None
    
    #this is the object that built this Tag and can build others
    Constructor = None
    
    #the whole Definition, including the Tag_Ext, Cls_ID, and Structure
    Definition = None
    
    #if this tags data starts inside a larger structure,
    #this is the offset its data should be written to
    Root_Offset = 0

    #determines whether or not to scan the tag for pointers
    #when writing it and set their values to where the blocks
    #they point to will be written. If False, any pointer
    #based blocks will be written to where their pointers
    #currently point to, whether or not they are valid.
    '''YOU SHOULDNT ENABLE THIS IF YOUR DEFINITION IS INCOMPLETE'''
    Calc_Pointers = True

    #if this tag is incomplete, this is the path to the source
    #file that was read from to build it. Used for preserving
    #the unknown data while allowing known parts to be edited
    Tag_Source_Path = ''
    
    #this is the string of the absolute path to the tag
    Tag_Path = ''
    
    #the actual data this tag holds
    #represented as nested Tag_Blocks
    Tag_Data = None
    
    def __init__(self, **kwargs):
        '''docstring'''
            
        if "Handler" in kwargs:
            self.Handler = kwargs["Handler"]

        if "Definition" in kwargs:
            self.Definition = kwargs["Definition"]

        if "Constructor" in kwargs:
            self.Constructor = kwargs["Constructor"]

        if "Root_Offset" in kwargs:
            self.Root_Offset = kwargs["Root_Offset"]

        if "Calc_Pointers" in kwargs:
            self.Calc_Pointers = kwargs["Calc_Pointers"]
        else:
            try:
                #If the definition isnt complete, changing any pointers
                #will almost certainly screw up the layout of the data.
                #By default, pointers wont be recalculated on incomplete defs
                if self.Definition.Incomplete:
                    self.Calc_Pointers = False
            except Exception:
                pass
        
        if "Tag_Path" in kwargs:
            self.Tag_Path = kwargs["Tag_Path"]

        if "Tag_Data" in kwargs:
            self.Tag_Data = kwargs["Tag_Data"]
        else:
            Raw_Data = kwargs.get("Raw_Data")

            #whether or not to allow corrupt tags to be built.
            #this is a debugging tool.
            if kwargs.get('Allow_Corrupt'):
                try:
                    self.Read(Raw_Data=Raw_Data)
                except Exception:
                    print(format_exc())
            else:
                self.Read(Raw_Data=Raw_Data)


    def __copy__(self):
        '''Creates a shallow copy of the object.'''
        
        #create the new Tag_Obj
        Dup_Tag = type(self)(Tag_Data=None)
        
        #copy all the attributes from this tag to the duplicate
        Dup_Tag.__dict__.update(self.__dict__)

        return Dup_Tag


    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the definition the same'''
        
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]
        
        #create the new Tag_Obj
        Dup_Tag = type(self)(Tag_Data=None)
        
        #copy all the attributes from this tag to the duplicate
        Dup_Tag.__dict__.update(self.__dict__)

        #add the Dup_Block to the memo with id of this tag as the key
        memo[id(self)] = Dup_Tag

        #create a deep copy of the Tag_Data and set it
        Dup_Tag.Tag_Data = deepcopy(self.Tag_Data, memo)

        return Dup_Tag


    def __str__(self, **kwargs):
        '''Creates a formatted string representation of the hierarchy and
        data within a tag. Keyword arguments can be supplied to specify
        what information to display and how much to indent per line.
        Passes keywords to self.Tag_Data.__str__() to maintain formatting.

        Optional kwargs:
            Indent(int)
            Level(int)

        Indent - determines how many spaces to indent each hierarchy line
        Level  - determines how many levels the hierarchy is already indented
        '''
        if not "Indent" in kwargs:
            kwargs['Indent'] = BLOCK_PRINT_INDENT
        if not "Level" in kwargs:
            kwargs['Level'] = 0
            
        kwargs['Printout'] = bool(kwargs.get('Printout'))
            
        '''Prints the contents of a tag object'''            
        if self.Tag_Data is None:
            raise LookupError("'Tag_Data' doesn't exist. Tag may have been "+
                              "constructed incorrectly.\n" + ' '*BPI + self.Tag_Path)
            
        return self.Tag_Data.__str__(**kwargs)


      
    def __sizeof__(self, Seen_Set=None, Include_Tag_Data=True):
        '''docstring'''
        if Seen_Set == None:
            Seen_Set = set()
        else:
            if id(self) in Seen_Set:
                return 0
            
        Attributes = self.__dict__
        Bytes_Total = getsizeof(self.__dict__)
        
        if id(self) not in Seen_Set:
            Seen_Set.add(id(self))
            Seen_Set.add(id(self.Tag_Data))
            Seen_Set.add(id(self.Definition))
            if ORIG_DESC in self.Definition.Tag_Structure:
                Bytes_Total += getsizeof(self.Definition.Tag_Structure)
                
        if Include_Tag_Data:
            for Block in self.Tag_Data:
                if isinstance(Block, Tag_Blocks.Tag_Block):
                    Bytes_Total += Block.__sizeof__(Seen_Set)
                else:
                    Bytes_Total += getsizeof(Block)
                    
            if hasattr(self.Tag_Data, 'CHILD'):
                if isinstance(self.Tag_Data.CHILD, Tag_Blocks.Tag_Block):
                    Bytes_Total += self.Tag_Data.CHILD.__sizeof__(Seen_Set)
                else:
                    Bytes_Total += getsizeof(self.Tag_Data.CHILD)
        
        for attr in Attributes:
            if id(Attributes[attr]) not in Seen_Set:
                Seen_Set.add(id(Attributes[attr]))
                Bytes_Total += getsizeof(Attributes[attr])

        return Bytes_Total


    def Set_Pointers(self, Offset=0):
        '''Scans through a tag and sets the pointer of each
        pointer based block in a way that ensures that, when
        written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other block.'''
        
        #Keep a set of all seen block IDs to prevent infinite recursion.
        Seen = set()
        PB_Blocks = []

        '''Loop over all the blocks in Tag_Data and log all blocks that use
        pointers to a list. Any pointer based blocks will NOT be entered.
        
        The size of all non-pointer blocks will be calculated and used
        as the starting offset pointer based blocks.'''
        Offset = self.Tag_Data.Set_Pointers_Loop(Offset, Seen, PB_Blocks)

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

                #In binary structs, usually when a block doesnt exist
                #its pointer will be set to zero. Emulate this by
                #setting the pointer to 0 if the size is zero
                if Block.Get_Size(Attr_Index):
                    Block.Set_Meta('POINTER', Offset, Attr_Index)
                else:
                    Block.Set_Meta('POINTER', 0, Attr_Index)

                Offset = Block.Set_Pointers_Loop(Offset, Seen, New_PB_Blocks,
                                               Attr_Index=Attr_Index, Root=True)
            #restart the loop using the next level of pointer based blocks
            PB_Blocks = New_PB_Blocks


    @property
    def Cls_ID(self):
        try:
            return self.Definition.Cls_ID
        except Exception:
            return None
        


    def Print(self, **kwargs):
        '''Used for printing the tag in a much more controlled
        way than simply print(Tag). Also allows printing a
        partially corrupted tag in order to debug it.
        
        If 'Printout' is a keyword, the function will
        print each line as it is constructed instead
        of returning the whole string at once(which
        it will still do)
        
        Keywords are:
        'Indent', 'Print_Raw', 'Printout', 'Precision',
        'Show':['Type', 'Offset', 'Value', 'Size',
                'Py_ID', 'Py_Type', 'Index',
                'Elements', 'Flags', 'Name', 'Children',
                'Tag_Path', 'Bin_Size', 'Ram_Size']
        '''
        if not 'Show' in kwargs or (not hasattr(kwargs['Show'], '__iter__')):
            kwargs['Show'] = set()
        if isinstance(kwargs["Show"], str):
            kwargs['Show'] = [kwargs['Show']]

        Show = set(kwargs['Show'])
        if 'All' in Show:
            Show.remove('All')
            Show.update(("Name", "Value", "Type", "Offset", "Flags", "Children",
                         "Index", "Elements", "Unique", "Size", "Py_Type",
                         'Tag_Path', "Py_ID", "Bin_Size", "Ram_Size"))

        Printout = False
        Ram_Size = "Ram_Size" in Show
        Bin_Size = "Bin_Size" in Show
        Tag_String = ''
        Precision = None
        
        if kwargs.get('Printout'):
            Printout = True
        if 'Precision' in kwargs:
            Precision = kwargs['Precision']
        
        kwargs['Printout'] = Printout
        
        if Ram_Size:
            Show.remove('Ram_Size')
        if Bin_Size:
            Show.remove('Bin_Size')
            
        kwargs['Show'] = Show
        
        if 'Tag_Path' in Show:
            Handler = self.Handler
            Tag_String = self.Tag_Path
            if Handler is not None and hasattr(Handler, 'Tags_Directory'):
                Tag_String = Tag_String.split(Handler.Tags_Directory)[-1]
                
            if Printout:
                print(Tag_String)
                Tag_String = ''
            else:
                Tag_String += '\n'
                
        Tag_String += self.__str__(**kwargs)
        if Printout:
            print(Tag_String)
            Tag_String = ''
        else:
            Tag_String += '\n'

        
        if Ram_Size:
            Tag_Obj_Size = self.__sizeof__()
            Tag_Data_Size = (Tag_Obj_Size -
                             self.__sizeof__(Include_Tag_Data=False))
            Tag_String += ('"In-Memory Tag Object" is '
                           +str(Tag_Obj_Size)+" bytes\n")
            Tag_String += ('"In-Memory Tag Data" is '
                           +str(Tag_Data_Size)+" bytes\n")

            
        if Bin_Size:
            Tag_Bin_Size = self.Tag_Data.Bin_Size
            Tag_String += ('"Packed Structure" is '
                           +str(Tag_Bin_Size) + " bytes\n")

            if Ram_Size and Bin_Size:
                File_Times_Larger = "∞"
                Data_Times_Larger = "∞"
                if Tag_Bin_Size:
                    Size_Str = "{:."+str(Precision)+"f}"
                    
                    File_Times_Larger = Tag_Obj_Size/Tag_Bin_Size
                    Data_Times_Larger = Tag_Data_Size/Tag_Bin_Size
                    if Precision:
                        File_Times_Larger = (Size_Str.format(round(
                                             File_Times_Larger, Precision)))
                        Data_Times_Larger = (Size_Str.format(round(
                                             Data_Times_Larger, Precision)))
                    
                Tag_String += ('"In-Memory Tag Object" is ' +
                               str(File_Times_Larger) + " times as large.\n" + 
                               '"In-Memory Tag Data" is ' +
                               str(Data_Times_Larger) + " times as large.\n")
            
        if Printout:
            print(Tag_String)
        else:
            return Tag_String



    def Read(self, **kwargs):
        '''this function gets run on the initial tag construction'''
        Raw_Data = Filepath = None
        Init_Attrs = True

        if 'Init_Attrs' in kwargs:
            Init_Attrs = bool(kwargs['Init_Attrs'])
        if 'Filepath' in kwargs:
            Filepath = kwargs['Filepath']
        if 'Raw_Data' in kwargs:
            Raw_Data = kwargs['Raw_Data']
            
        if Filepath is not None:
            if Raw_Data is not None:
                raise TypeError("Provide either Raw_Data " +
                                "or a Filepath, not both.")
        else:
            Filepath = self.Tag_Path
            
        '''try to open the tag's path as the raw tag data'''
        if Filepath and Raw_Data is None:
            try:
                with open(Filepath, 'r+b') as Tag_File:
                    Raw_Data = mmap(Tag_File.fileno(), 0)
            except Exception:
                raise IOError('Input filepath for reading Tag was ' +
                              'invalid or the file could not be ' +
                              'accessed.\n' + ' '*BPI + Filepath)
                
        if (Raw_Data is not None and
            not(hasattr(Raw_Data, 'read') or hasattr(Raw_Data, 'seek'))):
            raise TypeError('Cannot build a Tag_Block without either'
                            + ' an input path or a readable buffer')
        
        Desc = self.Definition.Tag_Structure
        Root_Offset = self.Root_Offset
        Init_Attrs = Raw_Data is None
        Offset = 0
        
        if CHILD in Desc:
            Block_Type = Desc.get(DEFAULT, Tag_Blocks.Tag_Parent_Block)
        else:
            Block_Type = Desc.get(DEFAULT, Tag_Blocks.Tag_Block)
            
        New_Tag_Data = Block_Type(Desc, Parent=self, Init_Attrs=False)
        self.Tag_Data = New_Tag_Data
        New_Tag_Data.__init__(Desc, Parent=self, Init_Attrs=Init_Attrs)
        
        if 'Root_Offset' in kwargs:
            Root_Offset = kwargs['Root_Offset']
        if 'Offset' in kwargs:
            Offset = kwargs['Offset']

        #if this is an incomplete object then we
        #need to keep a path to the source file
        if self.Definition.Incomplete and Raw_Data:
            self.Tag_Source_Path = self.Tag_Path
            
        Offset = Desc[TYPE].Reader(New_Tag_Data, Raw_Data,
                                   None, Root_Offset, Offset)

            

    def Write(self, **kwargs):            
        """ this function will attempt to save the tag to it's current
        file path, but while appending ".temp" to the end. if it
        successfully saved then it will attempt to either backup or
        delete the old tag and remove .temp from the resaved one.
        """
        
        Tag_Data = self.Tag_Data
        Desc     = self.Tag_Data.DESC
        Filepath = self.Tag_Path
        
        Root_Offset = self.Root_Offset
        Offset = 0
        
        Calc_Pointers = self.Calc_Pointers
        Test = True
        Temp = True
        Backup = True
        
        if 'Filepath' in kwargs:
            Filepath = kwargs['Filepath']
        if 'Root_Offset' in kwargs:
            Root_Offset = kwargs['Root_Offset']
        if 'Offset' in kwargs:
            Offset = kwargs['Offset']
        if 'Backup' in kwargs:
            Backup = kwargs['Backup']
        if "Temp" in kwargs:
            Temp = bool(kwargs["Temp"])
        if "Calc_Pointers" in kwargs:
            Calc_Pointers = bool(kwargs["Calc_Pointers"])
        if "Test" in kwargs:
            Test = bool(kwargs["Test"])
        if kwargs.get('Buffer'):
            raise TypeError("Cannot write whole tags to a buffer. " +
                            "Instead, call the Write() method in this " +
                            "Tags 'Tag_Data' with the same arguments.")

        #if the tag constructor doesnt exist then dont test after writing
        try:
            Test = bool(self.Constructor.Construct_Tag)
        except Exception:
            Test = False

        if Filepath == '':
            raise IOError("Filepath is invalid. Cannot write "+
                          "tag to '%s'" % self.Tag_Path)
            
        Temp_Tag_Path = Filepath + ".temp"
        Backup_Tag_Path = Filepath + ".backup"

        #open the file to be written and start writing!
        with open(Temp_Tag_Path, 'w+b') as Tag_File:
            '''if this is an incomplete object we need to copy the
            original file to the path of the new file in order to
            fill in the data we don't yet understand/have mapped out'''
            if self.Definition.Incomplete:
                if not(os.path.isfile(self.Tag_Source_Path)):
                    raise IOError("Tag is incomplete and the source "+
                                  "file to fill in the remaining "+
                                  "data cannot be found.")
                
                if self.Tag_Source_Path != Temp_Tag_Path:
                    shutil.copyfileobj(open(self.Tag_Source_Path, 'r+b'),
                                       Tag_File, 2*(1024**2) )#2MB buffer
            else:
                #make a file as large as the tag is calculated to fill
                Tag_File.write(bytes(Tag_Data.Bin_Size))
                    
            #if we need to calculate any pointers, do so
            if Calc_Pointers:
                self.Set_Pointers(Offset)

            Tag_Data.TYPE.Writer(Tag_Data, Tag_File, None,
                                 Root_Offset, Offset)
        if Test:
            #quick load the tag to check its integrity
            Integrity_Test = self.Constructor.Construct_Tag(Tag_Test=True,
                                                         Cls_ID=self.Cls_ID,
                                                         Filepath=Temp_Tag_Path)
        else:
            Integrity_Test = True
        
        #now we test to see if we can load the tag that we just made
        if Integrity_Test:
            """If we are doing a full save then we
            need to try and rename the temp file"""
            if not Temp:
                if Backup:
                    """if there's already a backup of this tag
                    we try to delete it. if we can't then we try
                    to rename the old tag with the backup name"""
                    if os.path.isfile(Backup_Tag_Path):
                        os.remove(Filepath)
                    else:
                        try: os.rename(Filepath, Backup_Tag_Path)
                        except Exception:
                            print(("ERROR: While attempting to save tag, " +
                                   "could not rename:\n" + ' '*BPI + "%s\nto "+
                                   "the backup file:\n" +' '*BPI + "%s")%
                                  (Filepath, Backup_Tag_Path))

                    """Try to rename the temp files to the new
                    file names. If we can't rename the temp to
                    the original, we restore the backup"""
                    try: os.rename(Temp_Tag_Path, Filepath)
                    except Exception:
                        try: os.rename(Backup_Tag_Path, Filepath)
                        except Exception: pass
                        raise IOError(("ERROR: While attempting to save" +
                                       "tag, could not rename temp file:\n" +
                                       ' '*BPI + "%s\nto\n" + ' '*BPI + "%s")%
                                      (Temp_Tag_Path, Filepath))
                else:
                    #Try to delete the old file
                    try: os.remove(Filepath)
                    except Exception: pass

                    #Try to rename the temp tag to the real tag name
                    try: os.rename(Temp_Tag_Path, Filepath)
                    except Exception: pass
        else:
            raise IOError("The following tag temp file did not pass the data "+
                          "integrity test:\n" + ' '*BPI + str(self.Tag_Path))

        return True
