import os
import weakref

from copy import deepcopy
from os.path import splitext, dirname, exists, isfile
from sys import getsizeof
from traceback import format_exc

from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.buffer import (get_rawdata, BytesBuffer,
                                 BytearrayBuffer, PeekableMmap)

# linked to through supyr_struct.__init__
tag = None


class Block():

    # An empty slots needs to be here or else all Blocks will have a dict
    #   When subclassing Block, make sure to at least
    #   include 'desc' and 'parent' as two of the slots.
    __slots__ = ()

    # This would normally go here, but it would break multiple
    # inheritance if subclassing Block and another slotted class.
    # __slots__ = ('desc', '_parent', '__weakref__')

    def __init__(self, desc, parent=None, **kwargs):
        '''You must override this method'''
        raise NotImplementedError('')

    def __getattr__(self, attr_name):
        '''
        Returns the attribute specified by the supplied 'attr_name'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['NAME_MAP'], or in self.desc.

        If object.__getattribute__(self, attr_name) raises an AttributeError,
        then self.desc['NAME_MAP'] will be checked for attr_name in its keys.

        If it exists, returns self[desc['NAME_MAP'][attr_name]]

        If attr_name does not exist in self.desc['NAME_MAP'],
        self.desc will be checked for attr_name in its keys.
        If it exists, returns self.desc[attr_index]

        Raises AttributeError if attr_name cant be found in any of the above.
        '''
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                return self[desc['NAME_MAP'][attr_name]]
            elif attr_name in desc:
                return desc[attr_name]
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_name))

    def __setattr__(self, attr_name, new_value):
        '''docstring'''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                assert not self.assert_is_valid_field_value(
                    desc['NAME_MAP'][attr_name], new_value)
                self[desc['NAME_MAP'][attr_name]] = new_value
            elif attr_name in desc:
                raise DescEditError(
                    "Setting entries in a descriptor in this way is not " +
                    "supported. Make a new descriptor instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))
        # if the object being placed in the Block is itself
        # a Block, set its parent attribute to this Block.
        if attr_name != "parent" and isinstance(new_value, Block):
            new_value.parent = self

    def __delattr__(self, attr_name):
        '''docstring'''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                # set the size of the node to 0 since it's being deleted
                try:
                    self.set_size(0, attr_name)
                except (NotImplementedError, AttributeError):
                    pass
                self.__delitem__(desc['NAME_MAP'][attr_name])
            elif attr_name in desc:
                raise DescEditError(
                    "Deleting entries from a descriptor is not " +
                    "supported. Make a new descriptor instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __getitem__(self, index):
        '''
        Returns the node located at 'index' in this Block.
        index must be the string name of an attribute.

        If 'index' is a string, calls:
            return self.__getattr__(index)
        '''
        if isinstance(index, str):
            return self.__getattr__(index)
        raise TypeError("'index' must be of type '%s', not '%s'" %
                        (str, type(index)))

    def __setitem__(self, index, new_value):
        '''
        Places 'new_value' into this Block at 'index'.
        index must be the string name of an attribute.

        If 'index' is a string, calls:
            self.__setattr__(index, new_value)
        '''
        if isinstance(index, str):
            self.__setattr__(index, new_value)
        else:
            raise TypeError("'index' must be of type '%s', not '%s'" %
                            (str, type(index)))

    def __delitem__(self, index):
        '''
        Deletes an attribute from this Block located in 'index'.
        index must be the string name of an attribute.

        If 'index' is a string, calls:
            self.__delattr__(index)
        '''
        if isinstance(index, str):
            self.__delattr__(index)
        else:
            raise TypeError("'index' must be of type '%s', not '%s'" %
                            (str, type(index)))

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this Block.

        Optional keywords arguments:
        # int:
        attr_index - The index this Block is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
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
            value ----- The field value(the node)
            type ------ The FieldType of the field
            size ------ The size of the field
            offset ---- The offset(or pointer) of the field
            parent_id - The id() of self.parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
            endian ---- The endianness of the field
            flags ----- The individual flags(offset, name, value) in a bool
            trueonly -- Limit flags shown to only the True flags
            steptrees - Fields parented to the node as steptrees
        '''
        seen = kwargs['seen'] = set(kwargs.get('seen', ()))
        seen.add(id(self))

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        level = kwargs.get('level', 0)
        indent = kwargs.get('indent', NODE_PRINT_INDENT)
        attr_index = kwargs.get('attr_index', None)

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(ALL_SHOW)

        tag_str = ' '*indent*level + '['
        tempstr = ''

        desc = object.__getattribute__(self, 'desc')
        f_type = desc['TYPE']

        if "index" in show and attr_index is not None:
            tempstr += ', %s' % attr_index
        if "type" in show:
            tempstr += ', %s' % f_type.name
        if "endian" in show:
            tempstr += ', endian:%s' % f_type.endian
        try:
            if "offset" in show:
                tempstr += ', offset:%s' % (self.parent.desc['ATTR_OFFS']
                                            [attr_index])
        except Exception:
            pass
        if "parent_id" in show:
            tempstr += ', parent_id:%s' % id(self.parent)
        if "node_id" in show:
            tempstr += ', node_id:%s' % id(self)
        if "node_cls" in show:
            tempstr += ', node_cls:%s' % f_type.node_cls
        if "size" in show:
            tempstr += ', size:%s' % self.get_size()
        if "name" in show:
            attr_name = kwargs.get('attr_name', UNNAMED)
            if attr_name == UNNAMED:
                attr_name = desc.get('NAME')
            tempstr += ', %s' % attr_name

        tag_str += tempstr + ' ]'

        return tag_str

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this Block, all its nodes, and all
        its other attributes take up in memory.

        'seen_set' is a set of python object ids used to keep track
        of whether or not an object has already been added to the byte
        total at some earlier point. This was added for more accurate
        measurements that dont count descriptor sizes multiple times.
        '''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = object.__sizeof__(self)

        desc = object.__getattribute__(self, 'desc')

        return bytes_total

    def __binsize__(self, node, substruct=False):
        '''You must override this method'''
        raise NotImplementedError(
            'binsize calculation must be manually defined per Block subclass.')

    @property
    def binsize(self):
        '''
        Returns the size of this Block and all nodes parented to it.
        This size is how many bytes it would take up if written to a buffer.
        '''
        try:
            return self.__binsize__(self)
        except Exception as exc:
            raise BinsizeError("Could not calculate binary size.") from exc

    def get_desc(self, desc_key, attr_name=None):
        '''Returns the value in the object's descriptor
        under the key "desc_key". If attr_name is not None,
        the descriptor being searched for "desc_key" will
        instead be the attribute "attr_name".'''
        desc = object.__getattribute__(self, "desc")

        # if we are getting something in the descriptor
        # of one of this Block's attributes, then we
        # need to set desc to the attributes descriptor
        if attr_name is not None:
            if isinstance(attr_name, int) or attr_name in desc:
                desc = desc[attr_name]
            else:
                try:
                    desc = desc[desc['NAME_MAP'][attr_name]]
                except Exception:
                    raise DescKeyError(("Could not locate '%s' in " +
                                        "the descriptor of '%s'.") %
                                       (attr_name, desc.get('NAME')))

        # Try to return the descriptor value under the key "desc_key"
        if desc_key in desc:
            return desc[desc_key]

        try:
            return desc[desc['NAME_MAP'][desc_key]]
        except KeyError:
            if attr_name is not None:
                raise DescKeyError(("Could not locate '%s' in the " +
                                    "sub-descriptor '%s' in the descriptor " +
                                    "of '%s'") % (desc_key, attr_name,
                                                  desc.get('NAME')))
            else:
                raise DescKeyError(("Could not locate '%s' in the " +
                                    "descriptor of '%s'.") %
                                   (desc_key, desc.get('NAME')))

    def get_root(node):
        '''Navigates up the given node and returns the root node.'''
        # rather than name the function argument 'self' it's slightly
        # faster to just name it 'root' and not have to do 'root = self'
        try:
            while node.parent:
                node = node.parent
        except AttributeError:
            pass
        return node

    def get_neighbor(self, path, node=None):
        '''
        Given a nodepath to follow, this function
        will navigate neighboring nodes until the
        path is exhausted and return the last node.
        '''
        if not isinstance(path, str):
            raise TypeError("'path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(path)))
        elif not path:
            if node is None:
                return self
            else:
                return node

        path_names = path.split('.')

        # if a starting node wasn't provided, or it was
        # and it's not a Block with a parent reference
        # we need to set it to something we can navigate from
        if not hasattr(node, 'parent'):
            if path_names and path_names[0] == "":
                # If the first direction in the path is to go to the
                # parent, set node to self (because node may not be
                # navigable from) and delete the first path direction
                node = self
                del path_names[0]
            else:
                # if the first path isn't "Go to parent",
                # then it means it's not a relative path.
                # Thus the path starts at the data root
                node = self.get_root().data
        try:
            for name in path_names:
                try:
                    node = node.parent if not name else node.__getattr__(name)
                except AttributeError:
                    if name and (name[0] == "[" and name[-1] == "]"):
                        node = node.__getitem__(int(name[1: -1]))
                    else:
                        raise
        except Exception:
            self_name = object.__getattribute__(self, 'desc').get('NAME',
                                                                  type(self))
            try:
                attr_name = node.NAME
            except Exception:
                attr_name = type(node)
            try:
                raise AttributeError(("Path string to neighboring node is " +
                                      "invalid.\nStarting node was '%s'. " +
                                      "Couldnt find '%s' in '%s'.\n" +
                                      "Full path was '%s'") %
                                     (self_name, name, attr_name, path))
            except NameError:
                raise AttributeError(("Path string to neighboring node " +
                                      "is invalid.\nStarting node " +
                                      "was '%s'. Full path was '%s'") %
                                     (self_name, path))
        return node

    def get_meta(self, meta_name, attr_index=None, **context):
        '''
        '''
        desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, int):
            node = self[attr_index]
            if desc['TYPE'].is_array:
                desc = desc['SUB_STRUCT']
            else:
                desc = desc[attr_index]
        elif isinstance(attr_index, str):
            node = self.__getattr__(attr_index)
            try:
                desc = desc[desc['NAME_MAP'][attr_index]]
            except Exception:
                desc = desc[attr_index]
        else:
            node = self

        if meta_name in desc:
            meta = desc[meta_name]

            if isinstance(meta, int):
                return meta
            elif isinstance(meta, str):
                # get the pointed to meta data by traversing the tag
                # structure along the path specified by the string
                return self.get_neighbor(meta, node)
            elif hasattr(meta, "__call__"):
                # find the pointed to meta data by calling the function
                if hasattr(node, 'parent'):
                    return meta(attr_index=attr_index, parent=node.parent,
                                node=node, **context)
                return meta(attr_index=attr_index, parent=self,
                            node=node, **context)

            else:
                raise LookupError("Couldnt locate meta info")
        else:
            attr_name = object.__getattribute__(self, 'desc')['NAME']
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            raise AttributeError("'%s' does not exist in '%s'." %
                                 (meta_name, attr_name))

    def get_size(self, attr_index=None, **context):
        '''getsize must be overloaded by subclasses'''
        raise NotImplementedError('Overload this method')

    def set_neighbor(self, path, new_value, node=None):
        '''
        Given a path to follow, this function
        will navigate neighboring nodes until the
        path is exhausted and set the last node.
        '''
        if not isinstance(path, str):
            raise TypeError("'path' argument must be of type " +
                            "'%s', not '%s'" % (str, type(path)))

        path_names = path.split('.')

        # if a starting node wasn't provided, or it was
        # and it's not a Block with a parent reference
        # we need to set it to something we can navigate from
        if not hasattr(node, 'parent'):
            if path_names and path_names[0] == "":
                # If the first direction in the path is to go to the
                # parent, set node to self (because node may not be
                # navigable from) and delete the first path direction
                node = self
                del path_names[0]
            else:
                # if the first path isn't "Go to parent",
                # then it means it's not a relative path.
                # Thus the path starts at the data root
                node = self.get_root().data
        try:
            for name in path_names[:-1]:
                try:
                    node = node.parent if not name else node.__getattr__(name)
                except AttributeError:
                    if name and (name[0] == "[" and name[-1] == "]"):
                        node = node.__getitem__(int(name[1: -1]))
                    else:
                        raise
        except Exception:
            self_name = object.__getattribute__(self, 'desc').get('NAME',
                                                                  type(self))
            try:
                attr_name = node.NAME
            except Exception:
                attr_name = type(node)
            try:
                raise AttributeError(("path string to neighboring node is " +
                                      "invalid.\nStarting node was '%s'. " +
                                      "Couldnt find '%s' in '%s'.\n" +
                                      "Full path was '%s'") %
                                     (self_name, name, attr_name, path))
            except NameError:
                raise AttributeError(("path string to neighboring node " +
                                      "is invalid.\nStarting node was " +
                                      "'%s'. Full path was '%s'") %
                                     (self_name, path))

        name = path_names[-1]
        if name and (name[0] == "[" and name[-1] == "]"):
            node.__setitem__(int(name[1: -1]), new_value)
        else:
            node.__setattr__(name, new_value)

        return node

    def set_meta(self, meta_name, new_value=None, attr_index=None, **context):
        '''
        '''
        desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, int):
            node = self[attr_index]
            attr_name = attr_index
            if desc['TYPE'].is_array:
                desc = desc['SUB_STRUCT']
            else:
                desc = desc[attr_index]
        elif isinstance(attr_index, str):
            node = self.__getattr__(attr_index)
            attr_name = attr_index
            try:
                desc = desc[desc['NAME_MAP'][attr_index]]
            except Exception:
                desc = desc[attr_index]
        else:
            node = self
            attr_name = desc['NAME']

        meta = desc.get(meta_name)

        # raise exception if the meta is None
        if meta is None and meta_name not in desc:
            raise AttributeError("'%s' does not exist in '%s'."
                                 % (meta_name, attr_name))
        elif isinstance(meta, str):
            # set meta by traversing the tag structure
            # along the path specified by the string
            self.set_neighbor(meta, new_value, node)
        elif hasattr(meta, "__call__"):
            # set the meta by calling the provided function
            if hasattr(node, 'parent'):
                meta(attr_index=attr_index, new_value=new_value,
                     parent=node.parent, node=node, **context)
            else:
                meta(attr_index=attr_index, new_value=new_value,
                     parent=self, node=node, **context)
        else:
            raise TypeError(("meta specified in '%s' is not a valid type." +
                             "Expected str or function. Got %s.\n" +
                             "Cannot determine how to set the meta data.") %
                            (attr_name, type(meta)))

    def set_size(self, new_value, attr_index=None, **context):
        '''setsize must be overloaded by subclasses'''
        raise NotImplementedError('Overload this method')

    def collect_pointers(self, offset=0, seen=None, pointed_nodes=None,
                         substruct=False, root=False, attr_index=None):
        if seen is None:
            seen = set()

        if attr_index is None:
            desc = object.__getattribute__(self, 'desc')
            node = self
        else:
            desc = self.get_desc(attr_index)
            node = self.__getattr__(attr_index)

        if 'POINTER' in desc:
            pointer = desc['POINTER']
            if isinstance(pointer, int):
                # if the next nodes are to be located directly after
                # this one then set the current offset to its location
                offset = pointer

            # if this is a node within the root node
            if not root:
                pointed_nodes.append((self, attr_index, substruct))
                return offset

        seen.add(id(node))

        f_type = desc['TYPE']

        if desc.get('ALIGN'):
            align = desc['ALIGN']
            offset += (align - (offset % align)) % align

        # increment the offset by this nodes size if it isn't a substruct
        if not(substruct or f_type.is_container):
            offset += self.get_size()
            substruct = True

        return offset

    def set_pointers(self, offset=0):
        '''Scans through this Block and sets the pointer of
        each pointer based node in a way that ensures that,
        when written to a buffer, its binary data chunk does not
        overlap with the binary data chunk of any other node.

        This function is a copy of the Tag.collect_pointers().
        This is ONLY to be called by a Block when it is writing
        itself so the pointers can be set as though this is the root.'''

        # Keep a set of all seen node ids to prevent infinite recursion.
        seen = set()
        pb_nodes = []

        # Loop over all the nodes in self and log all nodes that use
        # pointers to a list. Any pointer based nodes will NOT be entered.

        # The size of all non-pointer nodes will be calculated and used
        # as the starting offset pointer based nodes.
        offset = self.collect_pointers(offset, seen, pb_nodes)

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
                offset = node.collect_pointers(offset, seen, new_pb_nodes,
                                                substruct, True, attr_index)
                # this has been commented out since there will be a routine
                # later that will collect all pointers and if one doesn't
                # have a matching node in the structure somewhere then the
                # pointer will be set to 0 since it doesnt exist.
                '''
                # In binary structs, usually when a node doesnt exist its
                # pointer will be set to zero. Emulate this by setting the
                # pointer to 0 if the size is zero(there is nothing to read)
                if node.get_size(attr_index) > 0:
                    node.set_meta('POINTER', offset, attr_index)
                    offset = node.collect_pointers(offset, seen,
                                                    new_pb_nodes, False,
                                                    True, attr_index)
                else:
                    node.set_meta('POINTER', 0, attr_index)'''

            # restart the loop using the next level of pointer based nodes
            pb_nodes = new_pb_nodes

    def parse(self, **kwargs):
        ''''''
        raise NotImplementedError(
            'Subclasses of Block must define their own parse() method.')

    def serialize(self, **kwargs):
        '''
        This function will serialize this Block to the provided
        filepath/buffer. The name of the Block will be used as the
        extension. This function is used ONLY for writing a piece
        of a tag to a file/buffer, not the entire tag. DO NOT CALL
        this function when writing a whole tag at once.
        '''

        buffer = kwargs.pop('buffer', kwargs.pop('writebuffer', None))
        filepath = kwargs.pop('filepath', None)
        temp = kwargs.pop('temp',  False)
        clone = kwargs.pop('clone', True)
        zero_fill = kwargs.pop('zero_fill', True)

        attr_index = kwargs.pop('attr_index', None)
        root_offset = kwargs.pop('root_offset', 0)
        offset = kwargs.pop('offset', 0)
        
        kwargs.pop('parent', None)

        mode = 'buffer'
        parent = None
        block = self
        desc = self.desc
        if buffer is None:
            mode = 'file'

        if 'tag' in kwargs:
            parent_tag = kwargs.pop("tag")
        else:
            parent_tag = self.get_root()

        if "calc_pointers" in kwargs:
            calc_pointers = kwargs["calc_pointers"]
        if isinstance(parent_tag, tag.Tag):
            calc_pointers = parent_tag.calc_pointers
        else:
            calc_pointers = True
            parent_tag = None

        # convert string attr_indexes to ints
        if isinstance(attr_index, str) and attr_index not in desc:
            attr_index = desc['NAME_MAP'][attr_index]

        # if we are serializing an attribute, change some stuff
        if attr_index is not None:
            parent = self
            block = self[attr_index]
            desc = desc[attr_index]

        calc_pointers = bool(kwargs.pop("calc_pointers", calc_pointers))

        if filepath is None and buffer is None:
            # neither a filepath nor a buffer were
            # given, so make a BytearrayBuffer to write to.
            buffer = BytearrayBuffer()
            mode = 'buffer'
        elif filepath is not None and buffer is not None:
            raise IOError("Provide either a buffer or a filepath, not both.")

        if mode == 'file':
            folderpath = dirname(filepath)

            # if the filepath ends with the path terminator, raise an error
            if filepath.endswith(PATHDIV):
                raise IOError('filepath must be a valid path ' +
                              'to a file, not a folder.')

            # if the path doesnt exist, create it
            if not exists(folderpath):
                os.makedirs(folderpath)

            if temp:
                filepath += ".temp"
            try:
                # to avoid 'open' failing if windows files are hidden, we
                # open in 'r+b' mode and truncate if the file exists.
                if isfile(filepath):
                    buffer = open(filepath, 'r+b')
                    buffer.truncate(0)
                else:
                    buffer = open(filepath, 'w+b')
            except Exception:
                raise IOError('Output filepath for serializing Block ' +
                              'was invalid or the file could not ' +
                              'be created.\n    %s' % filepath)

        # make sure the buffer has a valid write and seek routine
        if not (hasattr(buffer, 'write') and hasattr(buffer, 'seek')):
            raise TypeError('Cannot serialize a Block without either' +
                            ' an output path or a writable buffer')

        cloned = False
        # try to write the Block to the buffer
        try:
            # if we need to calculate the pointers, do so
            if calc_pointers:
                # Make a copy of this Block so any changes
                # to pointers dont affect the entire Tag
                try:
                    if clone:
                        block = block.__deepcopy__({})
                        cloned = True
                        # remove the parent so any pointers
                        # higher in the tree are unaffected
                        block.parent = None
                    block.set_pointers(offset)
                except (NotImplementedError, AttributeError):
                    pass

            # make the buffer as large as the Block is calculated to fill
            if zero_fill:
                try:
                    blocksize = block.binsize
                    buffer.seek(0, 2)
                    if buffer.tell() < blocksize:
                        buffer.seek(blocksize - 1)
                        buffer.write(b'\x00')
                except AttributeError:
                    pass

            # commence the writing process
            desc[TYPE].serializer(block, parent=parent, attr_index=attr_index,
                                  writebuffer=buffer, root_offset=root_offset,
                                  offset=offset, **kwargs)

            # if a copy of the Block was made, delete the copy
            if cloned:
                del block
                cloned = False

            # return the filepath or the buffer in case
            # the caller wants to do anything with it
            if mode == 'file':
                try:
                    buffer.close()
                except Exception:
                    pass
                return filepath
            return buffer
        except Exception as e:
            if mode == 'file':
                try:
                    buffer.close()
                except Exception:
                    pass
            try:
                os.remove(filepath)
            except Exception:
                pass
            # if a copy of the Block was made, delete the copy
            if cloned:
                del block
            a = e.args[:-1]
            e_str = "\n"
            try:
                e_str = e.args[-1] + e_str
            except IndexError:
                pass
            e.args = a + (e_str + "Error occurred while attempting " +
                          "to serialize the Block:\n    " + str(filepath),)
            raise e

    @property
    def parent(self):
        return self._parent()

    @parent.setter
    def parent(self, new_val):
        try:
            self._parent = weakref.ref(new_val)
        except TypeError:
            self._parent = lambda val=new_val: val

    @parent.deleter
    def parent(self):
        del self._parent

    def pprint(self, **kwargs):
        '''
        A method for constructing a string detailing everything in the Block.
        Can print a partially corrupted Block for debugging purposes.

        Returns a formatted string representation of the Block.

        Optional keywords arguments:
        # bool:
        printout --- Whether or to print the constructed string line by line.

        # int:
        indent ----- The number of spaces of indent added per indent level
        precision -- The number of decimals to round floats to

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located in in its parent
            name ------ The name of the field
            value ----- The field value(the node)
            type ------ The FieldType of the field
            size ------ The size of the field
            offset ---- The offset(or pointer) of the field
            parent_id - The id() of self.parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
            endian ---- The endianness of the field
            flags ----- The individual flags(offset, name, value) in a bool
            trueonly -- Limit flags shown to only the True flags
            steptrees - Fields parented to the node as steptrees
            unique ---- Whether or not the descriptor of a field is unique
            binsize --- The size of the Tag if it were serialized to a file
            ramsize --- The number of bytes of ram the python objects that
                        compose the Block, its nodes, and other properties
                        stored in its __slots__ and __dict__ take up.
        '''
        # set the default things to show
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(ALL_SHOW)
        precision = kwargs.get('precision', None)

        tag_str = self.__str__(**kwargs) + '\n'

        if "ramsize" in show:
            blocksize = self.__sizeof__()
            tag_str += '"In-memory block" is %s bytes\n' % blocksize

        if "binsize" in show:
            try:
                block_binsize = self.binsize
                tag_str += '"Packed structure" is %s bytes\n' % block_binsize
                if "ramsize" in show:
                    xlarger = "∞"
                    if block_binsize:
                        xlarger = blocksize / block_binsize
                        if isinstance(precision, int):
                            fmt = "{:.%sf}" % precision
                            xlarger = fmt.format(round(xlarger, precision))

                    tag_str += ('"In-memory block" is %s times as large.\n' %
                                xlarger)
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
            return ''
        return tag_str

    def attr_to_str(self, **kwargs):
        '''
        Returns a formatted string representation of the attribute
        specified by attr_index. Intended to be used on nodes which
        are not Blocks and dont have a similar __str__ method.

        Optional keywords arguments:
        # int:
        attr_index - The index this node is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
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
            endian ---- The endianness of the field
            unique ---- Whether or not the descriptor of a field is unique
            parent_id - The id() of self.parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
        '''
        seen = kwargs['seen'] = set(kwargs.get('seen', ()))
        seen.add(id(self))

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        attr_index = kwargs.get('attr_index')
        indent = kwargs.get('indent', NODE_PRINT_INDENT)
        precision = kwargs.get('precision', None)
        kwargs.setdefault('level', 0)
        kwargs['show'] = show

        if attr_index is None:
            raise KeyError("Formatting a string for a Blocks node attribute " +
                           "requires the index of the attribute be " +
                           "supplied under the key 'attr_index'")

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.remove('all')
            show.update(ALL_SHOW)

        indent_str = ' '*indent*kwargs['level']

        desc = object.__getattribute__(self, 'desc')
        if isinstance(attr_index, str):
            node = self.__getattr__(attr_index)
        else:
            node = self[attr_index]

        name_map = desc.get('NAME_MAP', ())
        attr_offsets = desc.get('ATTR_OFFS', ())

        tag_str = ''

        if not isinstance(node, Block):
            tag_str += indent_str + '['
            tempstr = tempstr2 = ''

            try:
                if desc['TYPE'].is_array:
                    attr_desc = desc['SUB_STRUCT']
                else:
                    attr_desc = desc[attr_index]
            except Exception:
                try:
                    attr_desc = desc[name_map[attr_index]]
                except Exception:
                    return tag_str[:-1] + MISSING_DESC % type(node) + '\n'

            f_type = attr_desc['TYPE']
            if "index" in show:
                tempstr += ', %s' % attr_index
            if "type" in show:
                tempstr += ', %s' % attr_desc['TYPE'].name
            if "endian" in show:
                tempstr += ', endian:%s' % f_type.endian
            if "offset" in show:
                try:
                    tempstr += ', offset:%s' % attr_offsets[attr_index]
                except Exception:
                    pass
            if "parent_id" in show:
                tempstr += ', parent_id:%s' % id(self)
            if "node_id" in show:
                tempstr += ', node_id:%s' % id(node)
            if "node_cls" in show:
                tempstr += ', node_cls:%s' % f_type.node_cls
            if "size" in show:
                try:
                    tempstr += ', size:%s' % self.get_size(attr_index)
                except Exception:
                    pass
            if "name" in show:
                attr_name = kwargs.get('attr_name', UNNAMED)
                if attr_name == UNNAMED:
                    attr_name = attr_desc.get('NAME')
                tempstr += ', %s' % attr_name

            if "value" in show:
                if isinstance(node, float) and isinstance(precision, int):
                    tempstr2 += ((", {:.%sf}" % precision).format
                                 (round(node, precision)))
                elif f_type.is_raw and "raw" not in show:
                    tempstr2 += ', ' + RAWDATA
                else:
                    tempstr2 += ', %s' % node

            tag_str += (tempstr + tempstr2).replace(',', '', 1) + ' ]'

        elif id(node) in seen:
            # this is a Block that has been seen
            if "index" in show:
                tempstr += '%s, ' % attr_index
            tag_str += (indent_str + '[ ' + tempstr +
                        RECURSIVE % (node.NAME, id(node)))
        else:
            # this is a Block that has not been seen
            try:
                tag_str += node.__str__(**kwargs)
            except Exception:
                tag_str += '\n' + format_exc()

        return tag_str + '\n'

    def assert_are_valid_field_values(self, attr_indices, new_values):
        for attr_index, new_value in zip(attr_indices, new_values):
            self.assert_is_valid_field_value(attr_index, new_value)

    def assert_is_valid_field_value(self, attr_index, new_value):
        desc = object.__getattribute__(self, "desc")
        if desc['TYPE'].is_array and isinstance(attr_index, int):
            attr_desc = desc['SUB_STRUCT']
        else:
            attr_desc = desc[attr_index]

        if (attr_desc['TYPE'].is_block and
            not isinstance(new_value, (Block, NoneType))):
            raise TypeError(
                "'%s' field in '%s' of type %s must be a Block" %
                (attr_desc.get('NAME', UNNAMED),
                 desc.get('NAME', UNNAMED), type(self)))
