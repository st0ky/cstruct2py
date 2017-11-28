import struct
from collections import OrderedDict
# from basics import *

class MetaPyStruct(type):
    def __init__(cls, name, bases, d):
        # assert "BasePyStruct" in bases
        assert "_fields" in d and isinstance(d["_fields"], OrderedDict)

        super(MetaPyStruct, cls).__init__(name, (BasePyStruct,) + bases, d)

        cls.size = sum(map(len, cls._fields.values()))
        cls.__members__ = cls._fields.keys()
        cls.__methods__ = []

    def __new__(cls, name, bases, d):
        return type.__new__(cls, name, (BasePyStruct,) + bases, d)

    def pack(cls, buf, index, inst):
        offset = 0
        for var, var_cls in inst._fields.items():
            if var in inst.__dict__:
                var = getattr(inst, var)
                var_cls.pack(buf, index + offset, var)
            elif inst._buf:
                buf[index + offset : index + offset + len(var_cls)] = inst._buf[inst._index + offset : inst._index + offset + len(var_cls)]
            
            offset += len(var_cls)
        return buf

    def unpack(cls, buf, index):
        return cls(buf, index)

    def __len__(cls):
        return cls.size

    def copy(cls, val):
        if type(val) is cls:
            ret = cls(val._buf, val._index)
            for name in cls._fields.keys():
                if name in val.__dict__:
                    setattr(ret, name, getattr(val, name))
            return ret
        if (type(val) in [str, bytearray] and len(val) >= cls.size):
            return cls(val)

        raise ValueError

class BasePyStruct(object):
    def __init__(self, buf=None, index=0):
        super(BasePyStruct, self).__init__()

        if buf:
            assert len(buf) >= index + len(self), "buf length cannot be less than %d" % len(self)

        self._buf = buf
        self._index = index

    def __getattr__(self, name):
        print "[%d] __getattr__ %s" % (id(self), name)
        if name not in self._fields:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__, name))

        field_offset = sum(map(len, self._fields.values()[:self._fields.keys().index(name)]))
        super(BasePyStruct, self).__setattr__(name, self._fields[name](self._buf, self._index + field_offset))

        return getattr(self, name)

    def __setattr__(self, name, val):
        print "[%d] __setattr__ %s" % (id(self), name)
        
        if name in ["_buf", "_index", "_dirty"]:
            return super(BasePyStruct, self).__setattr__(name, val)

        assert name in self._fields, "%s not in self._fields" % name
        
        val = self._fields[name].copy(val)

        return super(BasePyStruct, self).__setattr__(name, val)

    def __len__(self):
        return type(self).size

    @property
    def size(self):
        return len(self)

    @property
    def packed(self):
        if self._buf:
            buf = self._buf
        else:
            buf = bytearray("\x00" * len(self))

        return type(self).pack(buf, self._index, self)


class A(object):
    __metaclass__ = MetaPyStruct
    _fields = OrderedDict([("x", py_uint64_t), ("y", py_uint64_t)])

class B(object):
    __metaclass__ = MetaPyStruct
    _fields = OrderedDict([("a", A), ("b", A)])

        
sizeof = len

# def make_struct(name, fields):
#     assert type(fields) is dict
#     globals()[name] = type(name, (BasePyStruct,), {"_fields" : fields})
