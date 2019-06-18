from pycbase import *
from pycstruct import *
from basics import *
from configuration import gcc_x86_64_le


class BasePyUnion(PyBase):
    def __init__(self, buf=None, index=0, **kwargs):
        super(BasePyUnion, self).__init__(buf, index)
        
        self._cache = bytearray("\x00" * len(self))
        if self._buf:
            self._cache[0:len(self)] = self._buf[self._index:self._index + len(self)]
        
        self._last = type("\x01", (object,), {})()
        self._last.name = None
        self._last.value = None

        if kwargs:
            self._val_property = kwargs

    def _flush_to_cache(self):
        if self._last.name:
            self._last.value.pack_into(self._cache, 0)
            self._last.name = None

    def _set_field(self, val, name, cls, unnamed=None):
        if not name in self._fields:
            raise KeyError(name)

        real_name = name if unnamed is None else unnamed
        if self._last.name == real_name:
            if unnamed is not None:
                return setattr(self._last.value, name, val)
            self._last.value._val_property = val
            return
        
        self._flush_to_cache()
        self._last.name = real_name
        self._last.value = cls(self._cache, 0)
        if unnamed is not None:
            return setattr(self._last.value, name, val)
        self._last.value._val_property = val

    def _get_field(self, name, cls, unnamed=None):
        if not name in self._fields:
            raise KeyError(name)

        real_name = name if unnamed is None else unnamed
        if self._last.name == real_name:
            if unnamed is not None:
                return getattr(self._last.value, name)
            return self._last.value._val_property

        self._flush_to_cache()
        self._last.name = real_name
        self._last.value = cls(self._cache, 0)

        if unnamed is not None:
            return getattr(self._last.value, name)
        return self._last.value._val_property

    @property
    def _val_property(self):
        return self

    @_val_property.setter
    def _val_property(self, val):
        if type(val) is type(self):
            val._flush_to_cache()
            self._last.name = None
            self._cache[0:] = val._cache
            return

        
        if isinstance(val, dict):
            for k, v in val.items():
                setattr(self, k, v)

            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            tmp = type(self)(val)
            self._val_property = tmp
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
    
    def __eq__(self, other):
        return isinstance(other, type(self)) and all(getattr(self, field) == getattr(other, field) for field in self._fields)

    def __str__(self):
        res = ", ".join("%s:%s" % (repr(field), getattr(self, field)) for field in self._fields)
        return "{%s}" % res

    def _to_repr(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        data = super(BasePyUnion, self)._to_repr()
        if data:
            res = ", ".join([data, res])
        return res
    

class MetaPyUnion(type):
    def __init__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        super(MetaPyUnion, cls).__init__(cls_name, (BasePyUnion,), d)
        if not hasattr(cls, "incomplete type"):
            cls.assign_fields(cls._fields, conf.alignment)

    def __new__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        assert "_fields" in d
        if d["_fields"] is None:
            d["incomplete type"] = True

        return type.__new__(cls, cls_name, (BasePyUnion,), d)

    def assign_fields(cls, fields, alignment=None):
        assert type(fields) in [list, tuple, dict]
        if type(fields) is dict:
            fields = fields.items()

        size = 0
        _alignment = 1 if alignment is None else alignment
        
        unnamed_count = 0
        names = []
        for (name, field_cls) in fields:
            assert issubclass(field_cls, PyBase), field_cls
            
            if alignment is None:
                _alignment = max(field_cls._alignment, _alignment)

            if name is None:
                unnamed = "unnamed %d" % unnamed_count
                unnamed_count += 1
                for field in field_cls._fields:
                    names.append(field)
                    setattr(cls, field, property(
                        partial(BasePyStruct._get_field, name=field, cls=field_cls, unnamed=unnamed),
                        partial(BasePyStruct._set_field, name=field, cls=field_cls, unnamed=unnamed)
                        ))
            else:
                assert type(name) is str, name
                names.append(name)
                setattr(cls, name, property(
                    partial(BasePyUnion._get_field, name=name, cls=field_cls),
                    partial(BasePyUnion._set_field, name=name, cls=field_cls)
                    ))
            size = max(size, len(field_cls))

        setattr(cls, " size", size)
        cls._alignment = _alignment
        cls._fields = names

        if hasattr(cls, "incomplete type"):
            delattr(cls, "incomplete type")


    def __len__(cls):
        return getattr(cls, " size")


    def show(cls):
        if cls.__name__ == "<unknown_union>":
            resp = "Union([\n" % repr(cls.__name__)
        else:
            resp = "Union(name=%s, fields=[\n" % repr(cls.__name__)
            
        for field in cls._fields:
            field_repr = getattr(cls, field).fget.keywords["cls"].show().splitlines()
            resp += "\t(%s, %s" % (repr(field), field_repr[0])
            for line in field_repr[1:]:
                resp += "\n\t"
                resp += line
            resp += "),\n"
        resp += "\t])"

        return resp


def Union(fields, name="<unknown_union>", conf=gcc_x86_64_le):
    return MetaPyUnion(name, (), dict(_fields=fields), conf)

# class A(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("x", py_uint32_t), ("y", py_uint32_t)]

# B = MetaPyUnion("B", (), {"_fields" : {"a" : py_uint32_t, "b" : py_uint64_t, "c" : A}})
