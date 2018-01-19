from .pycbase import PyBase
from collections import OrderedDict
from .basics import MetaPyBasic



class _EnumWrapper(int):
    def __repr__(self):
        if self in self._values:
            return "<%s.%s: %s>" % (type(self).__name__, self._values[self], hex(self))
        return hex(self)

    def __str__(self):
        return repr(self)

class MetaPyEnum(MetaPyBasic):
    def __init__(cls, cls_name, bases, d, conf):
        type.__init__(cls, cls_name, (BasePyEnum, d["base"],), d)
        del cls.base

        cls._val_wrapper = type(cls_name, (_EnumWrapper,), dict(_values=cls._values))
        for k, v in cls._values.items():
            setattr(cls, v, cls._val_wrapper(k))
        
    def __new__(cls, cls_name, bases, d, conf):
        assert "_values" in d
        _values = OrderedDict(d["_values"])
        assert all(map(lambda x: x is None or isinstance(x, int) or isinstance(x, long), _values.keys()))

        val = _values.items()[0][0]
        if val is None:
            val = 0
        new_keys = []
        for v, k in _values.items():
            if v is None:
                new_keys.append(val)
                val += 1
            else:
                val = v
                new_keys.append(val)
        _values = OrderedDict(zip(new_keys, _values.values()))

        min_val = min(_values.keys())
        max_val = max(_values.keys())
        int64_t = conf.basics["int64_t"]
        int32_t = conf.basics["int32_t"]
        assert min_val >= int64_t._min and max_val <= int64_t._max

        base = int64_t if min_val < int32_t._min or max_val > int32_t._max else int32_t

        d["base"] = base
        d["_values"] = _values

        return type.__new__(cls, cls_name, (BasePyEnum, base,), d)

    def __len__(cls):
        return cls.size

class BasePyEnum(object):
    def __init__(self, val=None, buf=None, index=0):
        super(BasePyEnum, self).__init__(buf, index)

        if val is not None:
            self._val_property = val
        
    
    def _to_repr(self):
        res = repr(self._val_property)
        data = PyBase._to_repr(self)
        if data:
            res = ", ".join([res, data])
        return res
