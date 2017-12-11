# from pycbase import *

class BasePyArray(PyBase):
    def __init__(self, buf=None, index=0):
        super(BasePyArray, self).__init__(buf, index)
        self._cache = {}
    
    def __getitem__(self, key):
        if type(key) is slice:
            start, stop, step = key.start, key.stop, key.step
            if step is None:
                step = 1
            if start is None:
                start = 0
            if stop is None:
                stop = self._count if not self._count is None else 0xffffffffffffffff 
            return [self[i] for i in xrange(start, stop, step)]

        assert type(key) in [int, long]
        if 0 > key or (self._count != None and key >= self._count):
            raise IndexError(key)

        if not key in self._cache:
            self._cache[key] = self._type(self._buf, self._index + len(self._type) * key)
        
        return self._cache[key].val

    def __setitem__(self, key, val):
        if type(key) is slice:
            start, stop, step = key.start, key.stop, key.step
            if step is None:
                step = 1
            if start is None:
                start = 0
            if stop is None:
                stop = self._count if not self._count is None else 0xffffffffffffffff 
            if issubclass(type(val), BasePyArray) or type(val) in [list, tuple, set]:
                for i, j in enumerate(xrange(start, stop, step)):
                    self[j] = val[i]
            else:
                for i in xrange(start, stop, step):
                    self[i] = val
            return

        assert type(key) in [int, long]
        if 0 > key or (self._count != None and key >= self._count):
            raise IndexError(key)

        if not key in self._cache:
            self._cache[key] = self._type(self._buf, self._index + len(self._type) * key)

        self._cache[key].val = val

    def __iter__(self):
        if self._count is None:
            i = 0
            while True:
                yield self[i]
                i += 1
        else:
            for i in xrange(self._count):
                yield self[i]

    @property
    def val(self):
        return self

    @val.setter
    def val(self, val):
        if issubclass(type(val), BasePyArray) or type(val) in [list, tuple, set]:
            for i, item in enumerate(val):
                self[j] = item
            return

        if (type(val) in [str, bytearray] and len(val) >= len(self)):
            tmp = type(self)(val)
            self.val = tmp
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
                _ = i


class MetaPyArray(type):
    def __init__(cls, name, bases, d):
        assert "_type" in d
        assert "_count" in d
        assert (d["_count"] is None or (type(d["_count"]) in [int, long] and d["_count"] >= 0))

        super(MetaPyArray, cls).__init__(name, (BasePyArray,) + bases, d)

        if cls._count:
            cls.size = len(cls._type) * cls._count
        else:
            cls.size = 0

    def __new__(cls, name, bases, d):
        return type.__new__(cls, name, (BasePyArray,) + bases, d)

    def __len__(cls):
        return cls.size


class iArr(object):
    __metaclass__ = MetaPyArray
    _type = py_uint64_t
    _count = 5

class iArrA(object):
    __metaclass__ = MetaPyArray
    _type = iArr
    _count = 5



class bArr(object):
    __metaclass__ = MetaPyArray
    _type = B
    _count = 5
