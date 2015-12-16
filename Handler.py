'''
A class for organizing and loading collections of tags of various Tag_IDs.

Handlers are meant to organize large quantities of different types of
tags which all reside in the same 'Tags_Directory' root folder. A Handler
contains methods for indexing all valid tags within its Tags_Directory,
loading all indexed tags, writing all loaded tags back to their files, and
resetting the Tag_Collection or individual Cls_ID collections to empty.

Handlers contain a basic log creation function for logging successes
and failures when saving tags. This function can also rename all temp files
generated during the save operation to their non-temp filenames and logs all
errors encountered while trying to rename these files and backup old files.
'''
import os

from datetime import datetime
from os import remove, rename
from os.path import splitext, join, isfile, relpath
from sys import getrecursionlimit
from traceback import format_exc

from supyr_struct import Constructor
from supyr_struct.Defs import Tag_Def, Tag_Obj


class Handler():
    '''
    A class for organizing and loading collections of tags of various Tag_IDs.

    Handlers are meant to organize large quantities of different types of
    tags which all reside in the same 'Tags_Directory' root folder. This class
    contains methods for indexing all valid tags within self.Tags_Directory,
    loading all indexed tags, and writing all loaded tags back to their files.
    
    Handlers contain a basic log creation function for logging successes
    and failures when saving tags. This function can also rename all temp files
    generated during the save operation to their non-temp filenames and logs all
    errors encountered while trying to rename these files and backup old files.

    Tags saved through a Handler are not saved to the Tag.Tag_Path string,
    but rather to self.Tags_Directory + Tag_Path where Tag_Path is the key that
    the Tag is under in self.Tag_Collection[Cls_ID].
    
    Refer to this classes __init__.__doc__ for descriptions of
    the properties in this class that aren't described below.
    
    Object Properties:
        object:
            Constructor
        int:
            Rename_Tries
            Debug
            Tags_Indexed
            Tags_Loaded
        str:
            Current_Tag ---------- The Tag_Path of the current tag that this
                                   Handler is indexing/loading/writing.
            Log_Filename
            Tags_Directory
        bool:
            Allow_Corrupt
            Check_Extension
            Write_as_Temp
            Backup_Old_Tags
        dict:
            Tag_Collection
            ID_Ext_Mapping -- A dict shared with self.Constructor which
                              maps each Cls_ID(key) to its extension(value)
            
    Object Methods:
        Get_Unique_Filename(Tag_Path[str], Dest[iterable], Src[iterable]=(),
                            Rename_Tries[int]=0)
        Iter_to_Tag_Collection(New_Tags[dict], Tag_Collection[iterable]=None)
        Extend_Tags(New_Tags[dict], Replace[bool]=True)
        Index_Tags()
        Load_Tags()
        Reset_Tags(Tag_IDs[dict]=None)
        Write_Tags(Print_Errors[bool]=True, Temp[bool]=True,
                         Backup[bool]=True, Test[bool]=True)
        Make_Tag_Write_Log(All_Successes[dict],
                           Backup[bool]=True, Rename[bool]=True)
        Make_Log_File(Log_String[str])
    '''
    
    Log_Filename = ''

    def __init__(self, **kwargs):
        '''
        Initializes a Handler with the supplied keyword arguments.
        If kwargs['Constructor'] is a class, all kwargs will be passed
        on during the construction of the class. If kwargs['Constructor']
        doesnt exist or is None then a default Constructor will be built.
        Raises a TypeError if 'Constructor' is either not a class or
        is not a subclass of supyr_struct.Constructor.Constructor.
        
        Keyword arguments:
        
        #type
        Constructor -- The Constructor class that this Handler
                       will use to build any and all tags. After it is
                       built, self.ID_Ext_Mapping is set to the
                       ID_Ext_Mapping of self.Constructor.
                           
        #int
        Debug ------------ The level of debugging information to show. 0 to 10.
                           The higher the number, the more information shown.
                           Currently this is of very limited use.
        Rename_Tries ----- The number of times that self.Get_Unique_Filename()
                           can fail to make the 'Tag_Path' string argument
                           unique before raising a RuntimeError. This renaming
                           process is used when calling self.Extend_Tags() with
                           'Replace'=False to merge a collection of tags into
                           the Tag_Collection of this Handler.
        Tags_Indexed ----- This is the number of tags that were found when
                           self.Index_Tags() was run.
        Tags_Loaded ------ This is the number of tags that were loaded when
                           self.Load_Tags() was run.
        
        #str
        Tags_Directory --- A filepath string pointing to the working directory
                           which all our tags are loaded from and written to.
                           When adding a tag to Tag_Collection[Cls_ID][Tag_Path]
                           the Tag_Path key is the path to the tag relative to
                           this Tags_Directory string. So if the Tags_Directory
                           string were 'c:/tags/' and a tag were located in
                           'c:/tags/test/a.tag', Tag_Path would be 'test/a.tag'
        Log_Filename ----- The name of the file all logs will be written to.
                           The file will be created in the Tags_Directory folder
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
        Tag_Collection --- A dict of dicts which holds every loaded tag. A
                           dict inside the Tag_Collection holds all of a single
                           type of tag, with each of the tags keyed by their
                           tag path, which is relative to self.Tags_Directory.
                           Accessing a tag is done like so:
                           Tag_Collection[Cls_ID][Tag_Path] = Tag_Obj

        #iterable
        Valid_Tag_IDs ---- Some form of iterable containing the Cls_ID strings
                           that this Handler and its Tag_Constructer will
                           be working with. You may instead provide a single
                           Cls_ID string if working with just one kind of tag.
        '''
        
        self.Current_Tag = ""
        self.Tags_Indexed = 0
        self.Tags_Loaded = 0
        self.Tag_Collection = {}
        self.Tags_Directory = os.path.abspath(os.curdir) + "\\tags\\"
        
        #Valid_Tag_IDs will determine which tag types are possible to load
        if isinstance(kwargs.get("Valid_Tag_IDs"), str):
            kwargs["Valid_Tag_IDs"] = tuple([kwargs["Valid_Tag_IDs"]])
        
        self.Rename_Tries = kwargs.get("Rename_Tries", getrecursionlimit())
        self.Check_Extension = kwargs.get("Check_Extension", True)
        self.Backup_Old_Tags = kwargs.get("Backup_Old_Tags", True)
        self.Log_Filename = kwargs.get("Log_Filename", 'log.log')
        self.Allow_Corrupt = kwargs.get("Allow_Corrupt", False)
        self.Write_as_Temp = kwargs.get("Write_as_Temp", True)
        self.Debug = kwargs.get("Debug", 0)
            
        if kwargs.get("Constructor"):
            self.Constructor = kwargs["Constructor"]

            #if kwargs["Constructor"] is not a class, raise a TypeError
            if not isinstance(self.Constructor, type):
                raise TypeError("'Constructor' must be an instance of " +
                                "%s, not '%s'." %(type, type(self.Constructor)))

            #if the provided Constructor is a class and it
            #is a subclass of Constructor, then build it
            if issubclass(self.Constructor, Constructor.Constructor):
                self.Constructor = self.Constructor(self, **kwargs)
            else:
                raise TypeError("'Constructor' must be a subclass of " +
                                "%s, not '%s'." %
                                (Constructor, type(self.Constructor)))
            
        else:
            self.Constructor = Constructor.Constructor(self, **kwargs)

        #the constructor and handler need to share this mapping
        self.ID_Ext_Mapping = self.Constructor.ID_Ext_Mapping

        #make slots in self.Tag_Collection for the types we want to load
        self.Reset_Tags(self.Constructor.Definitions.keys())
            
        self.Tags_Directory = kwargs.get("Tags_Directory",self.Tags_Directory)
        self.Tag_Collection = kwargs.get("Tag_Collection", self.Tag_Collection)
            
        #Make sure the slashes are all uniform
        self.Tags_Directory = self.Tags_Directory.replace('/', '\\')

        #make sure there is an ending folder slash on the tags directory
        if len(self.Tags_Directory) and not self.Tags_Directory.endswith("\\"):
            self.Tags_Directory += '\\'


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
            

    def Iter_to_Tag_Collection(self, New_Tags, Tag_Collection=None):
        '''
        Converts an arbitrarily deep collection of iterables
        into a two level deep Tag_Collection of nested dicts
        containing Tag_Objs using the following structure:
        Tag_Collection[Cls_ID][Tag_Path] = Tag_Obj
        
        Returns the organized Tag_Collection.
        Raises TypeError if 'Tag_Collection' is not a dict

        Required arguments:
            New_Tags(iterable)
        Optional arguments:
            Tag_Collection(dict)
            
        If Tag_Collection is None or unsupplied, a
        new dict will be created and returned.
        Any duplicate tags in the provided 'New_Tags'
        will be overwritten by the last one added.
        '''
        
        if Tag_Collection is None:
            Tag_Collection = dict()

        if not isinstance(Tag_Collection, dict):
            raise TypeError("The argument 'Tag_Collection' must be a dict.")
            
        if isinstance(New_Tags, Tag_Obj.Tag_Obj):
            if New_Tags.Cls_ID not in Tag_Collection:
                Tag_Collection[New_Tags.Cls_ID] = dict()
            Tag_Collection[New_Tags.Cls_ID][New_Tags.Tag_Path] = New_Tags
        elif isinstance(New_Tags, dict):
            for key in New_Tags:
                self.Iter_to_Tag_Collection(New_Tags[key], Tag_Collection)
        elif hasattr(New_Tags, '__iter__'):
            for element in New_Tags:
                self.Iter_to_Tag_Collection(Tag_Collection, element)

        return Tag_Collection


    def Extend_Tags(self, New_Tags, Replace=True):
        '''
        Adds all entries from New_Tags to this handlers Tag_Collection.

        Required arguments:
            New_Tags(iterable)
        Optional arguments:
            Replace(bool)

        Replaces tags with the same name if 'Replace' is True.
        Default is True
        
        If 'Replace' is False, attempts to rename conflicting tag paths.
        self.Rename_Tries is the max number of attempts to rename a tag path.
        '''
        
        if (not hasattr(self, "Tag_Collection") or
            not isinstance(self.Tag_Collection, dict)):
            self.Reset_Tags()

        '''organize New_Tags in the way the below algorithm requires'''
        New_Tags = self.Iter_to_Tag_Collection(New_Tags)

        #make these local for faster referencing
        Get_Unique_Filename = self.Get_Unique_Filename
        Tag_Collection = self.Tag_Collection
            
        for Cls_ID in New_Tags:
            if Cls_ID not in Tag_Collection:
                Tag_Collection[Cls_ID] = New_Tags[Cls_ID]
            else:
                for Tag_Path in list(New_Tags[Cls_ID]):
                    Src = New_Tags[Cls_ID]
                    Dest = Tag_Collection[Cls_ID]
                    
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
        Allocates empty dict entries in self.Tag_Collection under
        the proper Cls_ID for each tag found in self.Tags_Directory.
        
        The created dict keys are the paths of the tag relative to
        self.Tags_Directory and the values are set to None.

        Returns the number of tags that were found in the folder.
        '''
        

        self.Tags_Directory = self.Tags_Directory.replace('/', '\\')
        self.Tags_Indexed = 0

        Tag_Coll   = self.Tag_Collection
        Tags_Dir   = self.Tags_Directory
        Mapping    = self.ID_Ext_Mapping
        Get_Cls_ID = self.Constructor.Get_Cls_ID
        Check      = self.Check_Extension

        for root, directories, files in os.walk(Tags_Dir):
            for filename in files:
                filepath = join(root, filename)
                Cls_ID = Get_Cls_ID(filepath)
                self.Current_Tag = filepath
                #if the Cls_ID is valid, create a new spot
                #in the Tag_Collection using its filepath
                #(minus the Tags_Directory) as the key
                
                '''Check that the Cls_ID exists in self.Tag_Collection and
                make sure we either aren't validating extensions, or that
                the files extension matches the one for that Cls_ID.'''
                if (Tag_Coll.get(Cls_ID) is not None and (not Check or
                    splitext(filename.lower())[-1] == Mapping.get(Cls_ID) )):
                    
                    Tag_Path = filepath.split(Tags_Dir)[-1]
                    #Make sure the tag isn't already loaded
                    if Tag_Coll[Cls_ID].get(Tag_Path) is None:
                        Tag_Coll[Cls_ID][Tag_Path] = None
                        self.Tags_Indexed += 1
                        
        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        
        return self.Tags_Indexed


    def Load_Tags(self, Paths = None):
        '''
        Goes through each Cls_ID in self.Tag_Collection and attempts to
        load each tag that is currently indexed, but that isnt loaded.
        Each entry in self.Tag_Collection is a dict where each key is a
        tag's filepath relative to self.Tags_Directory and the value is
        the tag itself. If the tag isn't loaded the value is None.
        
        If an exception occurs while constructing a tag, the offending
        tag will be removed from self.Tag_Collection[Cls_ID] and a
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
        
        New_Tag = None
        Construct_Tag = self.Constructor.Construct_Tag
        Dir = self.Tags_Directory

        #Decide if loading a single tag or a collection of them
        if Paths is None:
            Paths_Coll = self.Tag_Collection
        else:
            Get_Cls_ID = self.Constructor.Get_Cls_ID
            Paths_Coll = {}
            
            if isinstance(Paths, str):
                '''make sure the supplied Tag_Path
                is relative to self.Tags_Directory'''
                Paths = relpath(Paths, Dir)
                Cls_ID = Get_Cls_ID(join(Dir, Paths))
                
                if Cls_ID is not None:
                    Paths_Coll[Cls_ID] = {Paths:None}
                else:
                    raise LookupError('Couldnt locate Cls_ID for:\n    '+Paths)
                    
            elif hasattr(Paths, '__iter__'):
                for Tag_Path in Paths:
                    '''make sure the supplied Tag_Path
                    is relative to self.Tags_Directory'''
                    Tag_Path = relpath(Tag_Path, Dir)
                    Cls_ID = Get_Cls_ID(Tag_Path)
                    
                    if Cls_ID is not None:
                        if isinstance(Tag_Coll.get(Cls_ID), dict):
                            Paths_Coll[Cls_ID][Tag_Path] = None
                        else:
                            Paths_Coll[Cls_ID] = {Tag_Path:None}
                    else:
                        raise LookupError('Could not locate Cls_ID for:\n',
                                          '    '+Paths)
            else:
                raise TypeError("'Paths' must be either a filepath "+
                                "string or some form of iterable containing "+
                                "strings, not '%s'" % type(Paths))
        

        #Loop through each Cls_ID in self.Tag_Collection in order
        for Cls_ID in sorted(Paths_Coll):
            Tag_Coll = self.Tag_Collection.get(Cls_ID)

            if not isinstance(Tag_Coll, dict):
                Tag_Coll = self.Tag_Collection[Cls_ID] = {}
            
            #Loop through each Tag_Path in Coll in order
            for Tag_Path in sorted(Paths_Coll[Cls_ID]):
                #only load the tag if it isnt already loaded
                if Tag_Coll.get(Tag_Path) is None:
                    self.Current_Tag = Tag_Path
                        
                    '''increasing Tags_Loaded and lowering Tags_Indexed in
                    this loop is done for reporting the loading progress'''
                    
                    try:
                        New_Tag = Construct_Tag(Filepath=Dir+Tag_Path,
                                               Allow_Corrupt=self.Allow_Corrupt)
                        Tag_Coll[Tag_Path] = New_Tag
                        self.Tags_Loaded += 1
                    except Exception:
                        print(format_exc())
                        print('Above error encountered while opening\\reading:'+
                              '\n    %s\n    Tag may be corrupt\n' % Tag_Path )
                        del Tag_Coll[Tag_Path]
                    self.Tags_Indexed -= 1

        #recount how many tags are loaded/indexed
        self.Tally_Tags()
                        
        #if only a single tag string was provided to be loaded, return it.
        if isinstance(Paths, str):
            return New_Tag
        else:
            return self.Tags_Loaded


    def Reset_Tags(self, Cls_IDs=None):
        '''
        Resets the dicts of the specified Tag_IDs in self.Tag_Collection.
        Raises TypeError if 'Cls_IDs' is not an iterable or dict.

        Optional arguments:
            Cls_IDs(iterable, dict)
            
        If 'Cls_IDs' is None or unsupplied, resets the entire Tag_Collection.
        '''
        
        if Cls_IDs is None:
            Cls_IDs = list(self.Tag_Collection)

        if isinstance(Cls_IDs, dict):
            tmp = Cls_IDs
            Cls_IDs = []
            for key in tmp:
                Cls_IDs.append(tmp[key])
        elif isinstance(Cls_IDs, str):
            Cls_IDs = (Cls_IDs,)
        elif not hasattr(Cls_IDs, '__iter__'):
            raise TypeError("'Cls_IDs' must be some form of iterable.")
        
        for Cls_ID in Cls_IDs:
            #create a dict to hold all tags of one type.
            #Tags are indexed by their filepath
            self.Tag_Collection[Cls_ID] = {}

        #recount how many tags are loaded/indexed
        self.Tally_Tags()
        

    def Tally_Tags(self):
        '''
        Goes through each Cls_ID in self.Tag_Collection and each of the
        collections in self.Tag_Collection[Cls_ID] and counts how many
        tags are indexed and how many are loaded.

        Sets self.Tags_Loaded to how many loaded tags were found and
        sets self.Tags_Indexed to how many indexed tags were found.
        '''
        loaded = indexed = 0
        
        #Recalculate how many tags are loaded and indexed
        for Cls_ID in self.Tag_Collection:
            Coll = self.Tag_Collection[Cls_ID]
            for Path in Coll:
                if Coll[Path] is None:
                    indexed += 1
                else:
                    loaded += 1

        self.Tags_Loaded = loaded
        self.Tags_Indexed = indexed


    def Write_Tags(self, Print_Errors=True, Test=True, Backup=None, Temp=None):
        '''
        Goes through each Cls_ID in self.Tag_Collection and attempts
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
            Test(bool)
            Backup(bool)
            Temp(bool)
            
        If 'Print_Errors' is True, exceptions will be printed as they occur.
        If 'Test' is True, each tag will be quick loaded after it is written
        to test its data integrity. Quick loading means skipping raw data.
        If 'Temp' is True, each tag written will be suffixed with '.temp'
        If 'Backup' is True, any tags that would be overwritten are instead
        renamed with the extension '.backup'. If a backup already exists
        then the oldest one is kept and the current file is deleted.

        Passes 'Backup', 'Temp', and 'Test' on to each tag's Write() method.
        '''
        
        Write_Statuses = {}
        Exceptions = '\n\nExceptions that occurred while writing tags:\n\n'
        
        Dir = self.Tags_Directory
        if Backup is None: Backup = self.Backup_Old_Tags
        if Temp is None:   Temp   = self.Write_as_Temp
        
        #Loop through each Cls_ID in self.Tag_Collection in order
        for Cls_ID in sorted(self.Tag_Collection):
            Coll = self.Tag_Collection[Cls_ID]
            Write_Statuses[Cls_ID] = {}
            
            #Loop through each Tag_Path in Coll in order
            for Tag_Path in sorted(Coll):
            
                #only write the tag if it is loaded
                if Coll[Tag_Path] is not None:
                    self.Current_Tag = Tag_Path
                    
                    try:
                        Coll[Tag_Path].Write(Filepath=Dir+Tag_Path, Temp=Temp,
                                             Test=Test, Backup=Backup)
                        Write_Statuses[Cls_ID][Tag_Path] = True
                    except Exception:
                        tmp = ((format_exc() + '\n\n' + 
                               'Above error occurred while writing the tag:'+
                               '\n    %s\n    Tag may be corrupt.\n')%Tag_Path)
                        Exceptions += '\n' + tmp + '\n'
                        if Print_Errors:
                            print(tmp)
                        Write_Statuses[Cls_ID][Tag_Path] = False
                    
        return(Write_Statuses, Exceptions)
    

    def Make_Tag_Write_Log(self, All_Successes, Rename=True, Backup=None):
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
        as self.Tag_Collection, but with bools instead of tags.
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
        
        if Backup is None: Backup = self.Backup_Old_Tags
        
        Error_String = Success_String=Ignored_String = '\n\nThese tags were '
        
        Success_String += 'properly loaded and processed:\n'
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

                    Tag_Path = self.Tags_Directory + Tag_Path

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
                            rename((Tag_Path + ".temp"), Tag_Path)
                        except Exception:
                            Success_String += ("\n        Could not remove "+
                                               "'temp' from filename.")
                            #restore the backup
                            if Backup:
                                try:   rename((Tag_Path + ".backup"), Tag_Path)
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
            
        if isfile(self.Tags_Directory + Filename):
            Mode = 'a'
        else:
            Mode = 'w'
              
        #open a debug file and write the debug string to it
        with open(self.Tags_Directory + Filename, Mode) as Log_File:
            Log_File.write(Log_String)
