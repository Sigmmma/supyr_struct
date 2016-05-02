import sys
import shutil

from array import array
from copy import copy, deepcopy
from os import makedirs, remove, rename
from os.path import dirname, exists, isfile
from sys import getsizeof
from traceback import format_exc
from time import time

from supyr_struct.defs.constants import *

class Tag():
    '''docstring'''
    
    def __init__(self, **kwargs):
        '''docstring'''
            
        #the tag handler which this tag belongs to and is also
        #the object that built this Tag and can build others
        self.handler = kwargs.get("handler", None)
        
        #the whole definition, including the ext, def_id, and Structure
        self.definition = kwargs.get("definition", None)

        #if this tags data starts inside a larger structure,
        #this is the offset its data should be written to
        self.root_offset = kwargs.get("root_offset", 0)
        
        #if this tag is incomplete, this is the path to the source
        #file that was read from to build it. Used for preserving
        #the unknown data while allowing known parts to be edited
        self.sourcepath = ''

        '''YOU SHOULDNT ENABLE THIS IF YOUR DEFINITION IS INCOMPLETE'''
        #calc_pointers determines whether or not to scan the tag for
        #pointers when writing it and set their values to where the
        #blocks they point to will be written. If False, any pointer
        #based blocks will be written to where their pointers
        #currently point to, whether or not they are valid.
        if "calc_pointers" in kwargs:
            self.calc_pointers = kwargs["calc_pointers"]
        else:
            try:
                self.calc_pointers = True
                #If the definition isnt complete, changing any pointers
                #will almost certainly screw up the layout of the data.
                #By default, pointers wont be recalculated on incomplete defs
                if self.definition.incomplete:
                    self.calc_pointers = False
            except AttributeError:
                pass
        
        #this is the string of the absolute path to the tag
        self.filepath = kwargs.get("filepath",'')

        #the actual data this tag holds represented as nested blocks
        if "data" in kwargs:
            self.data = kwargs["data"]
            return
        
        self.data = None
        #whether or not to allow corrupt tags to be built.
        #this is a debugging tool.
        if not kwargs.get('allow_corrupt'):
            self.read(rawdata = kwargs.get("rawdata", None),
                      int_test = kwargs.get("int_test", False))
            return
        
        try:
            self.read(rawdata = kwargs.get("rawdata", None),
                      int_test = kwargs.get("int_test", False))
        except Exception:
            print(format_exc())


    def __copy__(self):
        '''Creates a shallow copy of the object.'''
        #create the new Tag
        dup_tag = type(self)(data=None)
        
        #copy all the attributes from this tag to the duplicate
        if hasattr(self, '__dict__'):
            dup_tag.__dict__.update(self.__dict__)

        #if the tag uses slots, copy those over too
        if hasattr(self, '__slots__'):
            for slot in self.__slots__:
                dup_tag.__setattr__(slot, self.__getattr__(slot))

        return dup_tag


    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the definition the same'''
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]
        
        #create the new Tag
        memo[id(self)] = dup_tag = type(self)(data=None)
        
        #copy all the attributes from this tag to the duplicate
        if hasattr(self, '__dict__'):
            dup_tag.__dict__.update(self.__dict__)

        #if the tag uses slots, copy those over too
        if hasattr(self, '__slots__'):
            for slot in self.__slots__:
                dup_tag.__setattr__(slot, self.__getattr__(slot))

        #create a deep copy of the data and set it
        dup_tag.data = deepcopy(self.data, memo)

        return dup_tag


    def __str__(self, **kwargs):
        '''Creates a formatted string representation of the hierarchy and
        data within a tag. Keyword arguments can be supplied to specify
        what information to display and how much to indent per line.
        Passes keywords to self.data.__str__() to maintain formatting.

        Optional kwargs:
            indent(int)
            level(int)
            printout(bool)

        indent   - determines how many spaces to indent each hierarchy line
        level    - determines how many levels the hierarchy is already indented
        printout - Prints line by line if True. As a single string if False
        '''
        kwargs.setdefault('level',    0)
        kwargs.setdefault('indent',   BLOCK_PRINT_INDENT)
        kwargs.setdefault('printout', False)
            
        '''Prints the contents of a tag object'''            
        if self.data is None:
            raise LookupError("'data' doesn't exist. Tag may "+
                              "have been constructed incorrectly.\n" +
                              ' '*BPI + self.filepath)
            
        return self.data.__str__(**kwargs)


      
    def __sizeof__(self, seenset=None, include_data=True):
        '''docstring'''
        if seenset == None:
            seenset = set()
        elif id(self) in seenset:
            return 0
            
        dict_attrs = slot_attrs = ()
        if hasattr(self, '__dict__'):
            dict_attrs = copy(self.__dict__)                
        if hasattr(self, '__slots__'):
            slot_attrs = set(self.__slots__)
        bytes_total = getsizeof(self.__dict__)
        
        if id(self) not in seenset:
            seenset.add(id(self))
            seenset.add(id(self.definition))
            if ORIG_DESC in self.definition.descriptor:
                bytes_total += getsizeof(self.definition.descriptor)
                
        #if we aren't calculating the size of the data, remove it
        if not include_data:
            if 'data' in dict_attrs:
                del dict_attrs['data']
            if 'data' in slot_attrs:
                slot_attrs.remove('data')
            
        for attr_name in dict_attrs:
            if id(dict_attrs[attr_name]) not in seenset:
                seenset.add(id(dict_attrs[attr_name]))
                bytes_total += getsizeof(dict_attrs[attr_name])
            
        for attr_name in slot_attrs:
            try:
                attr = object.__getattribute__(self, attr_name)
            except AttributeError:
                continue
            if id(attr) not in seenset:
                seenset.add(id(attr))
                bytes_total += getsizeof(attr)

        return bytes_total


    def set_pointers(self, offset=0):
        '''Scans through a tag and sets the pointer of each
        pointer based block in a way that ensures that, when
        written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other block.'''
        
        #Keep a set of all seen block IDs to prevent infinite recursion.
        seen = set()
        pb_blocks = []

        '''Loop over all the blocks in data and log all blocks that use
        pointers to a list. Any pointer based blocks will NOT be entered.
        
        The size of all non-pointer blocks will be calculated and used
        as the starting offset pointer based blocks.'''
        offset = self.data.collect_pointers(offset, seen, pb_blocks)

        #Repeat this until there are no longer any pointer
        #based blocks for which to calculate pointers.
        while pb_blocks:
            new_pb_blocks = []
            
            '''Iterate over the list of pointer based blocks and set their
            pointers while incrementing the offset by the size of each block.
            
            While doing this, build a new list of all the pointer based
            blocks in all of the blocks currently being iterated over.'''
            for block in pb_blocks:
                block, attr_index, substruct = block[0], block[1], block[2]
                block.set_meta('POINTER', offset, attr_index)
                offset = block.collect_pointers(offset, seen, new_pb_blocks,
                                                substruct, True, attr_index)
                #this has been commented out since there will be a routine
                #later that will collect all pointers and if one doesn't
                #have a matching block in the structure somewhere then the
                #pointer will be set to 0 since it doesnt exist.
                '''
                #In binary structs, usually when a block doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if block.get_size(attr_index) > 0:
                    block.set_meta('POINTER', offset, attr_index)
                    offset = block.collect_pointers(offset, seen, new_pb_blocks,
                                                    False, True, attr_index)
                else:
                    block.set_meta('POINTER', 0, attr_index)'''
                    
            #restart the loop using the next level of pointer based blocks
            pb_blocks = new_pb_blocks


    @property
    def def_id(self):
        try:
            return self.definition.def_id
        except AttributeError:
            return None

    @property
    def ext(self):
        try:
            return self.definition.ext
        except AttributeError:
            return None
        

    def pprint(self, **kwargs):
        '''Used for pretty printing. Can print a
        partially corrupted tag for debugging purposes.
        
        If 'printout' is a keyword, the function will
        print each line as it is constructed instead
        of returning the whole string at once(which
        it will still do)
        
        Keywords are:
        'indent', 'print_raw', 'printout', 'precision',
        'show':['name',  'value', 'children',
                'field', 'size',  'offset', 
                'index', 'py_id', 'py_type',
                'flags', 'trueonly',
                'filepath', 'binsize', 'ramsize']
        '''
        if not 'show' in kwargs or (not hasattr(kwargs['show'], '__iter__')):
            kwargs['show'] = blocks.def_show
        if isinstance(kwargs["show"], str):
            kwargs['show'] = [kwargs['show']]

        show = kwargs['show'] = set(kwargs['show'])
        if 'all' in show:
            show.remove('all')
            show.update(blocks.all_show)

        ramsize = "ramsize" in show
        binsize = "binsize" in show
        tagstring = ''
        
        printout  = kwargs.get('printout',  False)
        precision = kwargs.get('precision', None)

        kwargs['printout'] = printout
        
        if ramsize: show.remove('ramsize')
        if binsize: show.remove('binsize')
        
        if 'filepath' in show:
            handler   = self.handler
            tagstring = self.filepath
            if handler is not None and hasattr(handler, 'tagsdir'):
                tagstring = tagstring.split(handler.tagsdir)[-1]
                
            if printout:
                print(tagstring)
                tagstring = ''
            else:
                tagstring += '\n'
                
        tagstring += self.__str__(**kwargs)
        if printout:
            print(tagstring)
            tagstring = ''
        else:
            tagstring += '\n'

        if ramsize:
            objsize  = self.__sizeof__()
            datasize = objsize - self.__sizeof__(include_data=False)
            tagstring += '"In-memory tag" is '+str(objsize) +" bytes\n"
            tagstring += '"In-memory data" is '  +str(datasize)+" bytes\n"
            
        if binsize:
            binsize = self.data.binsize
            tagstring += '"Packed structure" is '+str(binsize)+" bytes\n"

            if ramsize and binsize:
                #this is how many times larger these are than the packed binary
                objx = datax = "∞"
                
                if binsize:
                    fmt = "{:."+str(precision)+"f}"
                    
                    objx  = objsize/binsize
                    datax = datasize/binsize
                    if precision:
                        objx  = fmt.format(round(objx,  precision))
                        datax = fmt.format(round(datax, precision))
                    
                tagstring += ('"In-memory tag" is ' +
                              str(objx)+" times as large.\n" + 
                              '"In-memory data" is ' +
                              str(datax) + " times as large.\n")
            
        if printout:
            print(tagstring)
        else:
            return tagstring


    def read(self, **kwargs):
        ''''''
        if kwargs.get('filepath') is None and kwargs.get('rawdata') is None:
            kwargs['filepath'] = self.filepath
        rawdata = blocks.Block.get_raw_data(self, **kwargs)
        self.filepath = kwargs['filepath']
        
        desc  = self.definition.descriptor
        field = desc[TYPE]
        init_attrs = bool(kwargs.get('init_attrs', rawdata is None))
        block_type = desc.get(DEFAULT, field.py_type)

        #create the data block and parent it to this
        #Tag before initializing its attributes
        new_tag_data = block_type(desc, parent=self, init_attrs=False)
        self.data = new_tag_data
        
        if init_attrs:
            new_tag_data.__init__(desc, parent=self, init_attrs=True)
        
        root_offset = kwargs.get('root_offset', self.root_offset)
        offset = kwargs.get('offset', 0)

        #if this is an incomplete object then we
        #need to keep a path to the source file
        if self.definition.incomplete and rawdata:
            self.sourcepath = self.filepath

        #call the reader
        field.reader(desc, new_tag_data, rawdata, None, root_offset,
                     offset, int_test=kwargs.get("int_test", False))


    def rename_backup_and_temp(self, filepath, backuppath, temppath, backup):
        if backup:
            """if there's already a backup of this tag
            we try to delete it. if we can't then we try
            to rename the old tag with the backup name"""
            if isfile(backuppath):
                remove(filepath)
            else:
                try:
                    rename(filepath, backuppath)
                except Exception:
                    print(("ERROR: While attempting to save tag, " +
                           "could not rename:\n" + ' '*BPI + "%s\nto "+
                           "the backup file:\n" +' '*BPI + "%s")%
                          (filepath, backuppath))

            """Try to rename the temp files to the new
            file names. If we can't rename the temp to
            the original, we restore the backup"""
            try:
                rename(temppath, filepath)
            except Exception:
                try: rename(backuppath, filepath)
                except Exception: pass
                raise IOError(("ERROR: While attempting to save" +
                               "tag, could not rename temp file:\n" +
                               ' '*BPI + "%s\nto\n" + ' '*BPI + "%s")%
                              (temppath, filepath))
        else:
            #Try to delete the old file
            try: remove(filepath)
            except Exception: pass

            #Try to rename the temp tag to the real tag name
            try: rename(temppath, filepath)
            except Exception: pass


    def write(self, **kwargs):            
        """ this function will attempt to save the tag to it's current
        file path, but while appending ".temp" to the end. if it
        successfully saved then it will attempt to either backup or
        delete the old tag and remove .temp from the resaved one.
        """
        
        data = self.data
        desc = data.DESC        
        
        if kwargs.get('buffer') is not None:
            return data.write(**kwargs)
            
        backup = bool(kwargs.get('backup',True))
        temp   = bool(kwargs.get('temp',True))
        offset   = kwargs.get('offset',0)
        filepath = kwargs.get('filepath',self.filepath)
        root_offset   = kwargs.get('root_offset',self.root_offset)
        calc_pointers = bool(kwargs.get('calc_pointers',self.calc_pointers))

        #if the tag handler doesnt exist then dont test after writing
        try:
            int_test = bool(kwargs.get('int_test', self.handler.build_tag))
        except AttributeError:
            int_test = False

        if filepath == '':
            raise IOError("filepath is invalid. Cannot write "+
                          "tag to '%s'" % self.filepath)
        
        folderpath = dirname(filepath)

        #if the filepath ends with the folder path terminator, raise an error
        if filepath.endswith(pathdiv):
            raise IOError('filepath must be a path to a file, not a folder.')

        #if the path doesnt exist, create it
        if not exists(folderpath):
            makedirs(folderpath)
        
        temppath   = filepath + ".temp"
        backuppath = filepath + ".backup"

        #open the file to be written and start writing!
        with open(temppath, 'w+b') as tagfile:
            '''if this is an incomplete object we need to copy the
            original file to the path of the new file in order to
            fill in the data we don't yet understand/have mapped out'''
                    
            #if we need to calculate any pointers, do so
            if calc_pointers:
                self.set_pointers(offset)
            
            if self.definition.incomplete:
                if not(isfile(self.sourcepath)):
                    raise IOError("Tag is incomplete and the source "+
                                  "file to fill in the remaining "+
                                  "data cannot be found.")
                
                if self.sourcepath != temppath:
                    shutil.copyfileobj(open(self.sourcepath, 'r+b'),
                                       tagfile, 2*(1024**2) )#2MB buffer
            else:
                #make a file as large as the tag is calculated to fill
                tagfile.seek(data.binsize-1)
                tagfile.write(b'\x00')

            data.TYPE.writer(data, tagfile, None, root_offset, offset)
            
        #if the handler is accessible, we can quick load
        #the tag that was just written to check its integrity
        if int_test:
            good = self.handler.build_tag(int_test=True, def_id=self.def_id,
                                          filepath=temppath)
        else:
            good = True
        
        if good:
            """If we are doing a full save then we
            need to try and rename the temp file"""
            if not temp:
                self.rename_backup_and_temp(filepath, backuppath,
                                            temppath, backup)
        else:
            raise IOError("The following tag temp file did not pass the data "+
                          "integrity test:\n" + ' '*BPI + str(self.filepath))

        return filepath
