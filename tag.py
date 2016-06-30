'''
'''
import shutil

from copy import copy, deepcopy
from os import makedirs, remove, rename
from os.path import dirname, exists, isfile
from sys import getsizeof
from traceback import format_exc

from supyr_struct.defs.constants import *

# linked to through supyr_struct.__init__
blocks = None


class Tag():
    '''docstring'''

    def __init__(self, **kwargs):
        '''docstring'''

        # the whole definition, including the ext, def_id, and Structure
        self.definition = kwargs.get("definition", None)

        # if this tags data starts inside a larger structure,
        # this is the offset its data should be written to
        self.root_offset = kwargs.get("root_offset", 0)

        # YOU SHOULDNT ENABLE calc_pointers IF YOUR DEFINITION IS INCOMPLETE
        # calc_pointers determines whether or not to scan the tag for
        # pointers when writing it and set their values to where the
        # blocks they point to will be written. If False, any pointer
        # based blocks will be written to where their pointers
        # currently point to, whether or not they are valid.
        if "calc_pointers" in kwargs:
            self.calc_pointers = kwargs["calc_pointers"]
        else:
            try:
                self.calc_pointers = True
                # If the definition isnt complete, changing any pointers
                # will almost certainly screw up the layout of the data.
                # By default, pointers wont be recalculated on incomplete defs
                if self.definition.incomplete:
                    self.calc_pointers = False
            except AttributeError:
                pass

        # if this tag is incomplete, this is the path to the source
        # file that was read from to build it. Used for preserving
        # the unknown data while allowing known parts to be edited
        self.sourcepath = ''

        # this is the string of the absolute path to the tag
        self.filepath = kwargs.get("filepath", '')

        # whether or not to fill the output buffer with
        # b'\x00'*self.data.binsize before starting to write
        self.zero_fill = kwargs.get("zero_fill", True)

        # the actual data this tag holds represented as nested blocks
        if "data" in kwargs:
            self.data = kwargs["data"]
            return

        self.data = None
        # whether or not to allow corrupt tags to be built.
        # this is a debugging tool.
        if not kwargs.get('allow_corrupt'):
            self.build(rawdata=kwargs.get("rawdata", None),
                       int_test=kwargs.get("int_test", False))
            return

        try:
            self.build(rawdata=kwargs.get("rawdata", None),
                       int_test=kwargs.get("int_test", False))
        except Exception:
            print(format_exc())

    def __copy__(self):
        '''Creates a shallow copy of the object.'''
        # create the new Tag
        dup_tag = type(self)(data=None)

        # copy all the attributes from this tag to the duplicate
        if hasattr(self, '__dict__'):
            dup_tag.__dict__.update(self.__dict__)

        # if the tag uses slots, copy those over too
        if hasattr(self, '__slots__'):
            for slot in self.__slots__:
                dup_tag.__setattr__(slot, self.__getattr__(slot))

        return dup_tag

    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the definition the same'''
        # if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        # create the new Tag
        memo[id(self)] = dup_tag = type(self)(data=None)

        # copy all the attributes from this tag to the duplicate
        if hasattr(self, '__dict__'):
            dup_tag.__dict__.update(self.__dict__)

        # if the tag uses slots, copy those over too
        if hasattr(self, '__slots__'):
            for slot in self.__slots__:
                dup_tag.__setattr__(slot, self.__getattr__(slot))

        # create a deep copy of the data and set it
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

        indent   - how many spaces to indent each hierarchy line
        level    - how many levels the hierarchy is already indented
        printout - Prints line by line if True. As a single string if False
        '''
        kwargs.setdefault('level',    0)
        kwargs.setdefault('indent',   BLOCK_PRINT_INDENT)
        kwargs.setdefault('printout', False)

        # Prints the contents of a tag object
        if self.data is None:
            raise LookupError("'data' doesn't exist. Tag may " +
                              "have been constructed incorrectly.\n" +
                              ' '*BPI + self.filepath)

        return self.data.__str__(**kwargs)

    def __sizeof__(self, seenset=None, include_data=True):
        '''docstring'''
        if seenset is None:
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

        # if we aren't calculating the size of the data, remove it
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

        # Keep a set of all seen block IDs to prevent infinite recursion.
        seen = set()
        pb_blocks = []

        # Loop over all the blocks in data and log all blocks that use
        # pointers to a list. Any pointer based blocks will NOT be entered.
        # The size of all non-pointer blocks will be calculated and used
        # as the starting offset pointer based blocks.
        offset = self.data.collect_pointers(offset, seen, pb_blocks)

        # Repeat this until there are no longer any pointer
        # based blocks for which to calculate pointers.
        while pb_blocks:
            new_pb_blocks = []

            # Iterate over the list of pointer based blocks and set their
            # pointers while incrementing the offset by the size of each block.

            # While doing this, build a new list of all the pointer based
            # blocks in all of the blocks currently being iterated over.
            for block in pb_blocks:
                block, attr_index, substruct = block[0], block[1], block[2]
                block.set_meta('POINTER', offset, attr_index)
                offset = block.collect_pointers(offset, seen, new_pb_blocks,
                                                substruct, True, attr_index)
                # This has been commented out since there will be a routine
                # later that will collect all pointers and if one doesn't
                # have a matching block in the structure somewhere then the
                # pointer will be set to 0 since it doesnt exist.
                '''
                #In binary structs, usually when a block doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if block.get_size(attr_index) > 0:
                    block.set_meta('POINTER', offset, attr_index)
                    offset = block.collect_pointers(offset, seen,
                                                    new_pb_blocks, False,
                                                    True, attr_index)
                else:
                    block.set_meta('POINTER', 0, attr_index)'''

            # restart the loop using the next level of pointer based blocks
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
        '''
        A function for constructing a string detailing everything in the Tag.
        Can print a partially corrupted Tag for debugging purposes.

        Returns a formatted string representation of the Tag.

        Keywords arguments:
        # bool:
        printout ---- Whether or to print the constructed string line by line.

        # int:
        indent ------ The number of spaces of indent added per indent level
        precision --- The number of decimals to round floats to

        # set:
        show -------- An iterable containing strings specifying what to
                      include in the string. Valid strings are as follows:
            index ---- The index the attribute is located in in its parent
            name ----- The name of the attribute
            value ---- The attribute value
            field ---- The Field of the attribute
            size ----- The size of the attribute
            offset --- The offset(or pointer) of the attribute
            py_id ---- The id() of the attribute
            py_type -- The type() of the attribute
            endian --- The endianness of the Field
            flags ---- The individual flags(offset, name, value) in a bool
            trueonly - Limit flags shown to only the True flags
            children - Attributes parented to a block as children
            filepath - The Tags filepath
            binsize -- The size of the Tag if it were serialized to a file
            ramsize -- The number of bytes of ram the python objects that
                       compose the Tag, its Blocks, and other properties
                       stored in its __slots__ and __dict__ take up.
        '''
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        if 'all' in show:
            show.update(ALL_SHOW)
        precision = kwargs.get('precision', None)

        tag_str = ''

        if 'filepath' in show:
            tag_str = self.filepath
            tag_str += '\n'

        tag_str += self.__str__(**kwargs) + '\n'

        if "ramsize" in show:
            objsize = self.__sizeof__()
            datasize = objsize - self.__sizeof__(include_data=False)
            tag_str += ('"In-memory tag"  is %s bytes\n' % objsize +
                        '"In-memory data" is %s bytes\n' % datasize)

        if "binsize" in show:
            try:
                binsize = self.data.binsize
                tag_str += '"Packed structure" is %s bytes\n' % binsize

                if "ramsize" in show:
                    # the number of times larger this is than the packed binary
                    objx = datax = "∞"

                    if binsize:
                        objx = objsize / binsize
                        datax = datasize / binsize
                        if isinstance(precision, int):
                            fmt = "{:.%sf}" % precision
                            objx = fmt.format(round(objx, precision))
                            datax = fmt.format(round(datax, precision))

                    tag_str += (('"In-memory tag"  is %s times as large.\n' +
                                 '"In-memory data" is %s times as large.\n') %
                                (objx, datax))
            except Exception:
                tag_str += SIZE_CALC_FAIL + '\n'

        if kwargs.get('printout'):
            # print the string line by line
            for line in tag_str.split('\n'):
                try:
                    print(line)
                except:
                    print(' '*(len(line) - len(line.lstrip(' '))) +
                          UNPRINTABLE)
        return tag_str

    def build(self, **kwargs):
        ''''''
        if kwargs.get('filepath') is None and kwargs.get('rawdata') is None:
            kwargs['filepath'] = self.filepath
        rawdata = blocks.Block.get_rawdata(self, **kwargs)
        self.filepath = kwargs.get('filepath', self.filepath)

        desc = self.definition.descriptor
        field = desc[TYPE]
        init_attrs = bool(kwargs.get('init_attrs', rawdata is None))
        block_type = desc.get(DEFAULT, field.py_type)

        # Create the data block and parent it to this
        # Tag before initializing its attributes
        new_tag_data = block_type(desc, parent=self, init_attrs=False)
        self.data = new_tag_data

        if init_attrs:
            new_tag_data.__init__(desc, parent=self, init_attrs=True)

        root_offset = kwargs.get('root_offset', self.root_offset)
        offset = kwargs.get('offset', 0)

        # If this is an incomplete object then we
        # need to keep a path to the source file
        if self.definition.incomplete and rawdata:
            self.sourcepath = self.filepath

        # call the reader
        field.reader(desc, new_tag_data, rawdata, None, root_offset,
                     offset, int_test=kwargs.get("int_test", False))

    def rename_backup_and_temp(self, filepath, backuppath, temppath, backup):
        ''''''
        if backup:
            # if there's already a backup of this tag
            # we try to delete it. if we can't then we try
            # to rename the old tag with the backup name
            if isfile(backuppath):
                remove(filepath)
            else:
                try:
                    rename(filepath, backuppath)
                except Exception:
                    pass
                    # print(("ERROR: While attempting to save tag, " +
                    #        "could not rename:\n" + ' '*BPI + "%s\nto "+
                    #        "the backup file:\n" +' '*BPI + "%s")%
                    #       (filepath, backuppath))

            # Try to rename the temp files to the new file names.
            # Restore the backup if we can't rename the temp to the original
            try:
                rename(temppath, filepath)
            except Exception:
                try:
                    rename(backuppath, filepath)
                except Exception:
                    pass
                raise IOError(("ERROR: While attempting to save" +
                               "tag, could not rename temp file:\n" +
                               ' ' * BPI + "%s\nto\n" + ' '*BPI + "%s") %
                              (temppath, filepath))
        else:
            # Try to delete the old file
            try:
                remove(filepath)
            except Exception:
                pass

            # Try to rename the temp tag to the real tag name
            try:
                rename(temppath, filepath)
            except Exception:
                pass

    def serialize(self, **kwargs):
        """Attempts to serialize the tag to it's current
        filepath, but while appending ".temp" to the end. if it
        successfully saved then it will attempt to either backup or
        delete the old tag and remove .temp from the resaved one.
        """

        data = self.data

        if kwargs.get('buffer') is not None:
            return data.serialize(**kwargs)

        temp = bool(kwargs.get('temp', True))
        backup = bool(kwargs.get('backup', True))
        offset = kwargs.get('offset', 0)
        filepath = kwargs.get('filepath', self.filepath)
        root_offset = kwargs.get('root_offset', self.root_offset)
        calc_pointers = bool(kwargs.get('calc_pointers', self.calc_pointers))

        # If the definition doesnt exist then dont test after writing
        try:
            int_test = bool(kwargs.get('int_test', self.definition.build))
        except AttributeError:
            int_test = False

        if filepath == '':
            raise IOError("filepath is invalid. Cannot serialize " +
                          "tag to '%s'" % self.filepath)

        folderpath = dirname(filepath)

        # If the filepath ends with the folder path terminator, raise an error
        if filepath.endswith(PATHDIV):
            raise IOError('filepath must be a path to a file, not a folder.')

        # If the path doesnt exist, create it
        if not exists(folderpath):
            makedirs(folderpath)

        temppath = filepath + ".temp"
        backuppath = filepath + ".backup"

        # open the file to be written and start writing!
        with open(temppath, 'w+b') as tagfile:
            # if this is an incomplete object we need to copy the
            # original file to the path of the new file in order to
            # fill in the data we don't yet understand/have mapped out'''

            # if we need to calculate any pointers, do so
            if calc_pointers:
                self.set_pointers(offset)

            if self.definition.incomplete:
                if not(isfile(self.sourcepath)):
                    raise IOError("Tag is incomplete and the source " +
                                  "file to fill in the remaining " +
                                  "data cannot be found.")

                if self.sourcepath != temppath:
                    shutil.copyfileobj(open(self.sourcepath, 'r+b'),
                                       tagfile, 2*(1024**2))  # 2MB buffer
            elif self.zero_fill:
                # make a file as large as the tag is calculated to fill
                tagfile.seek(data.binsize - 1)
                tagfile.write(b'\x00')

            data.TYPE.writer(data, tagfile, None, root_offset, offset)

        # if the definition is accessible, we can quick load
        # the tag that was just written to check its integrity
        if int_test:
            good = self.definition.build(int_test=True, def_id=self.def_id,
                                         filepath=temppath)
        else:
            good = True

        if good:
            # If we are doing a full save then we
            # need to try and rename the temp file
            if not temp:
                self.rename_backup_and_temp(filepath, backuppath,
                                            temppath, backup)
        else:
            raise IntegrityError("The following tag temp file did not " +
                                 "pass the data integrity test:\n" + ' '*BPI +
                                 str(self.filepath))

        return filepath
