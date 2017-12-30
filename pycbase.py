class PyBase(object):
    def __init__(self, buf=None, index=0):
        super(PyBase, self).__init__()

        if buf:
            assert len(buf) >= index + len(self), "buf length cannot be less than %d" % len(self)

        self._buf = buf
        self._index = index
    
    @property
    def _val_property(self):
        raise NotImplemented()

    @_val_property.setter
    def _val_property(self, val):
        raise NotImplemented()

    def flush(self):
        raise NotImplemented()

    def pack_into(self, buf, index=0):
        raise NotImplemented()

    def parse_all(self):
        raise NotImplemented()

    def __len__(self):
        return self.size

    @property
    def packed(self):
        buf = bytearray("\x00" * len(self))
        self.pack_into(buf, 0)
        return buf

    def __str__(self):
        return ""

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self._to_repr())

    def _to_repr(self):
        if self._buf:
            return repr(self._buf[self._index:self._index + self.size])

        return ""