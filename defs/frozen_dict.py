'''
A module that implements a FrozenDict class,
which aims to be as immutable as possible
while maintaining the speed of a regular dict.
'''

__all__ = ('FrozenDict', 'submutables', 'mutable_typemap', 'immutable_typemap')

# used to determine if a type can contain mutable objects
submutables = set((tuple, list, dict, set))

# used to determine what pytype to convert a mutable python object into
mutable_typemap = {list: tuple, set: frozenset}

# used to determine what pytype to convert an immutable python object into
immutable_typemap = {tuple: list, frozenset: set}


class FrozenDict(dict):
    __slots__ = ()

    def __init__(self, initializer=(), **kw):
        '''
        Converts all dicts, sets, and lists contained in
        the immediate nesting layer of this FrozenDict into
        FrozenDicts, FrozenSets, and tuples respectively.

        Lists and sets will be traversed and their contents will
        be converted into their corresponding immutable versions.
        '''
        # make sure the FrozenDict hasnt already been built
        if self:
            # This could be made more secure by making a private bool
            # attribute which determines if the instances __init__ has
            # already been run, but that would require another __slot__.
            # With how many of these are likely to be made I want to keep
            # the memory footprint as small as possible, so no extra bool.
            return

        if isinstance(initializer, dict):
            if isinstance(initializer, FrozenDict):
                # if the initializer is a FrozenDict, assume it is immutified
                dict.update(self, initializer)
            elif initializer:
                dict.update(self, self.immutify(initializer))
        elif initializer:
            self._update_from_k_v_pairs(*initializer)

        if kw:
            dict.update(self, self.immutify(kw))

    def __delitem__(self, key):
        raise TypeError('%s does not support item deletion' % type(self))

    def __copy__(self):
        return self

    def __deepcopy__(self, memo=None):
        return self

    def __repr__(self):
        return "FrozenDict(%s)" % dict.__repr__(self)

    def __setitem__(self, key, value):
        raise TypeError('%s does not support item assignment' % type(self))

    def __hash__(self):
        return hash(tuple(self.keys())) ^ hash(tuple(self.values()))

    def _update_from_k_v_pairs(self, *k_v_pairs):
        '''
        Used internally by the implementation to initialize a
        FrozenDict with an initializer made of (key, value) tuples.
        Also used when making a modified copy of a FrozenDict.
        '''
        # the k_v_pairs can contain mutable data, so its contents
        # need to be immutified to make sure none of it is mutable.
        dict.update(self, self.immutify({p[0]: self._immutify(p[1], {})
                                         for p in k_v_pairs}))

    def clear(self):
        raise TypeError('%s does not support item clearing' % type(self))

    def copyremove(self, keys, can_miss=False):
        '''
        Returns a copy of this FrozenDict instance with
        the keys specified in the 'keys' argument removed.

        If can_miss is True, attempts to delete missing keys will pass.
        If can_miss is False, deleting missing keys raises a KeyError.
        Defaults to can_miss = False
        '''
        new_fdict = FrozenDict(self)
        _ddi = dict.__delitem__

        if can_miss:
            for key in keys:
                try:
                    _ddi(new_fdict, key)
                except KeyError:
                    pass
            return new_fdict

        for key in keys:
            _ddi(new_fdict, key)
        return new_fdict

    def copyadd(self, k_v_pairs=(), **initdata):
        '''
        Returns an updated copy of this FrozenDict using an iterable
        of supplied keyword argumentsand/or a positional argument
        iterable containing iterables in a (key,value) arrangement.

        The positional argument list is used to update the
        FrozenDict before the keyword arguments are.
        '''
        new_fdict = dict.__new__(FrozenDict, k_v_pairs)
        dict.__init__(new_fdict, self)
        dict.update(new_fdict, new_fdict.immutify(initdata))

        return new_fdict

    def fromkeys(self, keys, value=None):
        '''
        Returns a new FrozenDict with keys
        from 'keys' and values equal to value.
        '''
        new_fdict = FrozenDict()
        dictset = dict.__setitem__

        for key in keys:
            dictset(new_fdict, key, value)

        return new_fdict

    def _immutify(self, iterable, memo):
        '''
        Scans through 'iterable' and makes sure everything in it is
        an immutable object. If it isn't, the object is turned into
        its equivalent immutable version. If no equivalent immmutable
        version exists for that type, a TypeError is raised instead.
        '''
        i_id = id(iterable)
        if i_id in memo:
            return memo[i_id]

        i_type = type(iterable)
        immutify = self._immutify

        if issubclass(i_type, dict):
            if issubclass(i_type, FrozenDict):
                # add the iterable to the memo
                # assume all FrozenDicts are already immutified
                memo[i_id] = iterable
                return iterable
            else:
                new_iter = FrozenDict()
                dictset = dict.__setitem__

                # add the iterable to the memo
                memo[i_id] = new_iter

                for key in iterable:
                    value = iterable[key]
                    v_id = id(value)
                    v_type = type(value)

                    if v_id in memo:
                        # an immutified value already exists. use it
                        dictset(new_iter, key, memo[v_id])
                    elif v_type in submutables:
                        # this object is submutable. need to immutify it
                        dictset(new_iter, key, immutify(value, memo))
                    elif v_type in mutable_typemap:
                        # convert the object to its immutable type
                        dictset(new_iter, key, mutable_typemap[v_type](value))
                        memo[v_id] = new_iter[key]
                    else:
                        # the value is either fully immutable, or
                        # we cant tell. since descriptors need to
                        # be able to hold default values for fields
                        # which may be mutable, we need to allow this.
                        dictset(new_iter, key, value)
                        memo[v_id] = value
                return new_iter
        elif i_type in submutables:
            # the object is submutable. need to make
            # sure everything in it is made immutable

            # if the object is immutable, need to make it mutable to edit it
            if i_type in immutable_typemap:
                new_iter = immutable_typemap[i_type](iterable)
            else:
                new_iter = iterable

            for i in range(len(new_iter)):
                value = new_iter[i]
                v_id = id(value)
                v_type = type(value)

                if v_id in memo:
                    # an immutified value already exists. use it
                    new_iter.__setitem__(i, memo[v_id])
                elif v_type in submutables:
                    # this object is submutable. need to immutify it
                    new_iter.__setitem__(i, immutify(value, memo))
                elif v_type in mutable_typemap:
                    # convert the object to its immutable type
                    new_iter.__setitem__(i, mutable_typemap[v_type](value))
                    memo[v_id] = value
                else:
                    # the value is either fully immutable, or we cant tell.
                    # since descriptors need to be able to hold default values
                    # for fields which may be mutable, we need to allow this.
                    new_iter.__setitem__(i, value)
                    memo[v_id] = value

            # now that its modified, make it immutable
            if i_type in immutable_typemap:
                pass
            elif i_type in mutable_typemap:
                new_iter = mutable_typemap[i_type](new_iter)
            else:
                raise TypeError(("submutable py type '%s' is specified as " +
                                 "mutable and an immutable py type is not " +
                                 "given to convert it to") % i_type)

            return new_iter
        return iterable

    def immutify(self, iterable):
        '''
        Scans through 'iterable' and makes sure everything
        in it is an immutable object. If it isnt, the object
        is cast into its equivalent immutable version.
        If no equivalent immmutable version exists, a TypeError is raised.
        '''
        return self._immutify(iterable, {})

    def pop(self, key, default=None):
        raise TypeError('%s does not support item removal' % type(self))

    def popitem(self):
        raise TypeError('%s does not support item removal' % type(self))

    def setdefault(self, key, value):
        raise TypeError('%s does not support item assignment' % type(self))

    def update(self, k_v_pairs=None, **initdata):
        raise TypeError('%s does not support item assignment' % type(self))

# add the dict type to the mutable types with
# FrozenDict as its immutable counterpart
mutable_typemap[dict] = FrozenDict
