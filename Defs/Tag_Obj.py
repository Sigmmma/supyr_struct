import sys
import shutil

from array import array
from copy import copy, deepcopy
from mmap import mmap
from os import makedirs, remove, rename
from os.path import dirname, exists, isfile
from sys import getsizeof
from traceback import format_exc
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
    
    def __init__(self, **kwargs):
        '''docstring'''
            
        #the tag Library which this tag belongs to and is also
        #the object that built this Tag and can build others
        self.Library = kwargs.get("Library", None)
        
        #the whole Definition, including the Ext, Cls_ID, and Structure
        self.Definition = kwargs.get("Definition", None)

        #if this tags data starts inside a larger structure,
        #this is the offset its data should be written to
        self.Root_Offset = kwargs.get("Root_Offset", 0)
        
        #if this tag is incomplete, this is the path to the source
        #file that was read from to build it. Used for preserving
        #the unknown data while allowing known parts to be edited
        self.Tag_Source_Path = ''

        '''YOU SHOULDNT ENABLE THIS IF YOUR DEFINITION IS INCOMPLETE'''
        #Calc_Pointers determines whether or not to scan the tag for
        #pointers when writing it and set their values to where the
        #blocks they point to will be written. If False, any pointer
        #based blocks will be written to where their pointers
        #currently point to, whether or not they are valid.
        if "Calc_Pointers" in kwargs:
            self.Calc_Pointers = kwargs["Calc_Pointers"]
        else:
            try:
                self.Calc_Pointers = True
                #If the definition isnt complete, changing any pointers
                #will almost certainly screw up the layout of the data.
                #By default, pointers wont be recalculated on incomplete defs
                if self.Definition.Incomplete:
                    self.Calc_Pointers = False
            except AttributeError:
                pass
        
        #this is the string of the absolute path to the tag
        self.Tag_Path = kwargs.get("Tag_Path",'')

        #the actual data this tag holds represented as nested Tag_Blocks
        if "Tag_Data" in kwargs:
            self.Tag_Data = kwargs["Tag_Data"]
        else:
            self.Tag_Data = None
            #whether or not to allow corrupt tags to be built.
            #this is a debugging tool.
            if kwargs.get('Allow_Corrupt'):
                try:
                    self.Read(Raw_Data=kwargs.get("Raw_Data"))
                except Exception:
                    print(format_exc())
            else:
                self.Read(Raw_Data=kwargs.get("Raw_Data"))


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
        memo[id(self)] = Dup_Tag = type(self)(Tag_Data=None)
        
        #copy all the attributes from this tag to the duplicate
        Dup_Tag.__dict__.update(self.__dict__)

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
        kwargs['Level'] = kwargs.get('Level',0)
        kwargs['Indent'] = kwargs.get('Indent',BLOCK_PRINT_INDENT)
        kwargs['Printout'] = bool(kwargs.get('Printout'))
            
        '''Prints the contents of a tag object'''            
        if self.Tag_Data is None:
            raise LookupError("'Tag_Data' doesn't exist. Tag may "+
                              "have been constructed incorrectly.\n" +
                              ' '*BPI + self.Tag_Path)
            
        return self.Tag_Data.__str__(**kwargs)


      
    def __sizeof__(self, Seen_Set=None, Include_Data=True):
        '''docstring'''
        if Seen_Set == None:
            Seen_Set = set()
        elif id(self) in Seen_Set:
            return 0
            
        Dict_Attrs = Slot_Attrs = ()
        if hasattr(self, '__dict__'):
            Dict_Attrs = copy(self.__dict__)                
        if hasattr(self, '__slots__'):
            Slot_Attrs = set(self.__slots__)
        Bytes_Total = getsizeof(self.__dict__)
        
        if id(self) not in Seen_Set:
            Seen_Set.add(id(self))
            Seen_Set.add(id(self.Definition))
            if ORIG_DESC in self.Definition.Tag_Structure:
                Bytes_Total += getsizeof(self.Definition.Tag_Structure)
                
        #if we aren't calculating the size of the Tag_Data, remove it
        if not Include_Data:
            if 'Tag_Data' in Dict_Attrs:
                del Dict_Attrs['Tag_Data']
            if 'Tag_Data' in Slot_Attrs:
                Slot_Attrs.remove('Tag_Data')
            
        for Attr_Name in Dict_Attrs:
            if id(Dict_Attrs[Attr_Name]) not in Seen_Set:
                Seen_Set.add(id(Dict_Attrs[Attr_Name]))
                Bytes_Total += getsizeof(Dict_Attrs[Attr_Name])
            
        for Attr_Name in Slot_Attrs:
            try:
                Attr = object.__getattribute__(self, Attr_Name)
            except AttributeError:
                continue
            if id(Attr) not in Seen_Set:
                Seen_Set.add(id(Attr))
                Bytes_Total += getsizeof(Attr)

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
        Offset = self.Tag_Data.Collect_Pointers(Offset, Seen, PB_Blocks)
        
        #Repeat this until there are no longer any pointer
        #based blocks for which to calculate pointers.
        while PB_Blocks:
            New_PB_Blocks = []
            
            '''Iterate over the list of pointer based blocks and set their
            pointers while incrementing the offset by the size of each block.
            
            While doing this, build a new list of all the pointer based
            blocks in all of the blocks currently being iterated over.'''
            for Block in PB_Blocks:
                Block, Attr_Index = Block[0], Block[1]

                #In binary structs, usually when a block doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if Block.Get_Size(Attr_Index) > 0:
                    Block.Set_Meta('POINTER', Offset, Attr_Index)
                    Offset = Block.Collect_Pointers(Offset, Seen, New_PB_Blocks,
                                                    False, Attr_Index, True)
                else:
                    Block.Set_Meta('POINTER', 0, Attr_Index)
                    
            #restart the loop using the next level of pointer based blocks
            PB_Blocks = New_PB_Blocks


    @property
    def Cls_ID(self):
        try:
            return self.Definition.Cls_ID
        except AttributeError:
            return None
        

    def Print(self, **kwargs):
        '''Used for pretty printing. Allows printing a
        partially corrupted tag in order to debug it.
        
        If 'Printout' is a keyword, the function will
        print each line as it is constructed instead
        of returning the whole string at once(which
        it will still do)
        
        Keywords are:
        'Indent', 'Print_Raw', 'Printout', 'Precision',
        'Show':['Type', 'Offset', 'Value', 'Size',
                'Py_ID', 'Py_Type', 'Index',
                'Flags', 'Name', 'Children',
                'Tag_Path', 'Bin_Size', 'Ram_Size']
        '''
        if not 'Show' in kwargs or (not hasattr(kwargs['Show'], '__iter__')):
            kwargs['Show'] = set()
        if isinstance(kwargs["Show"], str):
            kwargs['Show'] = [kwargs['Show']]

        Show = set(kwargs['Show'])
        if 'All' in Show:
            Show.remove('All')
            Show.update(Tag_Blocks.All_Show)

        Ram_Size = "Ram_Size" in Show
        Bin_Size = "Bin_Size" in Show
        Tag_String = ''
        
        Printout = kwargs.get('Printout', False)
        Precision = kwargs.get('Precision', None)

        kwargs['Printout'] = Printout
        
        if Ram_Size: Show.remove('Ram_Size')
        if Bin_Size: Show.remove('Bin_Size')
            
        kwargs['Show'] = Show
        
        if 'Tag_Path' in Show:
            Library = self.Library
            Tag_String = self.Tag_Path
            if Library is not None and hasattr(Library, 'Tags_Dir'):
                Tag_String = Tag_String.split(Library.Tags_Dir)[-1]
                
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
            Obj_Size  = self.__sizeof__()
            Data_Size = Obj_Size - self.__sizeof__(Include_Data=False)
            Tag_String += '"In-Memory Tag Object" is '+str(Obj_Size)+" bytes\n"
            Tag_String += '"In-Memory Tag Data" is ' +str(Data_Size)+" bytes\n"
            
        if Bin_Size:
            Bin_Size = self.Tag_Data.Bin_Size
            Tag_String += '"Packed Structure" is '+str(Bin_Size)+" bytes\n"

            if Ram_Size and Bin_Size:
                File_X = Data_X = "∞"
                if Bin_Size:
                    fmt = "{:."+str(Precision)+"f}"
                    
                    File_X = Obj_Size/Bin_Size
                    Data_X = Data_Size/Bin_Size
                    if Precision:
                        File_X = fmt.format(round(File_X, Precision))
                        Data_X = fmt.format(round(Data_X, Precision))
                    
                Tag_String += ('"In-Memory Tag Object" is ' +
                               str(File_X)+" times as large.\n" + 
                               '"In-Memory Tag Data" is ' +
                               str(Data_X) + " times as large.\n")
            
        if Printout:
            print(Tag_String)
        else:
            return Tag_String


    def Read(self, **kwargs):
        '''this function gets run on the initial tag construction'''

        Filepath = kwargs.get('Filepath')
        Raw_Data = kwargs.get('Raw_Data')
            
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
        Type = Desc[TYPE]
        Init_Attrs = bool(kwargs.get('Init_Attrs', Raw_Data is None))
        Block_Type = Desc.get(DEFAULT, Type.Py_Type)

        #create the Tag_Data block and parent it to this
        #Tag_Obj before initializing its attributes
        New_Tag_Data = Block_Type(Desc, Parent=self, Init_Attrs=False)
        self.Tag_Data = New_Tag_Data
        
        if Init_Attrs:
            New_Tag_Data.__init__(Desc, Parent=self, Init_Attrs=True)
        
        Root_Offset = kwargs.get('Root_Offset', self.Root_Offset)
        Offset = kwargs.get('Offset', 0)

        #if this is an incomplete object then we
        #need to keep a path to the source file
        if self.Definition.Incomplete and Raw_Data:
            self.Tag_Source_Path = self.Tag_Path

        #call the reader
        Type.Reader(New_Tag_Data, Raw_Data, None, Root_Offset, Offset)


    def Write(self, **kwargs):            
        """ this function will attempt to save the tag to it's current
        file path, but while appending ".temp" to the end. if it
        successfully saved then it will attempt to either backup or
        delete the old tag and remove .temp from the resaved one.
        """
        
        Tag_Data = self.Tag_Data
        Desc     = self.Tag_Data.DESC        
        
        if kwargs.get('Buffer') is not None:
            return Tag_Data.Write(**kwargs)
            
        Filepath = kwargs.get('Filepath',self.Tag_Path)
        Offset = kwargs.get('Offset',0)
        Root_Offset = kwargs.get('Root_Offset',self.Root_Offset)
        Calc_Pointers = bool(kwargs.get('Calc_Pointers',self.Calc_Pointers))
        Backup = bool(kwargs.get('Backup',True))
        Temp = bool(kwargs.get('Temp',True))
        Test = bool(kwargs.get('Test',True))

        #if the tag library doesnt exist then dont test after writing
        try:
            Test = bool(self.Library.Build_Tag)
        except Exception:
            Test = False
            Tested = True

        if Filepath == '':
            raise IOError("Filepath is invalid. Cannot write "+
                          "tag to '%s'" % self.Tag_Path)
        
        Folderpath = dirname(Filepath)

        #if the filepath ends with the folder path terminator, raise an error
        if Filepath.endswith('\\') or Filepath.endswith('/'):
            raise IOError('Filepath must be a path to a file, not a folder.')

        #if the path doesnt exist, create it
        if not exists(Folderpath):
            makedirs(Folderpath)
        
        Temp_Path = Filepath + ".temp"
        Backup_Path = Filepath + ".backup"

        #open the file to be written and start writing!
        with open(Temp_Path, 'w+b') as Tag_File:
            '''if this is an incomplete object we need to copy the
            original file to the path of the new file in order to
            fill in the data we don't yet understand/have mapped out'''
            
            if self.Definition.Incomplete:
                if not(isfile(self.Tag_Source_Path)):
                    raise IOError("Tag is incomplete and the source "+
                                  "file to fill in the remaining "+
                                  "data cannot be found.")
                
                if self.Tag_Source_Path != Temp_Path:
                    shutil.copyfileobj(open(self.Tag_Source_Path, 'r+b'),
                                       Tag_File, 2*(1024**2) )#2MB buffer
            else:
                #make a file as large as the tag is calculated to fill
                Tag_File.seek(Tag_Data.Bin_Size-1)
                Tag_File.write(b'\x00')
                    
            #if we need to calculate any pointers, do so
            if Calc_Pointers:
                self.Set_Pointers(Offset)

            Tag_Data.TYPE.Writer(Tag_Data, Tag_File, None, Root_Offset, Offset)
            
        #if the library is accessible, we can quick load
        #the tag that was just written to check its integrity
        if Test:
            Tested = self.Library.Build_Tag(Test = True, Cls_ID = self.Cls_ID,
                                            Filepath = Temp_Path)
        
        if Tested:
            """If we are doing a full save then we
            need to try and rename the temp file"""
            if not Temp:
                if Backup:
                    """if there's already a backup of this tag
                    we try to delete it. if we can't then we try
                    to rename the old tag with the backup name"""
                    if isfile(Backup_Path):
                        remove(Filepath)
                    else:
                        try:
                            rename(Filepath, Backup_Path)
                        except Exception:
                            print(("ERROR: While attempting to save tag, " +
                                   "could not rename:\n" + ' '*BPI + "%s\nto "+
                                   "the backup file:\n" +' '*BPI + "%s")%
                                  (Filepath, Backup_Path))

                    """Try to rename the temp files to the new
                    file names. If we can't rename the temp to
                    the original, we restore the backup"""
                    try:
                        rename(Temp_Path, Filepath)
                    except Exception:
                        try: rename(Backup_Path, Filepath)
                        except Exception: pass
                        raise IOError(("ERROR: While attempting to save" +
                                       "tag, could not rename temp file:\n" +
                                       ' '*BPI + "%s\nto\n" + ' '*BPI + "%s")%
                                      (Temp_Path, Filepath))
                else:
                    #Try to delete the old file
                    try: remove(Filepath)
                    except Exception: pass

                    #Try to rename the temp tag to the real tag name
                    try: rename(Temp_Path, Filepath)
                    except Exception: pass
        else:
            raise IOError("The following tag temp file did not pass the data "+
                          "integrity test:\n" + ' '*BPI + str(self.Tag_Path))

        return True
