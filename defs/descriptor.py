'''
docstring
'''

__all__ = ('Descriptor', 'submutables', 'mutable_typemap', 'immutable_typemap')

from types import BuiltinFunctionType, CodeType, FunctionType, MethodType

#used to determine if a type can contain mutable objects
submutables = set((tuple, list, dict, set))

#used to determine what pytype to convert a mutable python object into
mutable_typemap = {list:tuple, set:frozenset}

#used to determine what pytype to convert an immutable python object into
immutable_typemap = {tuple:list, frozenset:set}


class Descriptor(dict):    
    _initialized = False
    
    def __init__(self, initializer=(), **kwargs):
        '''Converts all dicts, sets, and lists contained in the
        immediate nesting layer of this Descriptor to to Descriptors,
        FrozenSets, and tuples respectively. Raises a TypeError if
        encountering any other object that is detected as mutable.

        Lists and sets will be traversed and their contents will be
        converted to their corresponding immutable versions. If a
        corrosponding immutable version doesn't exist, raises TypeError.
        '''
        #make sure the Descriptor hasnt already been built
        if self._initialized:
            return
        
        if isinstance(initializer, dict):
            if isinstance(initializer, Descriptor):
                #if the initializer is a Descriptor, assume it is immutified
                dict.update(self, initializer)
            elif initializer:
                dict.update(self, self.immutify(initializer))
        elif initializer:
            self._update_from_k_v_pairs(initializer)
            
        if kwargs:
            dict.update(self, self.immutify(kwargs))
            
        self._initialized = True


    def __delitem__(self, key):
        raise TypeError('%s does not support item deletion' % type(self))

    def __copy__(self):
        return self
    
    def __deepcopy__(self, memo=None):
        return self

    def __repr__(self):
        return "<Descriptor %s>" % dict.__repr__(self)

    def __setitem__(self, key, value):
        raise TypeError('%s does not support item assignment' % type(self))

    def _update_from_k_v_pairs(self, k_v_pairs):
        '''Used internally by the implementation to initialize a
        Descriptor with an initializer made of (key, value) tuples.
        Also used when making a modified copy of a Descriptor.'''

        k_v_pairs = list(k_v_pairs)
        
        for i in range(len(k_v_pairs)):
            #the values in k_v_pairs can contain mutable data, so
            #its contents need to be immutified to prevent that.
            pair = k_v_pairs[i]
            k_v_pairs[i] = (pair[0], self.immutify(pair[1]))
        
        #the k_v_pairs can contain mutable data, so its contents
        #need to be immutified to make sure none of it is mutable.
        dict.update(self, self.immutify(k_v_pairs))

    def clear(self):
        raise TypeError('%s does not support item clearing' % type(self))

    def copyremove(self, keys, can_miss=False):
        '''Returns a copy of this Descriptor instance with
        the keys specified in the 'keys' argument removed.
        If can_miss is True, attempts to delete missing keys will pass.
        If can_miss is False, attempts to delete missing keys raises a KeyError.
        Defaults to can_miss=False'''
        fdict_copy = Descriptor(self)
        _ddi = dict.__delitem__

        if can_miss:
            for key in keys:
                try:
                    _ddi(fdict_copy, key)
                except KeyError:
                    pass
        else:
            for key in keys:
                _ddi(fdict_copy, key)
                
        return fdict_copy

    def copyadd(self, k_v_pairs=(), **initdata):
        '''Returns an updated copy of this Descriptor using an iterable
        of supplied keyword argumentsand/or a positional argument
        iterable containing iterables in a (key,value) arrangement.
        
        The positional argument list is used to update the
        Descriptor before the keyword arguments are.'''

        newfdict = Descriptor(self)
        
        newfdict._update_from_k_v_pairs(k_v_pairs)
        dict.update(newfdict, newfdict.immutify(initdata))
        
        return newfdict

    def fromkeys(self, keys, value=None):
        '''Returns a new Descriptor with keys
        from 'keys' and values equal to value.'''
        newfdict = Descriptor()
        dictset  = dict.__setitem__
        
        for key in keys:
            dictset(newfdict, key, value)
        
        return newfdict

    def _immutify(self, iterable, memo):
        '''Scans through 'iterable' and makes sure everything in it
        is an immutable object. If it isnt, the object is turned into
        its equivalent immutable version. If no equivalent immmutable
        version exists for that type, a TypeError is raised instead.'''
        i_id = id(iterable)
        if i_id in memo:
            return memo[i_id]
        
        i_type  = type(iterable)
        immutify = self._immutify
        
        if issubclass(i_type, dict):
            if issubclass(i_type, Descriptor):
                #add the iterable to the memo
                memo[i_id] = iterable
                '''assume all Descriptors are already immutified'''
                return iterable
            else:
                new_iter = Descriptor()
                dictset = dict.__setitem__
                
                #add the iterable to the memo
                memo[i_id] = new_iter
                
                for key in iterable:
                    value  = iterable[key]
                    v_id   = id(value)
                    v_type = type(value)

                    if v_id in memo:
                        '''an immutified value already exists. use it'''
                        dictset(new_iter, key, memo[v_id])
                    elif v_type in submutables:
                        '''this object is submutable. need to immutify it'''
                        dictset(new_iter, key, immutify(value, memo))
                    elif v_type in mutable_typemap:
                        '''convert the object to its immutable type'''
                        dictset(new_iter, key, mutable_typemap[v_type](value))
                        memo[v_id] = new_iter[key]
                    else:
                        '''the value is either fully immutable, or we
                        cant tell. since descriptors need to be able
                        to hold default values for fields which may
                        be mutable, we need to allow this.'''
                        dictset(new_iter, key, value)
                        memo[v_id] = value
                        
        elif i_type in submutables:
            '''the object is submutable. need to make
            sure everything in it is made immutable'''
            
            #if the object is immutable, need to make it mutable to edit it
            if i_type in immutable_typemap:
                new_iter = immutable_typemap[i_type](iterable)
            else:
                new_iter = iterable

            for i in range(len(new_iter)):
                value  = new_iter[i]
                v_id   = id(value)
                v_type = type(value)

                if v_id in memo:
                    '''an immutified value already exists. use it'''
                    new_iter.__setitem__(i, memo[v_id])
                elif v_type in submutables:
                    '''this object is submutable. need to immutify it'''
                    new_iter.__setitem__(i, immutify(value, memo))
                elif v_type in mutable_typemap:
                    '''convert the object to its immutable type'''
                    new_iter.__setitem__(i, mutable_typemap[v_type](value))
                    memo[v_id] = value
                else:
                    '''the value is either fully immutable, or we cant tell.
                    since descriptors need to be able to hold default values
                    for fields which may be mutable, we need to allow this.'''
                    new_iter.__setitem__(i, value)
                    memo[v_id] = value

            #now that its modified, make it immutable
            new_iter = mutable_typemap[i_type](new_iter)

        return new_iter

    def immutify(self, iterable):
        '''Scans through 'iterable' and makes sure everything in it
        is an immutable object. If it isnt, the object is turned into
        its equivalent immutable version. If no equivalent immmutable
        version exists for that type, a TypeError is raised instead.'''
        return self._immutify(iterable, {})

    def pop(self, key, default):
        raise TypeError('%s does not support item removal' % type(self))

    def popitem(self):
        raise TypeError('%s does not support item removal' % type(self))
        
    def setdefault(self, key, value):
        raise TypeError('%s does not support item assignment' % type(self))

    def update(self, k_v_pairs=None, **initdata):
        raise TypeError('%s does not support item assignment' % type(self))

#add the dict type to the mutable types with
#Descriptor as its immutable counterpart
mutable_typemap[dict] = Descriptor
