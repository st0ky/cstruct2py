import struct
from functools import partial
from basics import *
from pycbase import *

pad = lambda x, y: x + ((-x) % y)

class MetaPyStruct(type):
    def __init__(cls, cls_name, bases, d):
        super(MetaPyStruct, cls).__init__(cls_name, (BasePyStruct,) + bases, d)

    def __new__(cls, cls_name, bases, d):
        assert "_fields" in d
        assert type(d["_fields"]) in [list, tuple]

        off = 0
        _alignment = 1
        for (name, field_cls) in d["_fields"]:
            assert type(name) is str, name
            assert issubclass(field_cls, PyBase), field_cls

            if field_cls._alignment > _alignment:
                _alignment = field_cls._alignment

            off = pad(off, field_cls._alignment)

            d[name] = property(
                partial(BasePyStruct._get_field, name=name, cls=field_cls, off=off),
                partial(BasePyStruct._set_field, name=name, cls=field_cls, off=off)
                )
            off += len(field_cls)

        d["size"] = pad(off, _alignment)
        d["_alignment"] = _alignment
        d["_fields"] = [name for (name, field_cls) in d["_fields"]]

        return type.__new__(cls, cls_name, (BasePyStruct,) + bases, d)

    def __len__(cls):
        return cls.size

class BasePyStruct(PyBase):
    def __init__(self, buf=None, index=0):
        super(BasePyStruct, self).__init__(buf, index)

        self._cache = {}

    def _set_field(self, val, name, cls, off):
        if not name in self._fields:
            raise KeyError(name)

        if not name in self._cache:
            self._cache[name] = cls(self._buf, self._index + off)

        self._cache[name]._val_property = val

    def _get_field(self, name, cls, off):
        if not name in self._fields:
            raise KeyError(name)

        if not name in self._cache:
            self._cache[name] = cls(self._buf, self._index + off)

        return self._cache[name]._val_property

    @property
    def _val_property(self):
        return self

    @_val_property.setter
    def _val_property(self, val):
        if type(val) is type(self):
            for field in self._fields:
                setattr(self, field, getattr(val, field))
            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            tmp = type(self)(val)
            self._val_property = tmp
            return

        raise ValueError(val)

    def flush(self):
        if self._buf:
            for field in self._cache.values():
                field.flush()

        self._cache = {}

    def pack_into(self, buf, index=0):
        if self._buf:
            buf[index:index + len(self)] = self._buf[self._index:self._index + len(self)]
        for field in self._cache.values():
            field.pack_into(buf, field._index - self._index)

        return buf

    def parse_all(self):
        for field in self._fields:
            getattr(self, field)
        return self

    def __str__(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        return "dict(%s)" % res

    def _to_repr(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        data = super(BasePyStruct, self)._to_repr()
        if data:
            res = ", ".join([data, res])
        return res




# class A(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("x", py_uint64_t), ("y", py_uint64_t)]

# class B(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("a", A), ("b", A)]
