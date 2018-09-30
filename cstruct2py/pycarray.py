from pycbase import *
from pycstruct import *
from basics import *
from configuration import gcc_x86_64_le

class BasePyArray(PyBase):
    def __init__(self, buf=None, index=0, *args, **kwargs):
        super(BasePyArray, self).__init__(buf, index)
        if self._buf is not None and self._count is None:
            assert len(self._buf) % len(self._type) == 0, "buf len must be multiple of %d" % len(self._type)
        self._cache = {}

        if args:
            self._val_property = args
        if kwargs:
            self._val_property = kwargs

    @staticmethod
    def is_iterable(val):
        try:
            iter(val)
            return True 
        except Exception:
            return False

    def __getitem__(self, key):
        if type(key) is slice:
            start, stop, step = key.start, key.stop, key.step
            if step is None:
                step = 1
            if start is None:
                start = 0
            if stop is None:
                stop = self._count if not self._count is None else 0xffffffffffffffffffff

            res = []
            try:
                for i in xrange(start, stop, step):
                    res.append(self[i])
            except IndexError:
                if self._count is not None:
                    raise

            return res

        assert type(key) in [int, long]
        
        if self._count is None and not key in self._cache and (self._buf is None or self._index + len(self._type) * key >= len(self._buf)):
            raise IndexError(key)

        if 0 > key or (self._count != None and key >= self._count):
            raise IndexError(key)

        if not key in self._cache:
            if self._buf is not None:
                self._cache[key] = self._type(self._buf, self._index + len(self._type) * key)
            else:
                self._cache[key] = self._type()

            if self._count is None and len(self._type) * key > self.size:
                self.size = len(self._type) * key

        return self._cache[key]._val_property

    def __setitem__(self, key, val):
        if type(key) is slice:
            start, stop, step = key.start, key.stop, key.step
            if step is None:
                step = 1
            if start is None:
                start = 0
            if stop is None:
                stop = self._count if not self._count is None else 0xffffffffffffffffffff
            try:
                if BasePyArray.is_iterable(val):
                    for i, j in enumerate(xrange(start, stop, step)):
                        self[j] = val[i]
                else:
                    for i in xrange(start, stop, step):
                        self[i] = val
            except ValueError:
                if self._count is not None:
                    raise

            return

        if self._count is None and not key in self._cache and self._buf is not None and self._index + len(self._type) * key >= len(self._buf):
            raise IndexError(key)

        if 0 > key or (self._count != None and key >= self._count):
            raise IndexError(key)

        if not key in self._cache:
            if self._buf is not None:
                self._cache[key] = self._type(self._buf, self._index + len(self._type) * key)
            else:
                self._cache[key] = self._type()

            if self._count is None and len(self._type) * key > self.size:
                self.size = len(self._type) * key

        self._cache[key]._val_property = val

    def __iter__(self):
        if self._count is None and self._buf is None:
            return

        if self._count is None:
            i = 0
            while True:
                try:
                    yield self[i]
                except IndexError:
                    return
                i += 1
        else:
            for i in xrange(self._count):
                yield self[i]

    @property
    def _val_property(self):
        return self

    @_val_property.setter
    def _val_property(self, val):
        if isinstance(val, dict):
            for k, v in val.items():
                self[k] = v

            return

        if BasePyArray.is_iterable(val):
            for i, item in enumerate(val):
                self[i] = item
            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            tmp = type(self)(val)
            self._val_property = tmp
            return

        raise ValueError(val)

    def flush(self):
        for i, item in self._cache.items():
            item.flush()
        self._cache = {}

    def pack_into(self, buf, index=0):
        if self._buf:
            buf[index:index + len(self)] = self._buf[self._index:self._index + len(self)]
        for i, item in self._cache.items():
            item.pack_into(buf, item._index - self._index)

        return buf

    def parse_all(self):
        if not self._count is None:
            for i in self:
                pass

    def __str__(self):
        res = ", ".join(map(str, self))
        return "[%s]" % res

    def _to_repr(self):
        res = ", ".join(map(str, self))
        data = super(BasePyArray, self)._to_repr()
        if data:
            res = ", ".join([data, res])
        return res


class MetaPyArray(type):
    def __init__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        assert "_type" in d
        assert "_count" in d
        assert (d["_count"] is None or (type(d["_count"]) in [int, long] and d["_count"] >= 0))

        super(MetaPyArray, cls).__init__(cls_name, (BasePyArray,), d)

        cls._alignment = cls._type._alignment
        cls.size = len(cls._type) * cls._count if cls._count else 0

    def __new__(cls, cls_name, bases, d, conf=gcc_x86_64_le):
        return type.__new__(cls, cls_name, (BasePyArray,), d)

    def __len__(cls):
        return cls.size

    def show(cls):
        field_repr = cls._type.show().splitlines()
        type_data = "\n\t".join(field_repr)
        
        count_data = "" if cls._count is None else ", %s" % hex(cls._count)

        if cls.__name__ == "<unknown_array>":
            resp = "Array(%s%s)" % (type_data, count_data)
        else:
            resp = "Array(name=%s, typ=%s%s)" % (repr(cls.__name__), type_data,
                "" if cls._count is None else ", count=%s" % count_data)

        return resp

def Array(typ, count=None, name="<unknown_array>", conf=gcc_x86_64_le):
    return MetaPyArray(name, (), dict(_type=typ, _count=count), conf)



# class iArr(object):
#     __metaclass__ = MetaPyArray
#     _type = py_uint64_t
#     _count = 5

# class iArrA(object):
#     __metaclass__ = MetaPyArray
#     _type = iArr
#     _count = 5



# class bArr(object):
#     __metaclass__ = MetaPyArray
#     _type = B
#     _count = 5
