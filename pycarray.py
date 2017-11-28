# from pycstruct import BasePyStruct

class BasePyArray(BasePyStruct):
    def __init__(self, buf=None, index=0):
        super(BasePyArray, self).__init__(buf, index)
        self._cached = {}

    def __getattr__(self, name):
        print "1 __getattr__ %s" % name
        return self.__dict__[name]

    def __setattr__(self, name, val):
        print "1 __setattr__ %s" % name
        self.__dict__[name] = val
    
    def __getitem__(self, key):
        assert type(key) in [int, long] and 0 <= key and (self._count == None or key < self._count)

        if key in self._cached:
            return self._cached[key]
        else:
            self._cached[key] = self._type(self._buf, self._index + len(self._type) * key)
            return self._cached[key]

    def __setitem__(self, key, val):
        assert type(key) in [int, long] and 0 <= key and (self._count == None or key < self._count)

        self._cached[key] = self._type.copy(val)

class MetaPyArray(type):
    def __init__(cls, name, bases, d):
        assert "_type" in d and "_count" in d and (d["_count"] is None or (type(d["_count"]) in [int, long] and d["_count"] >= 0))


        super(MetaPyArray, cls).__init__(name, (BasePyArray,) + bases, d)

        if cls._count:
            cls.size = len(cls._type) * cls._count
        else:
            cls.size = 0

    def __new__(cls, name, bases, d):
        return type.__new__(cls, name, (BasePyArray,) + bases, d)

    def pack(cls, buf, index, inst):
        for ind, val in inst._cached.items():
            cls._type.pack(buf, index + ind * len(cls._type), val)
        return buf

    def unpack(cls, buf, index):
        return cls(buf, index)

    def __len__(cls):
        return cls.size

    def copy(cls, val):
        if type(val) is cls:
            ret = cls(val._buf, val._index)
            for i, v in cls._cached.items():
                ret[i] = v
            return ret
        
        if type(val) in [str, bytearray] and len(val) >= cls.size:
            return cls(val)
        
        raise ValueError


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
