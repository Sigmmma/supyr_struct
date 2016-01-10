'''
A class for organizing and loading collections of tags of various Tag_IDs.

Libraries are meant to organize large quantities of different types of
tags which all reside in the same 'Tags_Dir' root folder. A Library
contains methods for indexing all valid tags within its Tags_Dir,
loading all indexed tags, writing all loaded tags back to their files, and
resetting the Tags or individual Cls_ID collections to empty.

Libraries contain a basic log creation function for logging successes
and failures when saving tags. This function can also rename all temp files
generated during the save operation to their non-temp filenames and logs all
errors encountered while trying to rename these files and backup old files.
'''
import os

from datetime import datetime
from importlib import import_module
from os import remove, rename
from os.path import split, splitext, join, isfile, relpath
from sys import getrecursionlimit
from traceback import format_exc
from types import ModuleType

from supyr_struct.Defs.Constants import *


class Library():
    '''
    A class for organizing and loading collections of tags of various Tag_IDs.

    Libraries are meant to organize large quantities of different types of
    tags which all reside in the same 'Tags_Dir' root folder. This class
    contains methods for indexing all valid tags within self.Tags_Dir,
    loading all indexed tags, and writing all loaded tags back to their files.
    
    Libraries contain a basic log creation function for logging successes
    and failures when saving tags. This function can also rename all temp files
    generated during the save operation to their non-temp filenames and logs all
    errors encountered while trying to rename these files and backup old files.

    Tags saved through a Library are not saved to the Tag.Tag_Path string,
    but rather to self.Tags_Dir + Tag_Path where Tag_Path is the key that
    the Tag is under in self.Tags[Cls_ID].
    
    Refer to this classes __init__.__doc__ for descriptions of
    the properties in this class that aren't described below.
    
    Object Properties:
        int:
            Rename_Tries
            Debug
            Tags_Indexed
            Tags_Loaded
        str:
            Current_Tag ---------- The Tag_Path of the current tag that this
                                   Library is indexing/loading/writing.
            Log_Filename
            Tags_Dir
        bool:
            Allow_Corrupt
            Check_Extension
            Write_as_Temp
            Backup_Old_Tags
        dict:
            Tags
            ID_Ext_Map ------ maps each Cls_ID(key) to its extension(value)
            
    Object Methods:
        Get_Unique_Filename(Tag_Path[str], Dest[iterable], Src[iterable]=(),
                            Rename_Tries[int]=0)
        Iter_to_Collection(New_Tags[dict], Tags[iterable]=None)
        Extend_Tags(New_Tags[dict], Replace[bool]=True)
        Index_Tags()
        Load_Tags()
        Reset_Tags(Tag_IDs[dict]=None)
        Write_Tags(Print_Errors[bool]=True, Temp[bool]=True,
                   Backup[bool]=True, Int_Test[bool]=True)
        Make_Tag_Write_Log(All_Successes[dict],
                           Backup[bool]=True, Rename[bool]=True)
        Make_Log_File(Log_String[str])
    '''
    
    Log_Filename      = 'log.log'
    Default_Tag_Obj   = None
    Default_Defs_Path = "supyr_struct\\Defs\\"

    def __init__(self, **kwargs):
        '''
        Initializes a Library with the supplied keyword arguments.
        
        Keyword arguments:
                           
        #int
        Debug ------------ The level of debugging information to show. 0 to 10.
                           The higher the number, the more information shown.
                           Currently this is of very limited use.
        Rename_Tries ----- The number of times that self.Get_Unique_Filename()
                           can fail to make the 'Tag_Path' string argument
                           unique before raising a RuntimeError. This renaming
                           process is used when calling self.Extend_Tags() with
                           'Replace'=False to merge a collection of tags into
                           the Tags of this Library.
        Tags_Indexed ----- This is the number of tags that were found when
                           self.Index_Tags() was run.
        Tags_Loaded ------ This is the number of tags that were loaded when
                           self.Load_Tags() was run.
        
        #str
        Tags_Dir --------- A filepath string pointing to the working directory
                           which all our tags are loaded from and written to.
                           When adding a tag to Tags[Cls_ID][Tag_Path]
                           the Tag_Path key is the path to the tag relative to
                           this Tags_Dir string. So if the Tags_Dir
                           string were 'c:/tags/' and a tag were located in
                           'c:/tags/test/a.tag', Tag_Path would be 'test/a.tag'
        Log_Filename ----- The name of the file all logs will be written to.
                           The file will be created in the Tags_Dir folder
                           if it doesn't exist. If it does exist, the file will
                           be opened and any log writes will be appended to it.
        
        #bool
        Allow_Corrupt ---- Enables returning corrupt tags rather than discarding
                           them and reporting the exception. Instead, the
                           exception will be printed to the console and the tag
                           will be returned like normal. For debugging use only.
        Check_Extension -- Whether or not(when indexing tags) to make sure a
                           tag's extension also matches the extension for that
                           Cls_ID. The main purpose is to prevent loading temp
                           files. This is only useful when overloading the
                           constructors 'Get_Cls_ID' function since the default
                           constructor verifies tags by their extension.
        Write_as_Temp ---- Whether or not to keep tags as temp files when
                           calling self.Write_Tags. Overridden by supplying
                           'Temp' as a keyword when calling self.Write_Tags.
        Backup_Old_Tags -- Whether or not to backup a file that exists with the
                           same name as a tag that is being saved. The file will
                           be renamed with the extension '.backup'. If a backup
                           already exists then the oldest backup will be kept.
                           
        #dict
        Tags ------------- A dict of dicts which holds every loaded tag. A
                           dict inside the Tags holds all of a single
                           type of tag, with each of the tags keyed by their
                           tag path, which is relative to self.Tags_Dir.
                           Accessing a tag is done like so:
                           Tags[Cls_ID][Tag_Path] = Tag_Obj

        #iterable
        Valid_Tag_IDs ---- Some form of iterable containing the Cls_ID strings
                           that this Library and its Tag_Constructer will
                           be working with. You may instead provide a single
                           Cls_ID string if working with just one kind of tag.
        '''
        
        #this is the filepath to the tag currently being constructed
        self.Current_Tag  = ''
        self.Tags_Indexed = self.Tags_Loaded = 0
        self.Tags = {}
        self.Tags_Dir = os.path.abspath(os.curdir) + "\\tags\\"
        
        self.Defs_Path = ''
        self.ID_Ext_Map = {}
        self.Defs = {}
        
        #Valid_Tag_IDs will determine which tag types are possible to load
        if isinstance(kwargs.get("Valid_Tag_IDs"), str):
            kwargs["Valid_Tag_IDs"] = tuple([kwargs["Valid_Tag_IDs"]])
        
        self.Debug = kwargs.get("Debug", 0)
        self.Rename_Tries  = kwargs.get("Rename_Tries", getrecursionlimit())
        self.Log_Filename  = kwargs.get("Log_Filename", self.Log_Filename)
        self.Int_Test      = bool(kwargs.get("Int_Test", True))
        self.Allow_Corrupt = bool(kwargs.get("Allow_Corrupt", False))
        self.Write_as_Temp = bool(kwargs.get("Write_as_Temp", True))
        self.Check_Extension = bool(kwargs.get("Check_Extension", True))
        self.Backup_Old_Tags = bool(kwargs.get("Backup_Old_Tags", True))
            
        self.Tags_Dir = kwargs.get("Tags_Dir", self.Tags_Dir).replace('/', '\\')
        self.Tags = kwargs.get("Tags", self.Tags)

        #make sure there is an ending folder slash on the tags directory
        if len(self.Tags_Dir) and not self.Tags_Dir.endswith("\\"):
            self.Tags_Dir += '\\'
            
        self.Reload_Defs(**kwargs)
        
        #make slots in self.Tags for the types we want to load
        self.Reset_Tags(self.Defs.keys())


    def Add_Def(self, Def, Cls_ID=None, Ext=None, Endian=None, Obj=None):
        '''docstring'''
        if isinstance(Def, dict):
            #a descriptor formatted dictionary was provided
            if Cls_ID is None or Ext is None:
                raise TypeError("Could not add new Tag_Def to constructor. "+
                                "Neither 'Cls_ID' or 'Ext' can be None if "+
                                "'Def' is a dict based structure.")
                
            Def = Tag_Def.Tag_Def(Structure=Def, Ext=Ext, Cls_ID=Cls_ID)
        elif isinstance(Def, type):
            #the actual Tag_Def class was provided
            if issubclass(Def, Tag_Def.Tag_Def):
                Def = Def()
            else:
                raise TypeError("The provided 'Def' is a class, but not "+
                                "a subclass of 'Tag_Def.Tag_Def'.")
        elif isinstance(Def, ModuleType):
            #a whole module was provided
            if hasattr(Def, "Construct"):
                Def = Def.Construct()
            else:
                raise AttributeError("The provided module does not have "+
                                     "a 'Construct' method to get the "+
                                     "Tag_Def class from.")
        elif isinstance(Def, Tag_Def.Tag_Def):
            #a Tag_Def was provided. nothing to do
            pass
        else:
            #no idea what was provided, but we dont care. ERROR!
            raise TypeError("Incorrect type for the provided 'Def'.\n"+
                            "Expected %s, %s, or %s, but got %s" %
                            (type(Tag_Def.Tag_Def.Tag_Structure),
                             type, ModuleType, type(Def)) )

        if isinstance(Obj, Tag_Obj.Tag_Obj):
            Def.Tag_Obj = Obj
            
        #if no Tag_Obj is associated with this Tag_Def, use the default one
        if Def.Tag_Obj is None:
            Def.Tag_Obj = self.Default_Tag_Obj
            
        self.Defs[Def.Cls_ID] = Def
        self.ID_Ext_Map[Def.Cls_ID] = Def.Ext

        return Def


    def Build_Tag(self, **kwargs):
        '''builds and returns a tag object'''        
        Cls_ID   = kwargs.get("Cls_ID", None)
        Filepath = kwargs.get("Filepath", '')
        Raw_Data = kwargs.get("Raw_Data", None)
        Int_Test = kwargs.get("Int_Test", False)
        Allow_Corrupt  = kwargs.get("Allow_Corrupt", self.Allow_Corrupt)

        #set the current tag path so outside processes
        #have some info on what is being constructed
        self.Current_Tag = Filepath

        if not Cls_ID:
            Cls_ID = self.Get_Cls_ID(Filepath)
            if not Cls_ID:
                raise LookupError('Unable to determine Cls_ID for:' +
                                  '\n' + ' '*BPI + self.Current_Tag)

        Def = self.Get_Def(Cls_ID)
        
        #if it could find a Tag_Def, then use it
        if Def:
            New_Tag = Def.Tag_Obj(Tag_Path=Filepath, Raw_Data=Raw_Data,
                                  Definition=Def, Allow_Corrupt=Allow_Corrupt,
                                  Library=self, Int_Test=Int_Test)
            return New_Tag
        
        raise LookupError(("Unable to locate definition for " +
                           "tag type '%s' for file:\n%s'%s'") %
                           (Cls_ID, ' '*BPI, self.Current_Tag))
        

    def Clear_Unloaded_Tags(self):
        '''
        Goes through each Cls_ID in self.Tags and each of the
        collections in self.Tags[Cls_ID] and removes any tags
        which are indexed, but not loaded.
        '''
        Tags = self.Tags
        
        for Cls_ID in Tags:
            Coll = Tags[Cls_ID]

            #need to make the collection's keys a tuple or else
            #we will run into issues after deleting any keys
            for Path in tuple(Coll):
                if Coll[Path] is None:
                    del Coll[Path]
                    
        self.Tally_Tags()


    def Get_Cls_ID(self, Filepath):
        '''docstring'''
        if not Filepath.startswith('.') and '.' in Filepath:
            ext = splitext(Filepath)[-1].lower()
        else:
            ext = Filepath.lower()
            
        for Cls_ID in self.ID_Ext_Map:
            if self.ID_Ext_Map[Cls_ID].lower() == ext:
                return Cls_ID
    

    def Get_Def(self, Cls_ID):
        return self.Defs.get(Cls_ID)
        

    def Get_Unique_Filename(self, Tag_Path, Dest, Src=(), Rename_Tries=0):
        '''
        Does a rename operation on the string 'Tag_Path' which
        increments a number on the end of it if it is a valid
        integer, or adds a new one if there isnt one.
        
        Raises RuntimeError if 'Rename_Tries' is exceeded.

        Required arguments:
            Tag_Path(str)
            Dest(iterable)
        Optional arguments:
            Src(iterable)
            Rename_Tries(int)

        Src and Dest are iterables which contain the filepaths to
        check against to see if the generated filename is unique.
        '''
        
        Split_Path, ext = splitext(Tag_Path)
        New_Path = Split_Path

        #this is the max number of attempts to rename a tag
        #that the below routine will attempt. this is to
        #prevent infinite recursion, or really long stalls
        if (not isinstance(Rename_Tries, int)) or Rename_Tries <= 0:
            Rename_Tries = self.Rename_Tries

        #sets are MUCH faster for testing membership than lists
        Src = set(Src)
        Dest = set(Dest)

        #find the location of the last underscore
        last_u_s = None
        for i in range(len(Split_Path)):
            if Split_Path[i] == '_':
                last_u_s = i

        #if the stuff after the last underscore is not an
        #integer, treat it as if there is no last underscore
        try:
            i = int(Split_Path[last_u_s+1:])
            Old_Path = Split_Path[:last_u_s] + '_'
        except Exception:
            i = 0
            Old_Path = Split_Path + '_'

        #increase Rename_Tries by the number we are starting at
        Rename_Tries += i
        
        #make sure the name doesnt already
        #exist in both Src or Dest
        while (New_Path+ext) in Dest or (New_Path+ext) in Src:
            New_Path = Old_Path + str(i)
            if i > Rename_Tries:
                raise RuntimeError("Maximum rename attempts exceeded " +
                                   "while trying to find a unique name "+
                                   " for the tag:\n    %s" % Tag_Path)
            i += 1

        return New_Path + ext
            

    def Iter_to_Collection(self, New_Tags, Tags=None):
        '''
        Converts an arbitrarily deep collection of iterables
        into a two level deep Tags of nested dicts
        containing Tag_Objs using the following structure:
        Tags[Cls_ID][Tag_Path] = Tag_Obj
        
        Returns the organized Tags.
        Raises TypeError if 'Tags' is not a dict

        Required arguments:
            New_Tags(iterable)
        Optional arguments:
            Tags(dict)
            
        If Tags is None or unsupplied, a
        new dict will be created and returned.
        Any duplicate tags in the provided 'New_Tags'
        will be overwritten by the last one added.
        '''
        
        if Tags is None:
            Tags = dict()

        if not isinstance(Tags, dict):
            raise TypeError("The argument 'Tags' must be a dict.")
            
        if isinstance(New_Tags, Tag_Obj.Tag_Obj):
            if New_Tags.Cls_ID not in Tags:
                Tags[New_Tags.Cls_ID] = dict()
            Tags[New_Tags.Cls_ID][New_Tags.Tag_Path] = New_Tags
        elif isinstance(New_Tags, dict):
            for key in New_Tags:
                self.Iter_to_Collection(New_Tags[key], Tags)
        elif hasattr(New_Tags, '__iter__'):
            for element in New_Tags:
                self.Iter_to_Collection(Tags, element)

        return Tags


    def Make_Log_File(self, Log_String):
        '''
        Writes the supplied string to a log file.
        
        Required arguments:
            Log_String(str)
            
        If self.Log_Filename is a non-blank string it will be used as the
        log filename. Otherwise the current timestamp will be used as the
        filename in the format "YY-MM-DD  HH:MM SS".
        If the file already exists it will be appended to with the current
        timestamp separating each write. Otherwise the file will be created.
        '''
        #get the timestamp for the debug log's name
        Timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        Filename  = Timestamp.replace(':','.') + ".log"

        if isinstance(self.Log_Filename, str) and self.Log_Filename:
            Filename = self.Log_Filename
            Log_String = '\n' + '-'*80 + '\n'+ Timestamp + '\n' + Log_String
            
        if isfile(self.Tags_Dir + Filename):
            Mode = 'a'
        else:
            Mode = 'w'
              
        #open a debug file and write the debug string to it
        with open(self.Tags_Dir + Filename, Mode) as Log_File:
            Log_File.write(Log_String)
    

    def Make_Write_Log(self, All_Successes, Rename=True, Backup=None):
        '''
        Creates a log string of all tags that were saved and renames
        the tags from their temp filepaths to their original filepaths.
        Returns the created log string
        Raises TypeError if the Tag's status is not in (True,False,None)
        
        Renaming is done by removing '.temp' from the end of all files
        mentioned in 'All_Successes' having a value of True.
        The log consists of a section showing which tags were properly
        loaded and processed, a section showing tags were either not
        properly loaded or not properly processed, and a section showing
        which tags were either not loaded or ignored during processing.

        Required arguments:
            All_Successes(dict)
        Optional arguments:
            Rename(bool)
            Backup(bool)
            
        'All_Successes' must be a dict with the same structure
        as self.Tags, but with bools instead of tags.
        All_Successes[Cls_ID][Tag_Path] = True/False/None

        True  = Tag was properly loaded and processed
        False = Tag was not properly loaded or not properly processed
        None  = Tag was not loaded or ignored during processing

        If 'Backup' is True and a file already exists with the name
        that a temp file is going to be renamed to, the currently
        existing filename will be appended with '.backup'

        If 'Rename' is True then the tags are expected to be in a
        temp file form where their filename ends with '.temp'
        Attempts to remove '.temp' from all tags if 'Rename' == True

        The 'Tag_Path' key of each entry in All_Successes[Cls_ID]
        are expected to be the original, non-temp filepaths. The
        temp filepaths are assumed to be (Tag_Path + '.temp').
        '''
        
        if Backup is None:
            Backup = self.Backup_Old_Tags
        
        Error_String = Success_String = Ignored_String = "\n\nThese tags were "
        
        Success_String += "properly loaded and processed:\n"
        Error_String   += "improperly loaded or processed:\n"
        Ignored_String += "not loaded or ignored during processing:\n"
        
        #loop through each tag
        for Cls_ID in sorted(All_Successes):
            Write_Successes = All_Successes[Cls_ID]
                    
            Success_String += "\n" + Cls_ID
            Error_String   += "\n" + Cls_ID
            Ignored_String += "\n" + Cls_ID
            
            for Tag_Path in sorted(Write_Successes):
                Status = Write_Successes[Tag_Path]
                
                #if we had no errors trying to convert the tag
                if Status is True:
                    
                    Success_String += "\n    " + Tag_Path

                    Tag_Path = self.Tags_Dir + Tag_Path

                    if Rename:
                        if not Backup or isfile(Tag_Path + ".backup"):
                            '''try to delete the tag if told to not backup tags
                            OR if there's already a backup with its name'''
                            try:
                                remove(Tag_Path)
                            except Exception:
                                Success_String += ('\n        Could not '+
                                                   'delete original file.')
                        else:
                            '''Otherwise try to rename the old
                            files to the backup file names'''
                            try:
                                rename(Tag_Path, Tag_Path + ".backup")
                            except Exception:
                                Success_String += ('\n        Could not '+
                                                   'backup original file.')
                                
                        #Try to rename the temp file
                        try:
                            rename(Tag_Path + ".temp", Tag_Path)
                        except Exception:
                            Success_String += ("\n        Could not remove "+
                                               "'temp' from filename.")
                            #restore the backup
                            if Backup:
                                try:   rename(Tag_Path + ".backup", Tag_Path)
                                except Exception: pass
                elif Status is False:
                    Error_String += "\n    " + Tag_Path
                elif Status is None:
                    Ignored_String += "\n    " + Tag_Path
                else:
                    raise TypeError('Invalid type for tag write status. '+
                                    'Expected either True, False, or None. Got'+
                                    " '%s' of type '%s'"%(Status,type(Status)))

        return Success_String + Error_String + Ignored_String + '\n'
    

    def Reload_Defs(self, **kwargs):
        """ this function is used to dynamically load and index
        all tag definitions for all valid tags. This allows
        functionality to be extended simply by creating a new
        definition and dropping it into the Defs folder."""

        Module_IDs = []
        
        self.Defs.clear()
        
        if not self.Defs_Path:
            self.Defs_Path = self.Default_Defs_Path

        Valid_Tag_IDs = kwargs.get("Valid_Tag_IDs")
        if not hasattr(Valid_Tag_IDs, '__iter__'):
            Valid_Tag_IDs = None

        #get the path to the tag definitions folder
        self.Defs_Path = kwargs.get("Defs_Path", self.Defs_Path)
        #convert this path into an import path
        self.Defs_Import_Path = self.Defs_Path.replace('\\', '.')
        
        #cut off the trailing '.' if it exists
        if self.Defs_Import_Path.endswith('.'):
            self.Defs_Import_Path = self.Defs_Import_Path[:-1]

        #import the root definitions module to get its absolute path
        Defs_Root_Module = import_module(self.Defs_Import_Path)
        
        '''try to get the absolute folder path of the Defs module'''
        try:
            #Try to get the filepath of the module 
            Defs_Root = split(Defs_Root_Module.__file__)[0]
        except Exception:
            #If the module doesnt have an __init__.py in the folder then an
            #exception will occur trying to get '__file__' in the above code.
            #This method must be used instead(which I think looks kinda hacky)
            Defs_Root = tuple(Defs_Root_Module.__path__)[0]

        '''Log the location of every python file in the defs root'''
        #search for possibly valid definitions in the defs folder
        for root, directories, files in os.walk(Defs_Root):
            for module_path in files:
                base, ext = splitext(module_path)
                
                Folder = root.split(Defs_Root)[-1]
                
                #make sure the file name ends with .py and isn't already loaded
                if ext.lower() in (".py", ".pyw") and not(base in Module_IDs):
                    Module_IDs.append((Folder + '.' + base).replace('\\', '.'))

        #load the defs that were found 
        for Module_ID in Module_IDs:
            Def_Module = None
            
            #try to import the Definition module
            try:
                Def_Module = import_module(self.Defs_Import_Path + Module_ID)
            except Exception:
                if self.Debug >= 1:
                    print(format_exc() + "\nThe above exception occurred " +
                          "while trying to import a tag definition.")
                    continue

            #make sure this is a valid tag module by making a few checks
            if hasattr(Def_Module, 'Construct'):
                '''finally, try to add the definition
                and its constructor to the lists'''
                try:
                    Def = Def_Module.Construct()
                    
                    try:
                        '''if a def doesnt have a usable Cls_ID then skip it'''
                        Cls_ID = Def.Cls_ID
                        if not bool(Cls_ID):
                            continue

                        '''if it does though, add it to the definitions'''
                        if Valid_Tag_IDs is None or Cls_ID in Valid_Tag_IDs:
                            self.Add_Def(Def)
                    except Exception:
                        if self.Debug >= 3:
                            print(format_exc())
                            
                except Exception:
                    if self.Debug >= 2:
                        print(format_exc() + "\nThe above exception occurred "+
                              "while trying to load a tag definition.")


    def Extend_Tags(self, New_Tags, Replace=True):
        '''
        Adds all entries from New_Tags to this Libraries Tags.

        Required arguments:
            New_Tags(iterable)
        Optional arguments:
            Replace(bool)

        Replaces tags with the same name if 'Replace' is True.
        Default is True
        
        If 'Replace' is False, attempts to rename conflicting tag paths.
        self.Rename_Tries is the max number of attempts to rename a tag path.
        '''
        
        if not hasattr(self, "Tags") or not isinstance(self.Tags, dict):
            self.Reset_Tags()

        '''organize New_Tags in the way the below algorithm requires'''
        New_Tags = self.Iter_to_Collection(New_Tags)

        #make these local for faster referencing
        Get_Unique_Filename = self.Get_Unique_Filename
        Tags = self.Tags
            
        for Cls_ID in New_Tags:
            if Cls_ID not in Tags:
                Tags[Cls_ID] = New_Tags[Cls_ID]
            else:
                for Tag_Path in list(New_Tags[Cls_ID]):
                    Src = New_Tags[Cls_ID]
                    Dest = Tags[Cls_ID]
                    
                    #if this IS the same tag then just skip it
                    if Dest[Tag_Path] is Src[Tag_Path]:
                        continue
                    
                    if Tag_Path in Dest:
                        if Replace:
                            Dest[Tag_Path] = Src[Tag_Path]
                        else:
                            New_Path = Get_Unique_Filename(Tag_Path, Dest, Src)
                            
                            Dest[New_Path] = Src[Tag_Path]
                            Dest[New_Path].Tag_Path = New_Path
                            Src[New_Path] = Src[Tag_Path]
                    else:
                        Dest[Tag_Path] = Src[Tag_Path]

        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        

    def Index_Tags(self):
        '''
        Allocates empty dict entries in self.Tags under
        the proper Cls_ID for each tag found in self.Tags_Dir.
        
        The created dict keys are the paths of the tag relative to
        self.Tags_Dir and the values are set to None.

        Returns the number of tags that were found in the folder.
        '''
        
        self.Tags_Dir     = self.Tags_Dir.replace('/', '\\')
        self.Tags_Indexed = 0

        #local references for faster access
        ID_Ext_Get = self.ID_Ext_Map.get
        Get_Cls_ID = self.Get_Cls_ID
        Tags_Get = self.Tags.get
        Tags_Dir = self.Tags_Dir
        Check    = self.Check_Extension
        
        for root, directories, files in os.walk(Tags_Dir):
            for filename in files:
                filepath = join(root, filename)
                Cls_ID   = Get_Cls_ID(filepath)
                Tag_Cls_Coll     = Tags_Get(Cls_ID)
                self.Current_Tag = filepath
                
                '''Check that the Cls_ID exists in self.Tags and
                make sure we either aren't validating extensions, or that
                the files extension matches the one for that Cls_ID.'''
                if (Tag_Cls_Coll is not None and (not Check or
                    splitext(filename.lower())[-1] == ID_Ext_Get(Cls_ID))):
                    
                    '''if Cls_ID is valid, create a new mapping in Tags
                    using its filepath (minus the Tags_Dir) as the key'''
                    Tag_Path = filepath.split(Tags_Dir)[-1]
                    #Make sure the tag isn't already loaded
                    if Tag_Path not in Tag_Cls_Coll:
                        Tag_Cls_Coll[Tag_Path] = None
                        self.Tags_Indexed += 1
                    
        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        
        return self.Tags_Indexed


    def Load_Tags(self, Paths = None):
        '''
        Goes through each Cls_ID in self.Tags and attempts to
        load each tag that is currently indexed, but that isnt loaded.
        Each entry in self.Tags is a dict where each key is a
        tag's filepath relative to self.Tags_Dir and the value is
        the tag itself. If the tag isn't loaded the value is None.
        
        If an exception occurs while constructing a tag, the offending
        tag will be removed from self.Tags[Cls_ID] and a
        formatted exception string along with the name of the offending
        tag will be printed to the console.
        
        Returns the number of tags that were successfully loaded.

        If 'Paths' is a string, this function will try to load just
        the specified tag. If successful, the loaded tag will be returned.
        If 'Paths' is an iterable, this function will try to load all
        the tags whose paths are in the iterable. Return value is normal.
        
        If self.Allow_Corrupt == True, tags will still be returned as
        successes even if they are corrupted. This is a debugging tool.
        '''
        
        #local references for faster access
        Dir       = self.Tags_Dir
        Tags      = self.Tags
        Allow     = self.Allow_Corrupt
        New_Tag   = None
        Build_Tag = self.Build_Tag

        '''decide if we are loading a single tag, a collection
        of tags, or all tags that have been indexed'''
        if Paths is None:
            Paths_Coll = Tags
        else:
            Get_Cls_ID = self.Get_Cls_ID
            Paths_Coll = {}
            
            if isinstance(Paths, str):
                Paths = (Paths,)
            elif not hasattr(Paths, '__iter__'):
                raise TypeError("'Paths' must be either a filepath string "+
                                "or some form of iterable containing "+
                                "strings, not '%s'" % type(Paths))

            #loop over each Tag_Path and create an entry for it in Paths_Coll
            for Tag_Path in Paths:
                '''make sure each supplied Tag_Path
                is relative to self.Tags_Dir'''
                Tag_Path = relpath(Tag_Path, Dir)
                Cls_ID   = Get_Cls_ID(join(Dir, Tag_Path))
                
                if Cls_ID is not None:
                    if isinstance(Tags.get(Cls_ID), dict):
                        Paths_Coll[Cls_ID][Tag_Path] = None
                    else:
                        Paths_Coll[Cls_ID] = { Tag_Path:None }
                else:
                    raise LookupError("Couldn't locate Cls_ID for:\n    "+Paths)
        

        #Loop over each Cls_ID in the tag paths to load in sorted order
        for Cls_ID in sorted(Paths_Coll):
            Tag_Coll = Tags.get(Cls_ID)

            if not isinstance(Tag_Coll, dict):
                Tag_Coll = Tags[Cls_ID] = {}
            
            #Loop through each Tag_Path in Coll in sorted order
            for Tag_Path in sorted(Paths_Coll[Cls_ID]):
                
                #only load the tag if it isnt already loaded
                if Tag_Coll.get(Tag_Path) is None:
                    self.Current_Tag = Tag_Path
                        
                    '''incrementing Tags_Loaded and decrementing Tags_Indexed
                    in this loop is done for reporting the loading progress'''
                    
                    try:
                        New_Tag = Build_Tag(Filepath = Dir+Tag_Path,
                                            Allow_Corrupt = Allow)
                        Tag_Coll[Tag_Path] = New_Tag
                        self.Tags_Loaded += 1
                    except (OSError, MemoryError) as e:
                        print(format_exc())
                        print('Not enough accessable memory to continue '+
                              'loading tags. Ran out while opening\\reading:'+
                              ('\n    %s\n    Remaining unloaded tags will ' +
                               'be de-indexed and skipped\n') % Tag_Path)
                        del Tag_Coll[Tag_Path]
                        self.Clear_Unloaded_Tags()
                        return
                    except Exception:
                        print(format_exc())
                        print('Above error encountered while opening\\reading:'+
                              '\n    %s\n    Tag may be corrupt\n' % Tag_Path )
                        del Tag_Coll[Tag_Path]
                    self.Tags_Indexed -= 1

        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        
        return self.Tags_Loaded
    

    def Reset_Tags(self, Cls_IDs=None):
        '''
        Resets the dicts of the specified Tag_IDs in self.Tags.
        Raises TypeError if 'Cls_IDs' is not an iterable or dict.

        Optional arguments:
            Cls_IDs(iterable, dict)
            
        If 'Cls_IDs' is None or unsupplied, resets the entire Tags.
        '''
        
        if Cls_IDs is None:
            Cls_IDs = self.Tags

        if isinstance(Cls_IDs, dict):
            Cls_IDs = tuple(Cls_IDs)
        elif isinstance(Cls_IDs, str):
            Cls_IDs = (Cls_IDs,)
        elif not hasattr(Cls_IDs, '__iter__'):
            raise TypeError("'Cls_IDs' must be some form of iterable.")
        
        for Cls_ID in Cls_IDs:
            #create a dict to hold all tags of one type.
            #Tags are indexed by their filepath
            self.Tags[Cls_ID] = {}

        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        

    def Tally_Tags(self):
        '''
        Goes through each Cls_ID in self.Tags and each of the
        collections in self.Tags[Cls_ID] and counts how many
        tags are indexed and how many are loaded.

        Sets self.Tags_Loaded to how many loaded tags were found and
        sets self.Tags_Indexed to how many indexed tags were found.
        '''
        loaded = indexed = 0
        Tags = self.Tags
        
        #Recalculate how many tags are loaded and indexed
        for Cls_ID in Tags:
            Coll = Tags[Cls_ID]
            for Path in Coll:
                if Coll[Path] is None:
                    indexed += 1
                else:
                    loaded += 1

        self.Tags_Loaded = loaded
        self.Tags_Indexed = indexed


    def Write_Tags(self, **kwargs):
        '''
        Goes through each Cls_ID in self.Tags and attempts
        to save each tag that is currently loaded.
        
        Any exceptions that occur while writing the tags will be converted
        to formatted strings and concatenated together along with the name
        of the offending tags into a single 'Exceptions' string.

        Returns a 'Write_Statuses' dict and the 'Exceptions' string.
        Write_Statuses is used with self.Make_Tag_Write_Log() to
        rename all temp tag files to their non-temp names, backup the
        original tags, and make a log string to write to a log file.
        The structure of the Write_Statuses dict is as follows:
        Write_Statuses[Cls_ID][Tag_Path] = True/False/None. 

        True  = Tag was properly saved
        False = Tag could not be saved
        None  = Tag was not saved
        
        Optional arguments:
            Print_Errors(bool)
            Int_Test(bool)
            Backup(bool)
            Temp(bool)
            
        If 'Print_Errors' is True, exceptions will be printed as they occur.
        If 'Int_Test' is True, each tag will be quick loaded after it is written
        to test its data integrity. Quick loading means skipping raw data.
        If 'Temp' is True, each tag written will be suffixed with '.temp'
        If 'Backup' is True, any tags that would be overwritten are instead
        renamed with the extension '.backup'. If a backup already exists
        then the oldest one is kept and the current file is deleted.

        Passes 'Backup', 'Temp', and 'Int_Test' on to each tag's Write() method.
        '''
        Print_Errors = kwargs.get('Print_Errors', True)
        Int_Test = kwargs.get('Int_Test', self.Int_Test)
        Backup   = kwargs.get('Backup',   self.Backup_Old_Tags)
        Temp     = kwargs.get('Temp',     self.Write_as_Temp)
        
        Write_Statuses = {}
        Exceptions = '\n\nExceptions that occurred while writing tags:\n\n'
        
        Dir = self.Tags_Dir
        
        #Loop through each Cls_ID in self.Tags in order
        for Cls_ID in sorted(self.Tags):
            Coll = self.Tags[Cls_ID]
            Write_Statuses[Cls_ID] = These_Statuses = {}
            
            #Loop through each Tag_Path in Coll in order
            for Tag_Path in sorted(Coll):
            
                #only write the tag if it is loaded
                if Coll[Tag_Path] is not None:
                    self.Current_Tag = Tag_Path
                    
                    try:
                        Coll[Tag_Path].Write(Filepath=Dir+Tag_Path, Temp=Temp,
                                             Int_Test=Int_Test, Backup=Backup)
                        These_Statuses[Tag_Path] = True
                    except Exception:
                        tmp = (format_exc() + '\n\n' + 
                               'Above error occurred while writing the tag:\n'+
                               '    ' + str(Tag_Path) + '\n' +
                               '    Tag may be corrupt.\n')
                        Exceptions += '\n' + tmp + '\n'
                        if Print_Errors:
                            print(tmp)
                        These_Statuses[Tag_Path] = False
                    
        return(Write_Statuses, Exceptions)
