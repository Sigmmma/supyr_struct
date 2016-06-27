'''
A module that implements several buffers which behave similarly to
file and mmap.mmap objects. Buffer objects implement read, seek, size,
tell, peek, and write methods for getting/modifying their contents.
'''
from os import SEEK_SET, SEEK_CUR, SEEK_END
from mmap import mmap


class Buffer():
    '''
    The base class for all Buffer objects.

    Buffers are simply a wrapper around another object which gives it an
    interface that mimics the read, seek, size, tell and write methods
    found in mmaps and files.
    Buffers also implement a peek function for reading the next
    X number of bytes without changing the read/write position.
    '''
    __slots__ = ()

    def read(self, count=None):
        raise NotImplementedError('read method must be overloaded.')

    def seek(self, pos, whence=SEEK_SET):
        raise NotImplementedError('seek method must be overloaded.')

    def size(self):
        return len(self)

    def tell(self):
        '''Returns the current position of the read/write pointer.'''
        return self._pos

    def peek(self, count=None):
        '''
        Reads and returns 'count' number of bytes from the Buffer
        without changing the current read/write pointer position.
        '''
        self._pos, data = self._pos, self.read(count)
        return data

    def write(self, s):
        raise NotImplementedError('write method must be overloaded.')


class BytesBuffer(bytes, Buffer):
    '''
    An extension of the bytes class which implements read, seek,
    size, tell, peek, and write methods. Since bytes objects
    are immutable, the write method will raise an IOError.

    Attempts to seek outside the buffer will raise Assertion errors.

    Uses os.SEEK_SET, os.SEEK_CUR, and os.SEEK_END when calling seek.
    '''
    def __new__(typ, buffer=b'', *args, **kwargs):
        '''Creates a new BytesBuffer object.'''
        self = bytes.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''Reads and returns 'count' number of bytes as a bytes object.'''
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

    def seek(self, pos, whence=SEEK_SET):
        '''
        Changes the position of the read pointer based on 'pos' and 'whence'.

        If whence is os.SEEK_SET, the read pointer is set to pos
        If whence is os.SEEK_CUR, the read pointer has pos added to it
        If whence is os.SEEK_END, the read pointer is set to len(self) + pos

        Raises AssertionError if pos is not an int
        Raises AssertionError if the read pointer would end up negative.
        Raises ValueError if whence is not SEEK_SET, SEEK_CUR, or SEEK_END.
        Raises TypeError if whence is not an int.
        '''
        assert type(pos) is int

        if whence == SEEK_SET:
            self[pos - 1]  # check if seek is outside of range
            assert pos >= 0, "Read position cannot be negative."
            self._pos = pos
        elif whence == SEEK_CUR:
            self[self._pos + pos - 1]  # check if seek is outside of range
            assert self._pos + pos >= 0, "Read position cannot be negative."
            self._pos += pos
        elif whence == SEEK_END:
            pos += len(self)
            self[pos - 1]  # check if seek is outside of range
            assert pos >= 0, "Read position cannot be negative."
            self._pos = pos
        elif type(whence) is int:
            raise ValueError("Invalid value for whence. Expected " +
                             "0, 1, or 2, got %s." % whence)
        else:
            raise TypeError("Invalid type for whence. Expected " +
                            "%s, got %s" % (int, type(whence)))

    def write(self, s):
        '''Raises an IOError because bytes objects are immutable.'''
        raise IOError("Cannot write to byte strings as they are immutable.")


class BytearrayBuffer(bytearray, Buffer):
    '''
    An extension of the bytearray class which implements
    read, seek, size, tell, peek, and write methods.

    Uses os.SEEK_SET, os.SEEK_CUR, and os.SEEK_END when calling seek.
    '''
    __slots__ = ('_pos')

    def __new__(typ, buffer=b'', *args, **kwargs):
        '''Creates a new BytearrayBuffer object.'''
        self = bytearray.__new__(typ, buffer)
        self._pos = 0
        return self

    def read(self, count=None):
        '''Reads and returns 'count' number of bytes as a bytes object.'''
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

    def seek(self, pos, whence=SEEK_SET):
        '''
        Changes the position of the read pointer based on 'pos' and 'whence'.

        If whence is os.SEEK_SET, the read pointer is set to pos
        If whence is os.SEEK_CUR, the read pointer has pos added to it
        If whence is os.SEEK_END, the read pointer is set to len(self) + pos

        Raises AssertionError if pos is not an int
        Raises ValueError if whence is not SEEK_SET, SEEK_CUR, or SEEK_END.
        Raises TypeError if whence is not an int.
        '''
        assert type(pos) is int

        if whence == SEEK_SET:
            self._pos = pos
        elif whence == SEEK_CUR:
            self._pos += pos
        elif whence == SEEK_END:
            self._pos = pos + len(self)
        elif type(whence) is int:
            raise ValueError("Invalid value for whence. Expected " +
                             "0, 1, or 2, got %s." % whence)
        else:
            raise TypeError("Invalid type for whence. Expected " +
                            "%s, got %s" % (int, type(whence)))

    def write(self, s):
        '''
        Uses memoryview().tobytes() to convert the supplied
        object into bytes and writes those bytes to this object
        at the current location of the read/write pointer.
        Attempting to write outside the buffer will force
        the buffer to be extended to fit the written data.

        Updates the read/write pointer by the length of the bytes.
        '''
        s = memoryview(s).tobytes()
        str_len = len(s)
        if len(self) < str_len + self._pos:
            self.extend(b'\x00' * (str_len - len(self) + self._pos))
        self[self._pos:self._pos + str_len] = s
        self._pos += str_len


class PeekableMmap(mmap):
    '''An extension of the bytearray class which implements a peek method.'''
    __slots__ = ('_pos')

    def peek(self, count=None):
        '''
        Reads and returns 'count' number of bytes from the PeekableMmap
        without changing the current read/write pointer position.
        '''
        orig_pos = self.tell()
        try:
            data = self.read(count)
        except Exception:
            self.seek(orig_pos)
            raise
        finally:
            self.seek(orig_pos)
        return data
