'''
Tags are a kind of header object that hold a reference to the root
of the structure, the TagDef used to build the Tag, a filepath to
parse from/serialize to, and other properties. Tags and TagDefs are
not required to parse/serialize files, but are a simple way to give
a parsed structure some file properties. 
'''
import shutil

from copy import copy, deepcopy
from os import makedirs
from os.path import dirname, exists, isfile
from sys import getsizeof
from traceback import format_exc

from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.buffer import get_rawdata

# linked to through supyr_struct.__init__
blocks = None


class Tag():
    '''
    Instance properties:
        bool:
            calc_pointers
            zero_fill
        Block:
            data
        int:
            root_offset
        str:
            def_id
            ext
            filepath
            sourcepath
        TagDef:
            definition
    '''

    def __init__(self, **kwargs):
        '''
        If 'data' is not supplied, self.parse will be called.......
        MAKE IT SO ALL EXTRA KWARGS ARE PASSED TO self.parse

        Optional keyword arguments:
        # bool:
            calc_pointers -
            int_test ------
            zero_fill -----

        # Buffer:
            rawdata -------

        # Block:
            data ----------

        # str:
            filepath ------
        '''
        # the TagDef that describes this object
        self.definition = kwargs.pop("definition", None)

        try:
            self.ext = self.definition.ext
        except AttributeError:
            self.ext = None

        # if this tags data starts inside a larger structure,
        # this is the offset its data should be written to
        self.root_offset = kwargs.pop("root_offset", 0)

        # YOU SHOULDNT ENABLE calc_pointers IF YOUR DEFINITION IS INCOMPLETE.
        # calc_pointers determines whether or not to scan the tag for
        # pointers when writing it and set their values to where the
        # nodes they point to will be written. If False, any pointer
        # based nodes will be written to where their pointers
        # currently point to, whether or not they are valid.
        # By default, pointers will NOT be recalculated on incomplete defs
        try:
            if self.definition.incomplete and "calc_pointers" not in kwargs:
                kwargs["calc_pointers"] = False
        except AttributeError:
            pass
        self.calc_pointers = kwargs.pop("calc_pointers", True)

        # if this tag is incomplete, this is the path to the source
        # file that was read from to build it. Used for preserving
        # the unknown data while allowing known parts to be edited
        self.sourcepath = ''

        # this is the string of the absolute path to the tag
        self.filepath = kwargs.get("filepath", '')
        if 'rawdata' in kwargs:
            kwargs.pop("filepath", '')

        # whether or not to fill the output buffer with
        # b'\x00'*self.data.binsize before starting to serialize
        self.zero_fill = kwargs.pop("zero_fill", True)

        # check only for the existence of 'data' rather than its value.
        # the deepcopy method requires the copied class be instantiated
        # with 'data' as None so it can efficiently copy the data itself.
        if 'data' in kwargs:
            self.data = kwargs['data']
        else:
            self.parse(**kwargs)

    def __copy__(self):
        '''
        '''
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
        '''
        '''
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
        '''
        Creates a formatted string representation of the nodes
        within a Tag. Keyword arguments can be supplied to specify
        what information to display and how much to indent per line.

        Passes keywords to self.data.__str__() to maintain formatting.

        Optional keywords arguments:
        # int:
        indent ----- The number of spaces of indent added per indent level.
        precision -- The number of decimals to round floats to.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located at in its parent
            name ------ The name of the field
            value ----- The attribute value
            type ------ The FieldType of the field
            size ------ The size of the field
            offset ---- The offset(or pointer) of the field
            parent_id - The id() of each nodes parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
            endian ---- The endianness of the field
            flags ----- The individual flags(offset, name, value) in a bool
            trueonly -- Limit flags shown to only the True flags
            steptrees - Fields parented to the node as steptrees
        '''
        kwargs.setdefault('level',    0)
        kwargs.setdefault('indent',   NODE_PRINT_INDENT)
        kwargs.setdefault('printout', False)

        # Prints the contents of a tag object
        if self.data is not None:
            return self.data.__str__(**kwargs)

        raise LookupError(
            "This tags 'data' attribute doesn't exist. " +
            "Tag may have been incorrectly constructed.\n" +
            ' '*BPI + self.filepath)

    def __sizeof__(self, seenset=None, include_data=True):
        '''
        '''
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
        pointer based node in a way that ensures that, when
        written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other node.'''

        # Keep a set of all seen node ids to prevent infinite recursion.
        seen = set()
        pb_nodes = []

        # Loop over all the nodes in data and log all nodes that use
        # pointers to a list. Any pointer based nodes will NOT be entered.
        # The size of all non-pointer nodes will be calculated and used
        # as the starting offset pointer based nodes.
        offset = self.data.collect_pointers(offset, seen, pb_nodes)

        # Repeat this until there are no longer any pointer
        # based nodes for which to calculate pointers.
        while pb_nodes:
            new_pb_nodes = []

            # Iterate over the list of pointer based nodes and set their
            # pointers while incrementing the offset by the size of each node.

            # While doing this, build a new list of all the pointer based
            # nodes in all of the nodes currently being iterated over.
            for node in pb_nodes:
                node, attr_index, substruct = node[0], node[1], node[2]
                node.set_meta('POINTER', offset, attr_index)
                offset = node.collect_pointers(
                    offset, seen, new_pb_nodes, substruct, True, attr_index)
                # This has been commented out since there will be a routine
                # later that will collect all pointers and if one doesn't
                # have a matching node in the structure somewhere then the
                # pointer will be set to 0 since it doesnt exist.
                '''
                #In binary structs, usually when a node doesnt exist its
                #pointer will be set to zero. Emulate this by setting the
                #pointer to 0 if the size is zero(there is nothing to read)
                if node.get_size(attr_index) > 0:
                    node.set_meta('POINTER', offset, attr_index)
                    offset = node.collect_pointers(offset, seen,
                                                    new_pb_nodes, False,
                                                    True, attr_index)
                else:
                    node.set_meta('POINTER', 0, attr_index)'''

            # restart the loop using the next level of pointer based nodes
            pb_nodes = new_pb_nodes

    @property
    def def_id(self):
        try:
            return self.definition.def_id
        except AttributeError:
            return None

    def pprint(self, **kwargs):
        '''
        A method for constructing a string detailing everything in the Tag.
        Can print detailed information on a corrupted Tag for debugging.

        Returns a formatted string representation of the Tag.

        Optional keywords arguments:
        # bool:
        printout --- Whether or to print the constructed string line by line.

        # int:
        indent ----- The number of spaces of indent added per indent level.
        precision -- The number of decimals to round floats to.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located in in its parent
            name ------ The name of the field
            value ----- The field value(the node)
            type ------ The FieldType of the field
            size ------ The size of the field
            offset ---- The offset(or pointer) of the field
            parent_id - The id() of each nodes parent.
            node_id --- The id() of the node
            node_cls -- The type() of the node
            endian ---- The endianness of the field
            flags ----- The individual flags(offset, name, value) in a bool
            trueonly -- Limit flags shown to only the True flags
            steptrees - Nodes parented to a Block as steptrees
            filepath -- The tags filepath
            unique ---- Whether or not the descriptor of an attribute is unique
            binsize --- The size of the tag if it were serialized to a file
            ramsize --- The number of bytes of ram the python objects that
                        compose the tag, its nodes, and other properties
                        stored in its __slots__ and __dict__ take up.
        '''
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        if 'all' in show:
            show.update(ALL_SHOW)
        precision = kwargs.get('precision', None)

        tag_str = ''

        if 'filepath' in show:
            tag_str = self.filepath
            tag_str += '\n'

        # make the string
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

                    tag_str += (
                        '"In-memory tag"  is %s times as large.\n' % objx +
                        '"In-memory data" is %s times as large.\n' % datax)
            except Exception:
                tag_str += SIZE_CALC_FAIL + '\n'

        if kwargs.get('printout'):
            # print the string line by line
            for line in tag_str.split('\n'):
                try:
                    print(line)
                except:
                    print(
                        ' '*(len(line) - len(line.lstrip(' '))) + UNPRINTABLE)
            return ''
        return tag_str

    def parse(self, **kwargs):
        '''
        Optional keywords arguments:
        # bool:
        init_attrs -----
        allow_corrupt --

        # buffer:
        rawdata --------

        # int:
        root_offset ----
        offset ---------

        # iterable:
        initdata -------

        #str:
        filepath -------
        '''
        if not kwargs.get('rawdata'):
            kwargs.setdefault('filepath', self.filepath)
        kwargs.setdefault('root_offset', self.root_offset)
        filepath = kwargs.get('filepath')

        desc = self.definition.descriptor
        block_type = desc.get(NODE_CLS, desc[TYPE].node_cls)

        # Create the root node and set self.data to it before parsing.
        new_tag_data = self.data = block_type(desc, parent=self)

        if filepath:
            self.filepath = filepath
            # If this is an incomplete object then we
            # need to keep a path to the source file
            if self.definition.incomplete:
                self.sourcepath = filepath
        elif 'rawdata' not in kwargs:
            kwargs['init_attrs'] = True

        # whether or not to allow corrupt tags to be built.
        # this is a debugging tool.
        if kwargs.pop('allow_corrupt', False):
            try:
                new_tag_data.parse(**kwargs)
            except OSError:
                # file was likely not found, or something similar
                raise
            except Exception:
                print(format_exc())
        else:
            new_tag_data.parse(**kwargs)

    def serialize(self, **kwargs):
        '''
        Attempts to serialize the tag to it's current
        filepath, but while appending ".temp" to the end. if it
        successfully saved then it will attempt to either backup or
        delete the old tag and remove .temp from the resaved one.
        '''
        data = self.data
        filepath = kwargs.pop('filepath', self.filepath)

        if kwargs.get('buffer') is not None:
            return data.serialize(**kwargs)

        temp = kwargs.pop('temp', True)
        backup = kwargs.pop('backup', True)
        buffer = kwargs.pop('buffer', None)

        calc_pointers = bool(kwargs.pop('calc_pointers', self.calc_pointers))

        # If the definition doesnt exist then dont test after writing
        try:
            int_test = self.definition.build
        except AttributeError:
            int_test = False

        if 'int_test' in kwargs:
            int_test = bool(kwargs.pop('int_test'))
        elif 'integrity_test' in kwargs:
            int_test = bool(kwargs.pop('integrity_test'))

        if filepath == '':
            raise IOError(
                "Invalid filepath. Cannot serialize to '%s'" % self.filepath)

        # If the filepath ends with the folder path terminator, raise an error
        if filepath.endswith(PATHDIV):
            raise IOError('filepath must be a path to a file, not a folder.')

        folderpath = dirname(filepath)
        # If the path doesnt exist, create it
        if not exists(folderpath):
            makedirs(folderpath)

        temppath = filepath + ".temp"
        backuppath = filepath + ".backup"
        if not backup:
            backuppath = None

        # to avoid 'open' failing if windows files are hidden, we
        # open in 'r+b' mode and truncate if the file exists.
        mode = 'r+b' if isfile(temppath) else 'w+b'
        # open the file to be written and start writing!
        with open(temppath, mode) as tagfile:
            tagfile.truncate(0)
            # if this is an incomplete object we need to copy the
            # original file to the path of the new file in order to
            # fill in the data we don't yet understand/have mapped out'''

            # if we need to calculate any pointers, do so
            if calc_pointers:
                self.set_pointers(kwargs.get('offset', 0))

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
                try:
                    datasize = data.binsize
                    tagfile.seek(0, 2)
                    if tagfile.tell() < datasize:
                        tagfile.seek(datasize - 1)
                        tagfile.write(b'\x00')
                except BinsizeError:
                    pass

            kwargs.update(writebuffer=tagfile)
            data.TYPE.serializer(data, **kwargs)

        # if the definition is accessible, we can quick load
        # the tag that was just written to check its integrity
        if int_test:
            try:
                self.definition.build(int_test=True, filepath=temppath)
            except Exception:
                raise IntegrityError(
                    "Serialized Tag failed its data integrity test:\n" +
                    ' '*BPI + str(self.filepath) + '\nTag may be corrupted.')
        if not temp:
            # If we are doing a full save then we try and rename the temp file
            backup_and_rename_temp(filepath, temppath, backuppath)

        return filepath
