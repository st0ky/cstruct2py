# from pycstruct import BasePyStruct

class BasePyUnion(BasePyStruct):
    def __init__(self, buf=None, index=0):
        super(BasePyUnion, self).__init__(buf, index)
        self._cache = bytearray("\x00" * len(self))
        if self._buf:
            self._cache[0:len(self)] = self._buf[self._index:self._index + len(self)]
        self._last = type("\x01", (object,), {})()
        self._last.name = None

    def _flush_to_cache(self):
        if self._last.name:
            self._fields[self._last.name].pack(self._cache, 0, self._last.value)
            self._last.name = None

    def __getattr__(self, name):
        print "[%d] __getattr__ %s" % (id(self), name)
        if name not in self._fields:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__, name))

        if self._last.name == name:
            return self._last.value

        self._flush_to_cache()

        self._last.name = name
        self._last.value = self._fields[name](self._cache)

        return self._last.value

    def __setattr__(self, name, val):
        print "[%d] __getattr__ %s" % (id(self), name)
        if name in ["_cache", "_last", "_buf", "_index"]:
            self.__dict__[name] = val
            return

        if name not in self._fields:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__, name))

        if self._last.name == name:
            self._last.value = self._fields[name].copy(val)
            return

        self._flush_to_cache()

        self._last.name = name
        self._last.value = self._fields[name].copy(val)

        return self._last.value

class MetaPyUnion(type):
    def __init__(cls, name, bases, d):
        super(MetaPyUnion, cls).__init__(name, (BasePyUnion,) + bases, d)

        cls.size = max(v.size for v in cls._fields.values())
        cls.__members__ = cls._fields.keys()
        cls.__methods__ = []

    def __new__(cls, name, bases, d):
        print type(d["_fields"]), d["_fields"]
        assert "_fields" in d and type(d["_fields"]) in [dict, list]
        if type(d["_fields"]) is list:
            d["_fields"] = dict(d["_fields"])
        return type.__new__(cls, name, (BasePyUnion,) + bases, d)

    def pack(cls, buf, index, inst):
        inst._flush_to_cache()
        buf[index:index + cls.size] = inst._cache
        return buf

    def unpack(cls, buf, index):
        return cls(buf, index)

    def __len__(cls):
        return cls.size

    def copy(cls, val):
        if type(val) is cls:
            ret = cls(val._buf, val._index)
            val._flush_to_cache()
            ret._cache = val._cache[:]
            return ret
        
        if type(val) in [str, bytearray] and len(val) >= cls.size:
            return cls(val)
        
        raise ValueError

class A(object):
    __metaclass__ = MetaPyStruct
    _fields = [("x", py_uint32_t), ("y", py_uint32_t)]

B = MetaPyUnion("B", (), {"_fields" : {"a" : py_uint32_t, "b" : py_uint64_t, "c" : A}})
