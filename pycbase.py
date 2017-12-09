class PyBase(object):
	def __init__(self, buf=None, index=0):
        super(PyBase, self).__init__()

        if buf:
            assert len(buf) >= index + len(self), "buf length cannot be less than %d" % len(self)

        self._buf = buf
        self._index = index
	
	@property
    def val(self):
        raise NotImplemented()

    @val.setter
    def val(self, val):
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
        return self.pack_into(buf, 0)