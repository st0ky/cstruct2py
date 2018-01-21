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
        _values = d["_values"]
        if isinstance(_values, OrderedDict):
            _values = _values.items()
        assert all(map(lambda x: x is None or isinstance(x, int) or isinstance(x, long), [k for k, v in _values]))

        val = _values[0][0]
        if val is None:
            val = 0
        new_keys = []
        for v, k in _values:
            if v is None:
                val += 1
                new_keys.append(val)
            else:
                val = v
                new_keys.append(val)

        _values = OrderedDict(zip(new_keys, [v for k, v in _values]))

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

    def __iter__(cls):
        return iter(map(cls, cls._values.keys()))

    def __contains__(cls, val):
        if isinstance(val, PyBase):
            val = val._val_property
        return val in cls._values or val in cls._values.values()

class BasePyEnum(object):
    def __init__(self, val=None, buf=None, index=0):
        super(BasePyEnum, self).__init__(buf, index)

        if val is not None:
            self._val_property = val
    
    def __str__(self):
        if self in type(self):
            return self._values[self._val_property]

        return str(self._val_property)
    
    def _to_repr(self):
        res = repr(self._val_property)
        data = PyBase._to_repr(self)
        if data:
            res = ", ".join([res, data])
        return res