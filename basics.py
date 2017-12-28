from pycbase import *
import struct

class MetaPyBasic(type):
    "Basic value (just int ot char, etc.) no array or struct"
    def __init__(cls, cls_name, bases, d):
        super(MetaPyBasic, cls).__init__(cls_name, (BasePyBasic,) + bases, d)
        
        assert "_pattern" in d
        cls._struct = struct.Struct(cls._pattern)
        cls.size = cls._struct.size
    
    def __new__(cls, cls_name, bases, d):
        return type.__new__(cls, cls_name, (BasePyBasic,) + bases, d)

    def __len__(cls):
        return cls.size

class BasePyBasic(PyBase):
    def __init__(self, buf=None, index=0):

        if type(buf) in [int, long]:
            super(BasePyBasic, self).__init__(None, 0)
            self._cache = buf
            return

        super(BasePyBasic, self).__init__(buf, index)
        self._cache = None

    def flush(self):
        if not self._cache is None and self._buf:
            self._struct.pack_into(self._buf, self._index, self.val)

        self._cache = None

    def pack_into(self, buf, index=0):
        self._struct.pack_into(buf, index, self.val)

        return buf

    def parse_all(self):
        return self.val
    
    @property
    def val(self):
        if self._cache is None:
            if self._buf:
                self._cache = self._struct.unpack_from(self._buf, self._index)[0]
            else:
                self._cache = 0
        
        return self._cache

    @val.setter
    def val(self, val):
        if type(val) in [int, long]:
            self._cache = val
            return
        
        if type(val) is type(self):
            self._cache = val._cache
            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            self._cache = self._struct.unpack_from(val, 0)[0]
            return

        raise ValueError(val)


class py_uint64_t:
    __metaclass__ = MetaPyBasic
    _pattern = "Q"        

class py_uint32_t:
    __metaclass__ = MetaPyBasic
    _pattern = "I"        

class py_uint16_t:
    __metaclass__ = MetaPyBasic
    _pattern = "H"        

class py_uint8_t:
    __metaclass__ = MetaPyBasic
    _pattern = "B"

class py_int64_t:
    __metaclass__ = MetaPyBasic
    _pattern = "q"        

class py_int32_t:
    __metaclass__ = MetaPyBasic
    _pattern = "i"        

class py_int16_t:
    __metaclass__ = MetaPyBasic
    _pattern = "h"        

class py_int8_t:
    __metaclass__ = MetaPyBasic
    _pattern = "b"        
