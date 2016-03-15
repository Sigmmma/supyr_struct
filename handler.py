'''
A class for organizing and loading collections of tags of various Tag_IDs.

Libraries are meant to organize large quantities of different types of
tags which all reside in the same 'tagsdir' root folder. A Handler
contains methods for indexing all valid tags within its tagsdir,
loading all indexed tags, writing all loaded tags back to their files, and
resetting the tags or individual tag_id collections to empty.

Libraries contain a basic log creation function for logging successes
and failures when saving tags. This function can also os.rename all temp files
generated during the save operation to their non-temp filenames and logs all
errors encountered while trying to os.rename these files and backup old files.
'''
import os, sys

from datetime import datetime
from importlib import import_module
from importlib.machinery import SourceFileLoader
from os.path import dirname, split, splitext, join, isfile, relpath
from traceback import format_exc
from types import ModuleType

from supyr_struct.defs.constants import *

class Handler():
    '''
    A class for organizing and loading collections of tags of various Tag_IDs.

    Handlers are meant to organize large quantities of different types of
    tags which all reside in the same 'tagsdir' root folder. This class
    contains methods for indexing all valid tags within self.tagsdir,
    loading all indexed tags, and writing all loaded tags back to their files.
    
    Handlers contain a basic log creation function for logging successes
    and failures when saving tags. This function can also os.rename all temp files
    generated during the save operation to their non-temp filenames and logs all
    errors encountered while trying to os.rename these files and backup old files.

    Tags saved through a Handler are not saved to the Tag.tagpath string,
    but rather to self.tagsdir + tagpath where tagpath is the key that
    the Tag is under in self.tags[tag_id].
    
    Refer to this classes __init__.__doc__ for descriptions of
    the properties in this class that aren't described below.
    
    Object Properties:
        int:
            rename_tries
            debug
            tags_indexed
            tags_loaded
        str:
            current_tag ---------- The tagpath of the current tag that this
                                   Handler is indexing/loading/writing.
            log_filename
            tagsdir
        bool:
            allow_corrupt
            check_extension
            write_as_temp
            backup
        dict:
            tags
            id_ext_map ------ maps each tag_id(key) to its extension(value)
            
    Object Methods:
        get_unique_filename(tagpath[str], dest[iterable], src[iterable]=(),
                            rename_tries[int]=0)
        iter_to_collection(new_tags[dict], tags[iterable]=None)
        extend_tags(new_tags[dict], replace[bool]=True)
        index_tags()
        load_tags()
        reset_tags(Tag_IDs[dict]=None)
        write_tags(print_errors[bool]=True, temp[bool]=True,
                   backup[bool]=True, int_test[bool]=True)
        make_tag_write_log(all_successes[dict],
                           backup[bool]=True, rename[bool]=True)
        make_log_file(logstr[str])
    '''
    
    log_filename            = 'log.log'
    default_tag_cls         = None
    default_import_rootpath = "supyr_struct"
    default_defs_path       = "supyr_struct.defs"

    sys_path_index = -1

    def __init__(self, **kwargs):
        '''
        Initializes a Handler with the supplied keyword arguments.
        
        Keyword arguments:
                           
        #int
        debug ------------ The level of debugging information to show. 0 to 10.
                           The higher the number, the more information shown.
                           Currently this is of very limited use.
        rename_tries ----- The number of times that self.get_unique_filename()
                           can fail to make the 'tagpath' string argument
                           unique before raising a RuntimeError. This renaming
                           process is used when calling self.extend_tags() with
                           'replace'=False to merge a collection of tags into
                           the tags of this Handler.
        tags_indexed ----- This is the number of tags that were found when
                           self.index_tags() was run.
        tags_loaded ------ This is the number of tags that were loaded when
                           self.load_tags() was run.
        
        #str
        tagsdir ---------- A filepath string pointing to the working directory
                           which all our tags are loaded from and written to.
                           When adding a tag to tags[tag_id][tagpath]
                           the tagpath key is the path to the tag relative to
                           this tagsdir string. So if the tagsdir
                           string were 'c:/tags/' and a tag were located in
                           'c:/tags/test/a.tag', tagpath would be 'test/a.tag'
        log_filename ----- The name of the file all logs will be written to.
                           The file will be created in the tagsdir folder
                           if it doesn't exist. If it does exist, the file will
                           be opened and any log writes will be appended to it.
        
        #bool
        allow_corrupt ---- Enables returning corrupt tags rather than discarding
                           them and reporting the exception. Instead, the
                           exception will be printed to the console and the tag
                           will be returned like normal. For debugging use only.
        check_extension -- Whether or not(when indexing tags) to make sure a
                           tag's extension also matches the extension for that
                           tag_id. The main purpose is to prevent loading temp
                           files. This is only useful when overloading the
                           constructors 'get_tag_id' function since the default
                           constructor verifies tags by their extension.
        write_as_temp ---- Whether or not to keep tags as temp files when
                           calling self.write_tags. Overridden by supplying
                           'temp' as a keyword when calling self.write_tags.
        backup ----------- Whether or not to backup a file that exists with the
                           same name as a tag that is being saved. The file will
                           be renamed with the extension '.backup'. If a backup
                           already exists then the oldest backup will be kept.
                           
        #dict
        tags ------------- A dict of dicts which holds every loaded tag. A
                           dict inside the tags holds all of a single
                           type of tag, with each of the tags keyed by their
                           tag path, which is relative to self.tagsdir.
                           Accessing a tag is done like so:
                           tags[tag_id][tagpath] = Tag

        #iterable
        valid_tag_ids ---- Some form of iterable containing the tag_id strings
                           that this Handler and its Tag_Constructer will
                           be working with. You may instead provide a single
                           tag_id string if working with just one kind of tag.
        '''
        
        #this is the filepath to the tag currently being constructed
        self.current_tag  = ''
        self.tags_indexed = self.tags_loaded = 0
        self.tags = {}
        self.tagsdir = os.path.abspath(os.curdir) + pathdiv + "tags" + pathdiv

        self.import_rootpath = ''
        self.defs_filepath = ''
        self.defs_path = ''
        self.id_ext_map = {}
        self.defs = {}
        
        #valid_tag_ids will determine which tag types are possible to load
        if isinstance(kwargs.get("valid_tag_ids"), str):
            kwargs["valid_tag_ids"] = tuple([kwargs["valid_tag_ids"]])
        
        self.debug        = kwargs.get("debug", 0)
        self.rename_tries = kwargs.get("rename_tries", sys.getrecursionlimit())
        self.log_filename = kwargs.get("log_filename", self.log_filename)
        self.backup       = bool(kwargs.get("backup", True))
        self.int_test        = bool(kwargs.get("int_test", True))
        self.allow_corrupt   = bool(kwargs.get("allow_corrupt", False))
        self.write_as_temp   = bool(kwargs.get("write_as_temp", True))
        self.check_extension = bool(kwargs.get("check_extension", True))
        
        self.import_rootpath = kwargs.get("import_rootpath",
                                          self.import_rootpath)
        self.defs_filepath   = kwargs.get("defs_filepath", self.defs_filepath)
        self.defs_path       = kwargs.get("defs_path", self.defs_path)
            
        self.tagsdir = kwargs.get("tagsdir", self.tagsdir).replace('/', pathdiv)
        self.tags    = kwargs.get("tags", self.tags)

        #make sure there is an ending folder slash on the tags directory
        if len(self.tagsdir) and not self.tagsdir.endswith(pathdiv):
            self.tagsdir += pathdiv
            
        self.reload_defs(**kwargs)
        
        #make slots in self.tags for the types we want to load
        self.reset_tags(self.defs.keys())


    def add_def(self, tagdef, id=None, ext=None, endian=None, cls=None):
        '''docstring'''
        if isinstance(tagdef, dict):
            #a descriptor formatted dictionary was provided
            if tag_id is None or ext is None:
                raise TypeError("Could not add new TagDef to constructor. "+
                                "Neither 'id' or 'ext' can be None if "+
                                "'tagdef' is a dict based structure.")
                
            tagdef = tag_def.TagDef(descriptor=tagdef, ext=ext, tag_id=id)
        elif isinstance(tagdef, tag_def.TagDef):
            #a TagDef was provided. nothing to do
            pass
        elif isinstance(tagdef, type) and issubclass(tagdef, tag_def.TagDef):
            #the actual TagDef class was provided
            tagdef = tagdef()
        elif isinstance(tagdef, ModuleType):
            #a whole module was provided
            if hasattr(tagdef, "get"):
                tagdef = tagdef.get()
            else:
                raise AttributeError("The provided module does not have "+
                                     "a 'get' method to get the "+
                                     "TagDef class from.")
        else:
            #no idea what was provided, but we dont care. ERROR!
            raise TypeError("Incorrect type for the provided 'tagdef'.\n"+
                            "Expected %s, %s, or %s, but got %s" %
                            (type(tag_def.TagDef.descriptor),
                             type, ModuleType, type(tagdef)) )
        
        #if a tag_cls is supplied, use it instead of the default one
        if isinstance(cls, tag.Tag):
            tagdef.tag_cls = cls
            
        #if no tag_cls is associated with this TagDef, use the default one
        if tagdef.tag_cls is None:
            tagdef.tag_cls = self.default_tag_cls
            
        self.defs[tagdef.tag_id] = tagdef
        self.id_ext_map[tagdef.tag_id] = tagdef.ext

        return tagdef


    def build_tag(self, **kwargs):
        '''builds and returns a tag object'''        
        tag_id   = kwargs.get("tag_id", None)
        filepath = kwargs.get("filepath", '')
        raw_data = kwargs.get("raw_data", None)
        int_test = kwargs.get("int_test", False)
        allow_corrupt  = kwargs.get("allow_corrupt", self.allow_corrupt)

        #set the current tag path so outside processes
        #have some info on what is being constructed
        self.current_tag = filepath

        if not tag_id:
            tag_id = self.get_tag_id(filepath)
            if not tag_id:
                raise LookupError('Unable to determine tag_id for:' +
                                  '\n' + ' '*BPI + self.current_tag)

        tagdef = self.get_def(tag_id)
        
        #if it could find a TagDef, then use it
        if tagdef:
            new_tag = tagdef.tag_cls(tagpath=filepath,  raw_data=raw_data,
                                     definition=tagdef, int_test=int_test,
                                     allow_corrupt=allow_corrupt, handler=self)
            return new_tag
        
        raise LookupError(("Unable to locate definition for " +
                           "tag type '%s' for file:\n%s'%s'") %
                           (tag_id, ' '*BPI, self.current_tag))
        

    def clear_unloaded_tags(self):
        '''
        Goes through each tag_id in self.tags and each of the
        collections in self.tags[tag_id] and removes any tags
        which are indexed, but not loaded.
        '''
        tags = self.tags
        
        for tag_id in tags:
            coll = tags[tag_id]

            #need to make the collection's keys a tuple or else
            #we will run into issues after deleting any keys
            for path in tuple(coll):
                if coll[path] is None:
                    del coll[path]
                    
        self.tally_tags()


    def get_tag_id(self, filepath):
        '''docstring'''
        if not filepath.startswith('.') and '.' in filepath:
            ext = splitext(filepath)[-1].lower()
        else:
            ext = filepath.lower()
            
        for tag_id in self.id_ext_map:
            if self.id_ext_map[tag_id].lower() == ext:
                return tag_id
    

    def get_def(self, tag_id):
        return self.defs.get(tag_id)
        

    def get_unique_filename(self, tagpath, dest, src=(), rename_tries=0):
        '''
        Does a os.rename operation on the string 'tagpath' which
        increments a number on the end of it if it is a valid
        integer, or adds a new one if there isnt one.
        
        Raises RuntimeError if 'rename_tries' is exceeded.

        Required arguments:
            tagpath(str)
            dest(iterable)
        Optional arguments:
            src(iterable)
            rename_tries(int)

        src and dest are iterables which contain the filepaths to
        check against to see if the generated filename is unique.
        '''
        
        splitpath, ext = splitext(tagpath)
        newpath = splitpath

        #this is the max number of attempts to os.rename a tag
        #that the below routine will attempt. this is to
        #prevent infinite recursion, or really long stalls
        if not isinstance(rename_tries, int) or rename_tries <= 0:
            rename_tries = self.rename_tries

        #sets are MUCH faster for testing membership than lists
        src = set(src)
        dest = set(dest)

        #find the location of the last underscore
        last_us = None
        for i in range(len(splitpath)):
            if splitpath[i] == '_':
                last_us = i

        #if the stuff after the last underscore is not an
        #integer, treat it as if there is no last underscore
        try:
            i = int(splitpath[last_us+1:])
            oldpath = splitpath[:last_us] + '_'
        except Exception:
            i = 0
            oldpath = splitpath + '_'

        #increase rename_tries by the number we are starting at
        rename_tries += i
        
        #make sure the name doesnt already
        #exist in both src or dest
        while (newpath+ext) in dest or (newpath+ext) in src:
            newpath = oldpath + str(i)
            if i > rename_tries:
                raise RuntimeError("Maximum os.rename attempts exceeded " +
                                   "while trying to find a unique name "+
                                   " for the tag:\n    %s" % tagpath)
            i += 1

        return newpath + ext
            

    def iter_to_collection(self, new_tags, tags=None):
        '''
        Converts an arbitrarily deep collection of
        iterables into a two level deep tags of nested
        dicts containing tags using the following structure:
        tags[tag_id][tagpath] = Tag
        
        Returns the organized tags.
        Raises TypeError if 'tags' is not a dict

        Required arguments:
            new_tags(iterable)
        Optional arguments:
            tags(dict)
            
        If tags is None or unsupplied, a
        new dict will be created and returned.
        Any duplicate tags in the provided 'new_tags'
        will be overwritten by the last one added.
        '''
        
        if tags is None:
            tags = dict()

        if not isinstance(tags, dict):
            raise TypeError("The argument 'tags' must be a dict.")
            
        if isinstance(new_tags, tag.Tag):
            if new_tags.tag_id not in tags:
                tags[new_tags.tag_id] = dict()
            tags[new_tags.tag_id][new_tags.tagpath] = new_tags
        elif isinstance(new_tags, dict):
            for key in new_tags:
                self.iter_to_collection(new_tags[key], tags)
        elif hasattr(new_tags, '__iter__'):
            for element in new_tags:
                self.iter_to_collection(tags, element)

        return tags


    def make_log_file(self, logstr):
        '''
        Writes the supplied string to a log file.
        
        Required arguments:
            logstr(str)
            
        If self.log_filename is a non-blank string it will be used as the
        log filename. Otherwise the current timestamp will be used as the
        filename in the format "YY-MM-DD  HH:MM SS".
        If the file already exists it will be appended to with the current
        timestamp separating each write. Otherwise the file will be created.
        '''
        #get the timestamp for the debug log's name
        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        filename  = timestamp.replace(':','.') + ".log"

        if isinstance(self.log_filename, str) and self.log_filename:
            filename = self.log_filename
            logstr = '\n' + '-'*80 + '\n'+ timestamp + '\n' + logstr
            
        if isfile(self.tagsdir + filename):
            mode = 'a'
        else:
            mode = 'w'
              
        #open a debug file and write the debug string to it
        with open(self.tagsdir + filename, mode) as logfile:
            logfile.write(logstr)
    

    def make_write_log(self, all_successes, rename=True, backup=None):
        '''
        Creates a log string of all tags that were saved and renames
        the tags from their temp filepaths to their original filepaths.
        Returns the created log string
        Raises TypeError if the Tag's status is not in (True,False,None)
        
        Renaming is done by removing '.temp' from the end of all files
        mentioned in 'all_successes' having a value of True.
        The log consists of a section showing which tags were properly
        loaded and processed, a section showing tags were either not
        properly loaded or not properly processed, and a section showing
        which tags were either not loaded or ignored during processing.

        Required arguments:
            all_successes(dict)
        Optional arguments:
            rename(bool)
            backup(bool)
            
        'all_successes' must be a dict with the same structure
        as self.tags, but with bools instead of tags.
        all_successes[tag_id][tagpath] = True/False/None

        True  = Tag was properly loaded and processed
        False = Tag was not properly loaded or not properly processed
        None  = Tag was not loaded or ignored during processing

        If 'backup' is True and a file already exists with the name
        that a temp file is going to be renamed to, the currently
        existing filename will be appended with '.backup'

        If 'rename' is True then the tags are expected to be in a
        temp file form where their filename ends with '.temp'
        Attempts to os.remove '.temp' from all tags if 'rename' == True

        The 'tagpath' key of each entry in all_successes[tag_id]
        are expected to be the original, non-temp filepaths. The
        temp filepaths are assumed to be (tagpath + '.temp').
        '''
        
        if backup is None:
            backup = self.backup
        
        error_str = success_str = ignored_str = "\n\nThese tags were "
        
        success_str += "properly loaded and processed:\n"
        error_str   += "improperly loaded or processed:\n"
        ignored_str += "not loaded or ignored during processing:\n"
        
        #loop through each tag
        for tag_id in sorted(all_successes):
            write_successes = all_successes[tag_id]
                    
            success_str += "\n" + tag_id
            error_str   += "\n" + tag_id
            ignored_str += "\n" + tag_id
            
            for tagpath in sorted(write_successes):
                status = write_successes[tagpath]
                
                #if we had no errors trying to convert the tag
                if status is True:
                    
                    success_str += "\n    " + tagpath

                    tagpath = self.tagsdir + tagpath

                    if rename:
                        if not backup or isfile(tagpath + ".backup"):
                            '''try to delete the tag if told to not backup tags
                            OR if there's already a backup with its name'''
                            try:
                                os.remove(tagpath)
                            except Exception:
                                success_str += ('\n        Could not '+
                                                   'delete original file.')
                        else:
                            '''Otherwise try to os.rename the old
                            files to the backup file names'''
                            try:
                                os.rename(tagpath, tagpath + ".backup")
                            except Exception:
                                success_str += ('\n        Could not '+
                                                   'backup original file.')
                                
                        #Try to os.rename the temp file
                        try:
                            os.rename(tagpath + ".temp", tagpath)
                        except Exception:
                            success_str += ("\n        Could not os.remove "+
                                               "'temp' from filename.")
                            #restore the backup
                            if backup:
                                try:   os.rename(tagpath + ".backup", tagpath)
                                except Exception: pass
                elif status is False:
                    error_str += "\n    " + tagpath
                elif status is None:
                    ignored_str += "\n    " + tagpath
                else:
                    raise TypeError('Invalid type for tag write status. '+
                                    'Expected either True, False, or None. Got'+
                                    " '%s' of type '%s'"%(status,type(status)))

        return success_str + error_str + ignored_str + '\n'
    

    def reload_defs(self, **kwargs):
        """ this function is used to dynamically load and index
        all tag definitions for all valid tags. This allows
        functionality to be extended simply by creating a new
        definition and dropping it into the defs folder."""

        imp_paths = {}
        
        self.defs.clear()
        
        if not self.defs_path:
            self.defs_path = self.default_defs_path

        valid_tag_ids = kwargs.get("valid_tag_ids")
        if not hasattr(valid_tag_ids, '__iter__'):
            valid_tag_ids = None
            
        #get the filepath or import path to the tag definitions module
        is_folderpath        = kwargs.get('is_folderpath')
        self.defs_path       = kwargs.get("defs_path", self.defs_path)
        self.import_rootpath = kwargs.get("import_rootpath",
                                          self.import_rootpath)

        '''  NEED TO IMPORT ALL MODULES IN THE PATH OF mod_rootpath
             BEFORE I CAN IMPORT THE THINGS INSIDE IT.'''
        
        if is_folderpath:
            self.defs_filepath   = self.defs_path.replace('/', pathdiv)\
                                   .replace('\\', pathdiv)
            self.import_rootpath = self.import_rootpath.replace('/', pathdiv)\
                                   .replace('\\', pathdiv)
            self.defs_path = ''

            mod_rootpath = dirname(dirname(self.import_rootpath))
            mod_base     = self.defs_filepath.split(mod_rootpath, 1)[-1]
            mod_base     = mod_base.replace('/','.').replace('\\','.')
            mod_base     = mod_base[int(mod_base.startswith('.')):]
            
            import_rootname = mod_base.split('.', 1)[0]
            root_module = SourceFileLoader(import_rootname,
                                           self.import_rootpath).load_module()
            if self.import_rootpath:
                if self.sys_path_index < 0:
                    sys.path.insert(self.sys_path_index, self.import_rootpath)
                    self.sys_path_index = len(sys.path)
                else:
                    sys.path[self.sys_path_index] = self.import_rootpath
        else:
            #cut off the trailing '.' if it exists
            if self.defs_path.endswith('.'):
                self.defs_path = self.defs_path[:-1]

            #import the root definitions module to get its absolute path
            defs_module = import_module(self.defs_path)
            
            '''try to get the absolute folder path of the defs module'''
            try:
                #Try to get the filepath of the module 
                self.defs_filepath = split(defs_module.__file__)[0]
            except Exception:
                #If the module doesnt have an __init__.py in the folder then an
                #exception will occur trying to get '__file__' in the above code
                #This method must be used(which I think looks kinda hacky)
                self.defs_filepath = tuple(defs_module.__path__)[0]
            self.defs_filepath = self.defs_filepath.replace('\\', pathdiv)\
                                 .replace('/', pathdiv)

        '''Log the location of every python file in the defs root'''
        #search for possibly valid definitions in the defs folder
        for root, directories, files in os.walk(self.defs_filepath):
            for module_path in files:
                base, ext = splitext(module_path)
                
                fpath = root.split(self.defs_filepath)[-1]
                
                #make sure the file name ends with .py and isn't already loaded
                if ext.lower() in (".py", ".pyw") and base not in imp_paths:
                    mod_name = (fpath + '.' + base).replace(pathdiv, '.')
                    imp_paths[mod_name] = join(root, base+ext)

        #load the defs that were found 
        for mod_name in imp_paths:
            #try to import the Definition module
            try:
                if is_folderpath:
                    f_path = imp_paths[mod_name]
                    '''remove the defs_filepath from the modules
                    filepath, replace all the path dividers with dots,
                    and remove the python file extension from the path'''
                    mod_name   = splitext(f_path.split(self.defs_filepath)[1].\
                                          replace(pathdiv, '.'))[0]
                    mod_name   = mod_base + mod_name
                    print(mod_name, f_path)
                    def_module = SourceFileLoader(mod_name,f_path).load_module()
                else:
                    def_module = import_module(self.defs_path + mod_name)
            except Exception:
                def_module = None
                if self.debug >= 1:
                    print(format_exc() + "\nThe above exception occurred " +
                          "while trying to import a tag definition.\n\n")
                    continue

            #make sure this is a valid tag module by making a few checks
            if hasattr(def_module, 'get'):
                '''finally, try to add the definition
                and its constructor to the lists'''
                try:
                    tagdef = def_module.get()
                    
                    try:
                        '''if a def doesnt have a usable tag_id then skip it'''
                        tag_id = tagdef.tag_id
                        if not bool(tag_id):
                            continue

                        if tag_id in self.defs:
                            raise KeyError(("The tag_id '%s' already exists in"+
                                            " the loaded defs dict.") % tag_id)

                        '''if it does though, add it to the definitions'''
                        if valid_tag_ids is None or tag_id in valid_tag_ids:
                            self.add_def(tagdef)
                    except Exception:
                        if self.debug >= 3:
                            print(format_exc())
                            
                except Exception:
                    if self.debug >= 2:
                        print(format_exc() + "\nThe above exception occurred "+
                              "while trying to load a tag definition.")


    def extend_tags(self, new_tags, replace=True):
        '''
        Adds all entries from new_tags to this Libraries tags.

        Required arguments:
            new_tags(iterable)
        Optional arguments:
            replace(bool)

        Replaces tags with the same name if 'replace' is True.
        Default is True
        
        If 'replace' is False, attempts to os.rename conflicting tag paths.
        self.rename_tries is the max number of attempts to os.rename a tag path.
        '''
        
        if not hasattr(self, "tags") or not isinstance(self.tags, dict):
            self.reset_tags()

        '''organize new_tags in the way the below algorithm requires'''
        new_tags = self.iter_to_collection(new_tags)

        #make these local for faster referencing
        get_unique_filename = self.get_unique_filename
        tags = self.tags
            
        for tag_id in new_tags:
            if tag_id not in tags:
                tags[tag_id] = new_tags[tag_id]
            else:
                for tagpath in list(new_tags[tag_id]):
                    src = new_tags[tag_id]
                    dest = tags[tag_id]
                    
                    #if this IS the same tag then just skip it
                    if dest[tagpath] is src[tagpath]:
                        continue
                    
                    if tagpath in dest:
                        if replace:
                            dest[tagpath] = src[tagpath]
                        else:
                            newpath = get_unique_filename(tagpath, dest, src)
                            
                            dest[newpath] = src[tagpath]
                            dest[newpath].tagpath = newpath
                            src[newpath] = src[tagpath]
                    else:
                        dest[tagpath] = src[tagpath]

        #recount how many tags are loaded/indexed
        self.tally_tags()
        

    def index_tags(self):
        '''
        Allocates empty dict entries in self.tags under
        the proper tag_id for each tag found in self.tagsdir.
        
        The created dict keys are the paths of the tag relative to
        self.tagsdir and the values are set to None.

        Returns the number of tags that were found in the folder.
        '''
        
        self.tags_indexed = 0

        #local references for faster access
        id_ext_get = self.id_ext_map.get
        get_tag_id = self.get_tag_id
        tags_get = self.tags.get
        tagsdir  = self.tagsdir
        check    = self.check_extension
        
        for root, directories, files in os.walk(tagsdir):
            for filename in files:
                filepath = join(root, filename)
                tag_id   = get_tag_id(filepath)
                tag_coll = tags_get(tag_id)
                self.current_tag = filepath
                
                '''check that the tag_id exists in self.tags and
                make sure we either aren't validating extensions, or that
                the files extension matches the one for that tag_id.'''
                if (tag_coll is not None and (not check or
                    splitext(filename.lower())[-1] == id_ext_get(tag_id))):
                    
                    '''if tag_id is valid, create a new mapping in tags
                    using its filepath (minus the tagsdir) as the key'''
                    tagpath, ext = splitext(filepath.split(tagsdir)[-1])

                    #make the extension lower case so it is always
                    #possible to find the file in self.tags
                    #regardless of the case of the file extension.
                    tagpath = tagpath + ext.lower()
                    
                    #Make sure the tag isn't already loaded
                    if tagpath not in tag_coll:
                        tag_coll[tagpath] = None
                        self.tags_indexed += 1
                    
        #recount how many tags are loaded/indexed
        self.tally_tags()
        
        return self.tags_indexed


    def load_tags(self, paths = None):
        '''
        Goes through each tag_id in self.tags and attempts to
        load each tag that is currently indexed, but that isnt loaded.
        Each entry in self.tags is a dict where each key is a
        tag's filepath relative to self.tagsdir and the value is
        the tag itself. If the tag isn't loaded the value is None.
        
        If an exception occurs while constructing a tag, the offending
        tag will be removed from self.tags[tag_id] and a
        formatted exception string along with the name of the offending
        tag will be printed to the console.
        
        Returns the number of tags that were successfully loaded.

        If 'paths' is a string, this function will try to load just
        the specified tag. If successful, the loaded tag will be returned.
        If 'paths' is an iterable, this function will try to load all
        the tags whose paths are in the iterable. Return value is normal.
        
        If self.allow_corrupt == True, tags will still be returned as
        successes even if they are corrupted. This is a debugging tool.
        '''
        
        #local references for faster access
        tagsdir   = self.tagsdir
        tags      = self.tags
        allow     = self.allow_corrupt
        new_tag   = None
        build_tag = self.build_tag

        '''decide if we are loading a single tag, a collection
        of tags, or all tags that have been indexed'''
        if paths is None:
            paths_coll = tags
        else:
            get_tag_id = self.get_tag_id
            paths_coll = {}
            
            if isinstance(paths, str):
                paths = (paths,)
            elif not hasattr(paths, '__iter__'):
                raise TypeError("'paths' must be either a filepath string "+
                                "or some form of iterable containing "+
                                "strings, not '%s'" % type(paths))

            #loop over each tagpath and create an entry for it in paths_coll
            for tagpath in paths:
                '''make sure each supplied tagpath
                is relative to self.tagsdir'''
                tagpath = relpath(tagpath, tagsdir)
                tag_id   = get_tag_id(join(tagsdir, tagpath))
                
                if tag_id is not None:
                    if isinstance(tags.get(tag_id), dict):
                        paths_coll[tag_id][tagpath] = None
                    else:
                        paths_coll[tag_id] = { tagpath:None }
                else:
                    raise LookupError("Couldn't locate tag_id for:\n    "+paths)
        

        #Loop over each tag_id in the tag paths to load in sorted order
        for tag_id in sorted(paths_coll):
            tag_coll = tags.get(tag_id)

            if not isinstance(tag_coll, dict):
                tag_coll = tags[tag_id] = {}
            
            #Loop through each tagpath in coll in sorted order
            for tagpath in sorted(paths_coll[tag_id]):
                
                #only load the tag if it isnt already loaded
                if tag_coll.get(tagpath) is None:
                    self.current_tag = tagpath
                        
                    '''incrementing tags_loaded and decrementing tags_indexed
                    in this loop is done for reporting the loading progress'''
                    
                    try:
                        new_tag = build_tag(filepath = tagsdir+tagpath,
                                            allow_corrupt = allow)
                        tag_coll[tagpath] = new_tag
                        self.tags_loaded += 1
                    except (OSError, MemoryError) as e:
                        print(format_exc())
                        print('Not enough accessable memory to continue '+
                              'loading tags. Ran out while opening\\reading:'+
                              ('\n    %s\n    Remaining unloaded tags will ' +
                               'be de-indexed and skipped\n') % tagpath)
                        del tag_coll[tagpath]
                        self.clear_unloaded_tags()
                        return
                    except Exception:
                        print(format_exc())
                        print('Above error encountered while opening\\reading:'+
                              '\n    %s\n    Tag may be corrupt\n' % tagpath )
                        del tag_coll[tagpath]
                    self.tags_indexed -= 1

        #recount how many tags are loaded/indexed
        self.tally_tags()
        
        return self.tags_loaded
    

    def reset_tags(self, tag_ids=None):
        '''
        Resets the dicts of the specified Tag_IDs in self.tags.
        Raises TypeError if 'tag_ids' is not an iterable or dict.

        Optional arguments:
            tag_ids(iterable, dict)
            
        If 'tag_ids' is None or unsupplied, resets the entire tags.
        '''
        
        if tag_ids is None:
            tag_ids = self.tags

        if isinstance(tag_ids, dict):
            tag_ids = tuple(tag_ids)
        elif isinstance(tag_ids, str):
            tag_ids = (tag_ids,)
        elif not hasattr(tag_ids, '__iter__'):
            raise TypeError("'tag_ids' must be some form of iterable.")
        
        for tag_id in tag_ids:
            #create a dict to hold all tags of one type.
            #tags are indexed by their filepath
            self.tags[tag_id] = {}

        #recount how many tags are loaded/indexed
        self.tally_tags()
        

    def tally_tags(self):
        '''
        Goes through each tag_id in self.tags and each of the
        collections in self.tags[tag_id] and counts how many
        tags are indexed and how many are loaded.

        Sets self.tags_loaded to how many loaded tags were found and
        sets self.tags_indexed to how many indexed tags were found.
        '''
        loaded = indexed = 0
        tags = self.tags
        
        #Recalculate how many tags are loaded and indexed
        for tag_id in tags:
            coll = tags[tag_id]
            for path in coll:
                if coll[path] is None:
                    indexed += 1
                else:
                    loaded += 1

        self.tags_loaded = loaded
        self.tags_indexed = indexed


    def write_tags(self, **kwargs):
        '''
        Goes through each tag_id in self.tags and attempts
        to save each tag that is currently loaded.
        
        Any exceptions that occur while writing the tags will be converted
        to formatted strings and concatenated together along with the name
        of the offending tags into a single 'exceptions' string.

        Returns a 'statuses' dict and the 'exceptions' string.
        statuses is used with self.make_tag_write_log() to
        os.rename all temp tag files to their non-temp names, backup the
        original tags, and make a log string to write to a log file.
        The structure of the statuses dict is as follows:
        statuses[tag_id][tagpath] = True/False/None. 

        True  = Tag was properly saved
        False = Tag could not be saved
        None  = Tag was not saved
        
        Optional arguments:
            print_errors(bool)
            int_test(bool)
            backup(bool)
            temp(bool)
            
        If 'print_errors' is True, exceptions will be printed as they occur.
        If 'int_test' is True, each tag will be quick loaded after it is written
        to test its data integrity. Quick loading means skipping raw data.
        If 'temp' is True, each tag written will be suffixed with '.temp'
        If 'backup' is True, any tags that would be overwritten are instead
        renamed with the extension '.backup'. If a backup already exists
        then the oldest one is kept and the current file is deleted.

        Passes 'backup', 'temp', and 'int_test' on to each tag's write() method.
        '''
        print_errors = kwargs.get('print_errors', True)
        int_test     = kwargs.get('int_test', self.int_test)
        backup       = kwargs.get('backup',   self.backup)
        temp         = kwargs.get('temp',     self.write_as_temp)
        
        statuses = {}
        exceptions = '\n\nExceptions that occurred while writing tags:\n\n'
        
        tagsdir = self.tagsdir
        
        #Loop through each tag_id in self.tags in order
        for tag_id in sorted(self.tags):
            coll = self.tags[tag_id]
            statuses[tag_id] = these_statuses = {}
            
            #Loop through each tagpath in coll in order
            for tagpath in sorted(coll):
            
                #only write the tag if it is loaded
                if coll[tagpath] is not None:
                    self.current_tag = tagpath
                    
                    try:
                        coll[tagpath].write(filepath=tagsdir+tagpath, temp=temp,
                                            int_test=int_test, backup=backup)
                        these_statuses[tagpath] = True
                    except Exception:
                        tmp = (format_exc() + '\n\n' + 
                               'Above error occurred while writing the tag:\n'+
                               '    ' + str(tagpath) + '\n' +
                               '    Tag may be corrupt.\n')
                        exceptions += '\n' + tmp + '\n'
                        if print_errors:
                            print(tmp)
                        these_statuses[tagpath] = False
                    
        return(statuses, exceptions)
