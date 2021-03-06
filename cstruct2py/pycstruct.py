from functools import partial
from basics import *
from pycbase import *
from configuration import gcc_x86_64_le

pad = lambda x, y: x + ((-x) % y)

class MetaPyStruct(type):
    def __init__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        super(MetaPyStruct, cls).__init__(cls_name, (BasePyStruct,), d)
        if not hasattr(cls, "incomplete type"):
            cls.assign_fields(cls._fields, conf.alignment)

    def __new__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        assert "_fields" in d
        if d["_fields"] is None:
            d["incomplete type"] = True

        return type.__new__(cls, cls_name, (BasePyStruct,), d)

    def assign_fields(cls, fields, alignment=None):
        assert type(fields) in [list, tuple, dict]
        if type(fields) is dict:
            fields = fields.items()

        off = 0
        _alignment = 1 if alignment is None else alignment
        unnamed_count = 0
        names = []
        for (name, field_cls) in fields:
            assert issubclass(field_cls, PyBase), field_cls
            
            if alignment is None:
                _alignment = max(field_cls._alignment, _alignment)

            off = pad(off, field_cls._alignment if alignment is None else alignment)
            
            if name is None:
                unnamed = "unnamed %d" % unnamed_count
                unnamed_count += 1
                for field in field_cls._fields:
                    names.append(field)
                    setattr(cls, field, property(
                        partial(BasePyStruct._get_field, name=field, cls=field_cls, off=off, unnamed=unnamed),
                        partial(BasePyStruct._set_field, name=field, cls=field_cls, off=off, unnamed=unnamed)
                        ))
            else:
                assert type(name) is str, name

                names.append(name)
                setattr(cls, name, property(
                    partial(BasePyStruct._get_field, name=name, cls=field_cls, off=off),
                    partial(BasePyStruct._set_field, name=name, cls=field_cls, off=off)
                    ))
            
            off += len(field_cls)

        setattr(cls, " size", pad(off, _alignment))
        cls._alignment = _alignment
        cls._fields = names

        if hasattr(cls, "incomplete type"):
            delattr(cls, "incomplete type")

    def __len__(cls):
        return getattr(cls, " size")

    def show(cls):
        resp = "Struct(name=%s, fields=[\n" % repr(cls.__name__)
        for field in cls._fields:
            field_repr = getattr(cls, field).fget.keywords["cls"].show().splitlines()
            resp += "\t(%s, %s" % (repr(field), field_repr[0])
            for line in field_repr[1:]:
                resp += "\n\t"
                resp += line
            resp += "),\n"
        resp += "\t])"

        return resp

class BasePyStruct(PyBase):
    def __init__(self, buf=None, index=0, **kwargs):
        super(BasePyStruct, self).__init__(buf, index)

        self._cache = {}

        if kwargs:
            self._val_property = kwargs

    def _set_field(self, val, name, cls, off, unnamed=None):
        real_name = name if unnamed is None else unnamed
        
        if not name in self._fields:
            raise KeyError(name)

        if not real_name in self._cache:
            self._cache[real_name] = cls(self._buf, self._index + off)

        if unnamed is not None:
            return setattr(self._cache[real_name], name, val)

        self._cache[real_name]._val_property = val

    def _get_field(self, name, cls, off, unnamed=None):
        real_name = name if unnamed is None else unnamed
        
        if not name in self._fields:
            raise KeyError(name)

        if not real_name in self._cache:
            self._cache[real_name] = cls(self._buf, self._index + off)

        if unnamed is not None:
            return getattr(self._cache[real_name], name)

        return self._cache[real_name]._val_property

    @property
    def _val_property(self):
        return self

    @_val_property.setter
    def _val_property(self, val):
        if type(val) is type(self):
            for field in self._fields:
                setattr(self, field, getattr(val, field))
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
        if self._buf:
            for field in self._cache.values():
                field.flush()

        self._cache = {}

    def pack_into(self, buf, index=0):
        if self._buf:
            buf[index:index + len(self)] = self._buf[self._index:self._index + len(self)]
        for field in self._cache.values():
            field.pack_into(buf, index + field._index - self._index)

        return buf

    def parse_all(self):
        for field in self._fields:
            getattr(self, field)
        return self

    def __eq__(self, other):
        return isinstance(other, type(self)) and all(getattr(self, field) == getattr(other, field) for field in self._fields)

    def __str__(self):
        res = ", ".join("%s:%s" % (repr(field), getattr(self, field)) for field in self._fields)
        return "{%s}" % res

    def _to_repr(self):
        res = ", ".join("%s=%s" % (field, getattr(self, field)) for field in self._fields)
        data = super(BasePyStruct, self)._to_repr()
        if data:
            res = ", ".join([data, res])
        return res

def Struct(fields, name="<unknown_struct>", conf=gcc_x86_64_le):
    return MetaPyStruct(name, (), dict(_fields=fields), conf)



# class A(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("x", py_uint64_t), ("y", py_uint64_t)]

# class B(object):
#     __metaclass__ = MetaPyStruct
#     _fields = [("a", A), ("b", A)]
