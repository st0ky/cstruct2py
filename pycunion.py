from pycbase import *
from pycstruct import *
from basics import *

class BasePyUnion(PyBase):
    def __init__(self, buf=None, index=0):
        super(BasePyUnion, self).__init__(buf, index)
        self._cache = bytearray("\x00" * len(self))
        if self._buf:
            self._cache[0:len(self)] = self._buf[self._index:self._index + len(self)]
        self._last = type("\x01", (object,), {})()
        self._last.name = None
        self._last.value = None

    def _flush_to_cache(self):
        if self._last.name:
            self._last.value.pack_into(self._cache, 0)
            self._last.name = None

    def _set_field(self, val, name, cls):
        if not name in self._fields:
            raise KeyError(name)

        if self._last.name == name:
            self._last.value.val = val
            return
        
        self._flush_to_cache()
        self._last.name = name
        self._last.value = cls(self._cache, 0)
        self._last.value.val = val

    def _get_field(self, name, cls):
        if not name in self._fields:
            raise KeyError(name)

        if self._last.name == name:
            return self._last.value.val

        self._flush_to_cache()
        self._last.name = name
        self._last.value = cls(self._cache, 0)

        return self._last.value.val

    @property
    def val(self):
        return self

    @val.setter
    def val(self, val):
        if type(val) is type(self):
            val._flush_to_cache()
            self._last.name = None
            self._cache[0:] = val._cache
            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            tmp = type(self)(val)
            self.val = tmp
            return

        raise ValueError(val)

    def flush(self):
        self._flush_to_cache()
        if self._buf:
            self.pack_into(self._buf, self._index)

    def pack_into(self, buf, index=0):
        self._flush_to_cache()
        buf[index:index + len(self)] = self._cache

    def parse_all(self):
        pass

    def __str__(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        return "dict(%s)" % res

    def _to_repr(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        data = super(BasePyUnion, self)._to_repr()
        if data:
            res = ", ".join([data, res])
        return res
    

class MetaPyUnion(type):
    def __init__(cls, cls_name, bases, d):
        super(MetaPyUnion, cls).__init__(cls_name, (BasePyUnion,) + bases, d)

    def __new__(cls, cls_name, bases, d):
        assert "_fields" in d
        assert type(d["_fields"]) in [list, tuple, dict]
        if type(d["_fields"]) is dict:
            d["_fields"] = d["_fields"].items()

        size = 0
        for (name, field_cls) in d["_fields"]:
            assert type(name) is str, name
            assert issubclass(field_cls, PyBase), field_cls
            d[name] = property(
                partial(BasePyUnion._get_field, name=name, cls=field_cls),
                partial(BasePyUnion._set_field, name=name, cls=field_cls)
                )
            size = max(size, len(field_cls))

        d["size"] = size
        d["_fields"] = [name for (name, field_cls) in d["_fields"]]

        return type.__new__(cls, cls_name, (BasePyUnion,) + bases, d)

    def __len__(cls):
        return cls.size

# class A(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("x", py_uint32_t), ("y", py_uint32_t)]

# B = MetaPyUnion("B", (), {"_fields" : {"a" : py_uint32_t, "b" : py_uint64_t, "c" : A}})
