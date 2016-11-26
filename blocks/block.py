import os

from copy import deepcopy
from os.path import splitext, dirname, exists
from sys import getsizeof
from traceback import format_exc

from supyr_struct.defs.constants import *
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
    # __slots__ = ('desc', 'parent')

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
                self[desc['NAME_MAP'][attr_name]] = new_value
            elif attr_name in desc:
                raise DescEditError(
                    "Setting entries in a descriptor in this way is not " +
                    "supported. Use the 'set_desc' method instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))
        # if the object being placed in the Block has
        # a 'parent' attribute, set it to this Block.
        if hasattr(new_value, 'parent'):
            object.__setattr__(new_value, 'parent', self)

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
                self.del_desc(attr_name)
                self.__delitem__(self, desc['NAME_MAP'][attr_name])
            elif attr_name in desc:
                raise DescEditError(
                    "Deleting entries from a descriptor in this way is not " +
                    "supported. Use the 'del_desc' method instead.")
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
                        (type(str), type(index)))

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
                            (type(str), type(index)))

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
                            (type(str), type(index)))

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
        if "unique" in show:
            tempstr += ', unique:%s' % ('ORIG_DESC' in desc)
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

        If this Blocks descriptor is unique(denoted by it having an
        'ORIG_DESC' key) then the size of the descriptor and all its
        entries will be included in the byte size total.

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
        if 'ORIG_DESC' in desc and id(desc) not in seenset:
            seenset.add(id(desc))
            bytes_total += getsizeof(desc)
            for key in desc:
                item = desc[key]
                if not isinstance(key, int) and (key != 'ORIG_DESC' and
                                                 id(item) not in seenset):
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

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
        return self.__binsize__(self)

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

    def del_desc(self, desc_key, attr_name=None):
        '''
        Enables clean deletion of attributes from this
        Block's descriptor. Takes care of decrementing
        ENTRIES, shifting indexes of attributes, removal from
        NAME_MAP, and making sure the descriptor is unique.
        Does not shift offsets or change struct size.

        The new descriptor is left as a mutable dict with a
        reference to the original descriptor under ORIG_DESC.
        '''

        desc = object.__getattribute__(self, "desc")

        # if we are setting something in the descriptor
        # of one of this Block's attributes, then we
        # need to set desc to the attributes descriptor
        if attr_name is not None:
            # if the attr_name doesnt exist in the desc, try to
            # see if it maps to a valid key in desc[NAME_MAP]
            if not(attr_name in desc or isinstance(attr_name, int)):
                attr_name = desc['NAME_MAP'][attr_name]
            self_desc = desc
            desc = self_desc[attr_name]

            # Check if the descriptor needs to be made unique
            if 'ORIG_DESC' not in self_desc:
                self_desc = self.make_unique(self_desc)

        if isinstance(desc_key, int):
            # "desc_key" must be a string for the
            # below routine to work, so change it
            desc_key = desc[desc_key]['NAME']

        # Check if the descriptor needs to be made unique
        if not desc.get('ORIG_DESC'):
            desc = self.make_unique(desc)

        name_map = desc.get('NAME_MAP')

        # if we are deleting a descriptor based attribute
        if name_map and desc_key in desc['NAME_MAP']:
            attr_index = name_map[desc_key]

            # if there is an offset mapping to set,
            # need to get a local reference to it
            attr_offsets = desc.get('ATTR_OFFS')

            # delete the name of the attribute from NAME_MAP
            dict.__delitem__(name_map, desc_key)
            # delete the attribute
            dict.__delitem__(desc, attr_index)
            # remove the offset from the list of offsets
            if attr_offsets is not None:
                attr_offsets = list(attr_offsets)
                attr_offsets.pop(attr_index)
                dict.__setitem__(desc, 'ATTR_OFFS', tuple(attr_offsets))
            # decrement the number of entries
            desc['ENTRIES'] -= 1

            # if an attribute is being deleted,
            # then NAME_MAP needs to be shifted down
            # and the key of each attribute needs to be
            # shifted down in the descriptor as well

            last_entry = desc['ENTRIES']

            # shift all the indexes down by 1
            for i in range(attr_index, last_entry):
                dict.__setitem__(desc, i, desc[i+1])
                dict.__setitem__(name_map, desc[i+1]['NAME'], i)

            # now that all the entries have been moved down,
            # delete the topmost entry since it's a copy
            if attr_index < last_entry:
                dict.__delitem__(desc, last_entry)
        else:
            # we are trying to delete something other than an
            # attribute. This isn't safe to do, so raise an error.
            raise DescEditError(("It is unsafe to delete '%s' from " +
                                 "Tag Object descriptor.") % desc_key)

        # replace the old descriptor with the new one
        if attr_name is not None:
            self_desc[attr_name] = desc
            desc = self_desc
        object.__setattr__(self, "desc", FrozenDict(desc))

    def set_desc(self, desc_key, new_value, attr_name=None):
        '''
        Enables cleanly changing the attributes in this
        Block's descriptor or adding non-attributes.
        Takes care of adding to NAME_MAP and other stuff.
        Does not shift offsets or change struct size.

        The new descriptor is left as a mutable dict with a
        reference to the original descriptor under ORIG_DESC.
        '''

        desc = object.__getattribute__(self, "desc")

        # if we are setting something in the descriptor
        # of one of this Block's attributes, then we
        # need to set desc to the attributes descriptor
        if attr_name is not None:
            # if the attr_name doesnt exist in the desc, try to
            # see if it maps to a valid key in desc[NAME_MAP]
            if not(attr_name in desc or isinstance(attr_name, int)):
                attr_name = desc['NAME_MAP'][attr_name]
            self_desc = desc
            desc = self_desc[attr_name]

            # Check if the descriptor needs to be made unique
            if 'ORIG_DESC' not in self_desc:
                self_desc = self.make_unique(self_desc)

        if isinstance(desc_key, int):
            # "desc_key" must be a string for the
            # below routine to work, so change it
            desc_key = desc[desc_key]['NAME']

        desc_name = desc_key
        if 'NAME_MAP' in desc and desc_name in desc['NAME_MAP']:
            desc_name = desc['NAME_MAP'][desc_name]

        # Check if the descriptor needs to be made unique
        if not desc.get('ORIG_DESC') and id(desc[desc_name]) != id(new_value):
            desc = self.make_unique(desc)

        name_map = desc.get('NAME_MAP')
        if name_map and desc_key in desc['NAME_MAP']:
            # we are setting a descriptor based attribute.
            # We might be changing what it's named

            attr_index = name_map[desc_key]

            # if the new_value desc doesnt have a NAME entry, the
            # new_name will be set to the current entry's name
            new_name = new_value.get('NAME', desc_key)

            # if the names are different, change the
            # NAME_MAP and ATTR_OFFS mappings
            if new_name != desc_key:
                # Run a series of checks to make
                # sure the name in new_value is valid
                self.validate_name(new_name, name_map, attr_index)

                # remove the old name from the name_map
                dict.__delitem__(name_map, desc_key)
                # set the name of the attribute in NAME_MAP
                dict.__setitem__(name_map, new_name, attr_index)
            else:
                # If the new_value doesn't have a name,
                # give it the old descriptor's name
                new_value['NAME'] = desc_key

            # set the attribute to the new new_value
            dict.__setitem__(desc, attr_index, new_value)
        else:
            # we are setting something other than an attribute
            # if setting the name, there are some rules to follow
            if desc_key == 'NAME' and new_value != desc.get('NAME'):
                name_map = None
                try:
                    parent = self.parent
                except Exception:
                    pass

                # make sure to change the name in the
                # parent's name_map mapping as well
                if attr_name is not None:
                    name_map = dict(self_desc['NAME_MAP'])
                elif parent:
                    try:
                        name_map = dict(parent.NAME_MAP)
                    except Exception:
                        pass

                # if the parent name mapping exists,
                # change the name that it's mapped to
                if name_map is not None:
                    attr_index = name_map[desc['NAME']]
                    # Run a series of checks to make
                    # sure the name in new_value is valid
                    self.validate_name(new_value, name_map, attr_index)

                    # set the index of the new name to the index of the old one
                    dict.__setitem__(name_map, new_value, attr_index)
                    # delete the old name
                    dict.__delitem__(name_map, desc['NAME'])

                # Now that we've gotten here, it's safe to commit the changes
                if name_map is not None:
                    # set the parent's NAME_MAP to the newly configured one
                    if attr_name is not None:
                        dict.__setitem__(self_desc, 'NAME_MAP', name_map)
                    elif parent:
                        parent.set_desc('NAME_MAP', name_map)

                else:
                    self.validate_name(new_value)

            dict.__setitem__(desc, desc_key, new_value)

        # replace the old descriptor with the new one
        if attr_name is not None:
            dict.__setitem__(self_desc, attr_name, desc)
            object.__setattr__(self, "desc", self_desc)
        else:
            object.__setattr__(self, "desc", desc)

    def ins_desc(self, desc_key, new_value, attr_name=None):
        '''
        Enables clean insertion of attributes into this
        Block's descriptor. Takes care of incrementing
        ENTRIES, adding to NAME_MAP, and shifting indexes.

        The new descriptor is left as a mutable dict with a
        reference to the original descriptor under ORIG_DESC.
        '''

        desc = object.__getattribute__(self, "desc")

        # if we are setting something in the descriptor
        # of one of this Block's attributes, then we
        # need to set desc to the attributes descriptor
        if attr_name is not None:
            # if the attr_name doesnt exist in the desc, try to
            # see if it maps to a valid key in desc[NAME_MAP]
            if not(attr_name in desc or isinstance(attr_name, int)):
                attr_name = desc['NAME_MAP'][attr_name]
            self_desc = desc
            desc = self_desc[attr_name]

            # Check if the descriptor needs to be made unique
            if 'ORIG_DESC' not in self_desc:
                self_desc = self.make_unique(self_desc)

        # Check if the descriptor needs to be made unique
        if not desc.get('ORIG_DESC'):
            desc = self.make_unique(desc)

        # if desc_key is an already existing attribute, we are
        # inserting the new descriptor where it currently is.
        # Thus, we need to get what index the attribute is in.
        if 'NAME_MAP' in desc and desc_key in desc['NAME_MAP']:
            desc_key = desc['NAME_MAP'][desc_key]

        if isinstance(desc_key, int):
            '''we are adding an attribute'''
            name_map = desc['NAME_MAP']
            attr_index = desc_key
            desc_key = new_value['NAME']

            # before any changes are committed, validate the
            # name to make sure we aren't adding a duplicate
            self.validate_name(desc_key, name_map)

            # if there is an offset mapping to set,
            # need to get a local reference to it
            attr_offsets = desc.get('ATTR_OFFS')

            # if an attribute is being added, then
            # NAME_MAP needs to be shifted up and the
            # key of each attribute needs to be
            # shifted up in the descriptor as well

            # shift all the indexes up by 1 in reverse
            for i in range(desc['ENTRIES'], attr_index, -1):
                dict.__setitem__(desc, i, desc[i-1])
                dict.__setitem__(name_map, desc[i-1]['NAME'], i)

            # add name of the attribute to NAME_MAP
            dict.__setitem__(name_map, desc_key, attr_index)
            # add the attribute
            dict.__setitem__(desc, attr_index, new_value)
            # increment the number of entries
            dict.__setitem__(desc, 'ENTRIES', desc['ENTRIES'] + 1)

            if attr_offsets is not None:
                attr_offsets = list(attr_offsets)
                try:
                    # set the offset of the new attribute to
                    # the offset of the old one plus its size
                    offset = (attr_offsets[attr_index - 1] +
                              self.get_size(attr_index - 1))
                except Exception:
                    # If we fail, it means this attribute is the
                    # first in the structure, so its offset is 0
                    offset = 0

                # add the offset of the attribute
                # to the offsets map by name and index
                attr_offsets.insert(attr_index, offset)
                dict.__setitem__(desc, 'ATTR_OFFS', attr_offsets)
        else:
            if isinstance(new_value, dict):
                raise DescEditError(("Supplied value was not a valid " +
                                     "attribute descriptor.\nThese are the " +
                                     "supplied descriptor's keys.\n    %s") %
                                    new_value.keys())
            else:
                raise DescEditError("Supplied value was not a " +
                                    "valid attribute descriptor.\n" +
                                    "Got:\n    %s" % new_value)

        # replace the old descriptor with the new one
        if attr_name is not None:
            dict.__setitem__(self_desc, attr_name, desc)
            object.__setattr__(self, "desc", self_desc)
        else:
            object.__setattr__(self, "desc", desc)

    def res_desc(self, name=None):
        '''Restores the descriptor of the attribute "name"
        WITHIN this Block's descriptor to its backed up
        original. This is done this way in case the attribute
        doesn't have a descriptor, like strings and integers.
        If name is None, restores this Blocks descriptor.'''
        desc = object.__getattribute__(self, "desc")
        name_map = desc['NAME_MAP']

        # if we need to convert name from an int into a string
        if isinstance(name, int):
            name = name_map['NAME']

        if name is not None:
            # restoring an attributes descriptor
            if name in name_map:
                attr_index = name_map[name]
                # restore the descriptor of this Block's
                # attribute if an original exists
                dict.__setitem__(desc, attr_index,
                                 desc[attr_index]['ORIG_DESC'])
            else:
                raise DescKeyError((
                    "'%s' is not an attribute in the Block '%s'. " +
                    "Cannot restore descriptor.") % (name, desc.get('NAME')))
        elif desc.get('ORIG_DESC'):
            # restore the descriptor of this Block
            object.__setattr__(self, "desc", desc['ORIG_DESC'])

    def make_unique(self, desc=None):
        '''Returns a unique copy of the provided descriptor. The
        copy is made unique from the provided one by replacing it
        with a semi-shallow copy and adding a reference to the
        original descriptor under the key "ORIG_DESC". The copy
        is semi-shallow in that the attributes are shallow, but
        entries like NAME_MAP, ATTR_OFFS, and NAME are deep.

        If you use the new, unique, descriptor as this object's
        descriptor, this object will end up using more ram.'''

        if desc is None:
            desc = object.__getattribute__(self, "desc")

        # make a new descriptor with a reference to the original
        new_desc = {'ORIG_DESC': desc}

        # semi shallow copy all the keys in the descriptor
        for key in desc:
            if isinstance(key, int) or key in ('STEPTREE', 'SUB_STRUCT'):
                # if the entry is an attribute then make a reference to it
                new_desc[key] = desc[key]
            else:
                # if the entry IS NOT an attribute then full copy it
                new_desc[key] = deepcopy(desc[key])

        return new_desc

    def get_root(node):
        '''Navigates up the given node and returns the root node.'''
        # rather than name the function argument 'self' it's slightly
        # faster to just name it 'root' and not have to do 'root = self'
        try:
            while True:
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
                if name == '':
                    node = node.parent
                else:
                    node = node.__getattr__(name)
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
                if name == '':
                    node = node.parent
                else:
                    node = node.__getattr__(name)
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

        node.__setattr__(path_names[-1], new_value)

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
        elif isinstance(meta, int):
            self.set_desc(meta_name, new_value, attr_index)
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

        buffer = kwargs.pop('buffer', None)
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

        if isinstance(parent_tag, tag.Tag):
            calc_pointers = parent_tag.calc_pointers
        else:
            calc_pointers = True
            parent_tag = None

        # convert string attr_indexes to ints
        if isinstance(attr_index, str):
            attr_index = self.desc['NAME_MAP'][attr_index]

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
                try: buffer.seek(block.binsize - 1); buffer.write(b'\x00')
                except AttributeError: pass

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
            index ---- The index the field is located in in its parent
            name ----- The name of the field
            value ---- The field value(the node)
            type ----- The FieldType of the field
            size ----- The size of the field
            offset --- The offset(or pointer) of the field
            endian --- The endianness of the field
            unique --- Whether or not the descriptor of a field is unique
            node_id -- The id() of the node
            node_cls - The type() of the node
        '''
        seen = kwargs['seen'] = set(kwargs.get('seen', ()))
        seen.add(id(self))

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
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
            if "unique" in show:
                tempstr += ', unique:%s' % ('ORIG_DESC' in attr_desc)
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

    def validate_name(self, attr_name, name_map={}, attr_index=0):
        '''
        Runs a series of assertions to check if 'attr_name'
        is a valid string to use as an attributes name.
        Returns True if it is, Raises a AssertionError if it isnt.
        '''
        # make sure attr_name is a string
        assert isinstance(attr_name, str), (
            "'attr_name' must be a string, not %s" % type(attr_name))
        # make sure it doesnt already exist, or if it does then
        # it exists in the attr_index we're trying to add it to
        assert name_map.get(attr_name, attr_index) == attr_index, (
            (("'%s' already exists as an attribute in '%s'.\n" +
              'Duplicate names are not allowed.') %
             (attr_name, object.__getattribute__(self, 'desc').get('NAME'))))
        # make sure attr_name isnt an empty string
        assert not attr_name, "'' cannot be used as attribute names."
        # make sure it begins with a valid character
        assert attr_name[0] in ALPHA_IDS, (
            "The first character of an attribute name must be " +
            "either an alphabet character or an underscore.")
        # check all the characters to make sure they are valid identifiers
        assert not attr_name.strip(ALPHA_NUMERIC_IDS_STR), (
            ("'%s' is an invalid identifier as it contains characters " +
             "other than alphanumeric or underscores.") % attr_name)
        # make sure attr_name isnt a descriptor keyword
        assert attr_name not in reserved_desc_names, (
            "Attribute names cannot be descriptor keywords.\n" +
            "Cannot use '%s' as an attribute name." % attr_name)
        return True
