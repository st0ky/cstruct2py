import struct

class MetaPyBasic(type):
    "Basic value (just int ot char, etc.) no array or struct"
    def __init__(cls, name, bases, d):
        super(MetaPyBasic, cls).__init__(name, bases, d)
        
        assert "_pattern" in d
        cls._struct = struct.Struct(cls._pattern)
        cls.size = cls._struct.size
        print d
                

    def __len__(cls):
        return cls.size

    def unpack(cls, buf, index):
        return cls(buf, index)

    def __call__(cls, buf=0, index=0, val=None):
        if type(buf) in [float, int, long]:
            return buf

        if buf == None:
            return 0

        if val == None:
            return cls._struct.unpack_from(buf, index)[0]
        else:
            cls._struct.pack_into(buf, index, val)
            return buf

    def pack(cls, buf, index, val):
        return cls(buf, index, val)

    def copy(cls, val):
        if type(val) in [int, long] or (type(val) in [str, bytearray] and len(val) >= cls.size):
            return cls(val)
        raise ValueError

class py_uint64_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "Q"        

class py_uint32_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "I"        

class py_uint16_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "H"        

class py_uint8_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "B"

class py_int64_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "q"        

class py_int32_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "i"        

class py_int16_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "h"        

class py_int8_t(object):
    __metaclass__ = MetaPyBasic
    _pattern = "b"        
