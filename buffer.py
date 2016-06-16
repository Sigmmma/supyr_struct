from os import SEEK_SET, SEEK_CUR, SEEK_END
from mmap import mmap

class Buffer():
    '''docstring'''
    __slots__ = ()
    
    def read(self, count=None):
        '''docstring'''
        raise NotImplementedError('read method must be overloaded.')
    
    def seek(self, pos, whence=SEEK_SET):
        '''docstring'''
        raise NotImplementedError('seek method must be overloaded.')

    def size(self):
        '''docstring'''
        return len(self)

    def tell(self):
        '''docstring'''
        return self._pos

    def peek(self, count=None):
        orig_pos, self._pos, data = self._pos, self._pos, self.read(count)
        return data
        
    def write(self, s):
        '''docstring'''
        raise NotImplementedError('write method must be overloaded.')


class BytesBuffer(bytes, Buffer):
    '''Meant for reading from the supplied buffer. Attempts to seek
    outside the size of the buffer will raise assertion errors.'''
    
    def __new__(typ, buffer=b'', *args, **kwargs):
        '''docstring'''
        self = bytes.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''docstring'''
        try:
            if self._pos + count < len(self):
                old_pos = self._pos
                self._pos += count
            else:
                old_pos = self._pos
                self._pos = len(self)
                
            return self[old_pos:self._pos]
        except TypeError:
            pass
        
        assert count is None
        
        old_pos = self._pos
        self._pos = len(self)
        return self[old_pos:self._pos]
    
    def seek(self, pos, whence = SEEK_SET):
        '''docstring'''
        assert type(pos) is int
        
        if whence == SEEK_SET:
            self[pos - 1]#check if seek is outside of range
            assert pos >= 0, ("Read position cannot be negative.")
            self._pos = pos
        elif whence == SEEK_CUR:
            self[self._pos + pos - 1]#check if seek is outside of range
            assert pos >= 0, ("Read position cannot be negative.")
            self._pos += pos
        elif whence == SEEK_END:
            pos += len(self)
            self[pos - 1]#check if seek is outside of range
            assert pos >= 0, ("Read position cannot be negative.")
            self._pos = pos
        elif type(whence) is int:
            raise ValueError("Invalid value for whence. Expected "+
                             "0, 1, or 2, got %s." % whence)
        else:
            raise TypeError("Invalid type for whence. Expected "+
                            "%s, got %s" % (int, type(whence)))
    
    def write(self, s):
        '''docstring'''
        raise IOError("Cannot write to byte strings as they are immutable.")
    

class BytearrayBuffer(bytearray, Buffer):
    '''Meant for writing to the supplied buffer.'''
    __slots__ = ('_pos')
    
    def __new__(typ, buffer=b'', *args, **kwargs):
        '''docstring'''
        self = bytearray.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''docstring'''
        try:
            if self._pos + count < len(self):
                old_pos = self._pos
                self._pos += count
            else:
                old_pos = self._pos
                self._pos = len(self)
                
            return self[old_pos:self._pos]
        except TypeError:
            pass
        
        assert count is None
        
        old_pos = self._pos
        self._pos = len(self)
        return bytes(self[old_pos:self._pos])

    def seek(self, pos, whence = SEEK_SET):
        '''docstring'''
        assert type(pos) is int
        
        if whence == SEEK_SET:
            self._pos = pos
        elif whence == SEEK_CUR:
            self._pos += pos
        elif whence == SEEK_END:
            self._pos = pos + len(self)
        elif type(whence) is int:
            raise ValueError("Invalid value for whence. Expected "+
                             "0, 1, or 2, got %s." % whence)
        else:
            raise TypeError("Invalid type for whence. Expected "+
                            "%s, got %s" % (int, type(whence)))
    
    def write(self, s):
        '''docstring'''
        s = memoryview(s).tobytes()
        str_len = len(s)
        if len(self) < str_len + self._pos:
            self.extend(b'\x00' * (str_len - len(self) + self._pos) )
        self[self._pos:self._pos + str_len] = s
        self._pos += str_len


class PeekableMmap(mmap):
    __slots__ = ('_pos')
    
    def peek(self, count=None):
        orig_pos = self.tell()
        try:
            data = self.read(count)
        except Exception:
            self.seek(orig_pos)
            raise
        finally:
            self.seek(orig_pos)
        return data
