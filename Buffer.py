from os import SEEK_SET, SEEK_CUR, SEEK_END

class Buffer():
    '''docstring'''
    
    def read(self, count):
        '''docstring'''
        raise NotImplementedError('read method must be overloaded.')
    
    def seek(self, count):
        '''docstring'''
        raise NotImplementedError('seek method must be overloaded.')

    def size(self):
        '''docstring'''
        return len(self)

    def tell(self):
        '''docstring'''
        return self._pos
            
    def read(self, count):
        '''docstring'''
        raise NotImplementedError('write method must be overloaded.')
    

class BytesBuffer(bytes, Buffer):
    '''Meant for reading from the supplied buffer. Attempts to seek
    outside the size of the buffer will raise assertion errors.'''
    
    def __new__(typ, buffer=[]):
        '''docstring'''
        self = bytes.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''docstring'''
        try:
            if self._pos + count < len(self):
                oldPos = self._pos
                self._pos += count
            else:
                oldPos = self._pos
                self._pos = len(self)
                
            return self[oldPos:self._pos]
        except TypeError:
            pass
        
        assert count is None
        
        oldPos = self._pos
        self._pos = len(self)
        return self[oldPos:self._pos]
    
    def seek(self, pos, whence = SEEK_SET):
        '''docstring'''
        assert type(pos) is int
        
        if whence == SEEK_SET:
            self[pos - 1]#check if seek is outside of range
            self._pos = pos
        elif whence == SEEK_CUR:
            self[self._pos + pos - 1]#check if seek is outside of range
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
    
    def write(self, string):
        '''docstring'''
        raise IOError("Cannot write to byte strings as they are immutable.")
    

class BytearrayBuffer(bytearray, Buffer):
    '''Meant for writing to the supplied buffer. Attempts to seek
    outside the size of the buffer will not raise assertion errors.'''
    
    def __new__(typ, buffer=[]):
        '''docstring'''
        self = bytearray.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''docstring'''
        try:
            if self._pos + count < len(self):
                oldPos = self._pos
                self._pos += count
            else:
                oldPos = self._pos
                self._pos = len(self)
                
            return self[oldPos:self._pos]
        except TypeError:
            pass
        
        assert count is None
        
        oldPos = self._pos
        self._pos = len(self)
        return bytes(self[oldPos:self._pos])

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
    
    def write(self, string):
        '''docstring'''
        string = memoryview(string).tobytes()
        strLen = len(string)
        if len(self) < strLen + self._pos:
            self.extend(b'\x00' * (strLen - len(self) + self._pos) )
        self[self._pos:self._pos + strLen] = string
        self._pos += strLen
