from .basics import MetaPyBasic, _CharRapper


class Config(object):
    def __init__(self, byteorder, long_size, ptr_size):
        super(Config, self).__init__()

        big = ["big", "be", ">"]
        little = ["little", "le", "<"]
        assert byteorder in big + little

        assert long_size in [32, 64]
        assert ptr_size in [8, 16, 32, 64]

        self.byteorder = "<" if byteorder in little else ">"
        self.long_size = long_size
        self.ptr_size = ptr_size

        self.generate_types()
        

    def generate_types(self):
        names_to_pycstructs = {}
        for i, p in zip([8, 16, 32, 64], "BHIQ"):
            names_to_pycstructs['uint%d_t' % i] = MetaPyBasic("uint%d_t" % i, (),
                dict(_pattern=self.byteorder + p, _alignment=i/8, _max = (1 << i) - 1, _min=0))

        for i, p in zip([8, 16, 32, 64], "bhiq"):
            names_to_pycstructs['int%d_t' % i] = MetaPyBasic("int%d_t" % i, (),
                dict(_pattern=self.byteorder + p, _alignment=i/8, _max = (1 << (i - 1)) - 1, _min=-(1 << (i - 1))))

        for i, p in zip([32, 64], "fd"):
            names_to_pycstructs['float%d_t' % i] = MetaPyBasic("float%d_t" % i, (),
                dict(_pattern=self.byteorder + p, _alignment=i/8))

        names_to_pycstructs['char_t'] = MetaPyBasic("char_t", (),
                dict(_pattern=self.byteorder + "b", _alignment=1, _max = (1 << (8 - 1)) - 1, _min=-(1 << (8 - 1)),
                    _val_wrapper=_CharRapper))

        names_to_pycstructs['uchar_t'] = MetaPyBasic("uchar_t", (),
                dict(_pattern=self.byteorder + "B", _alignment=1, _max = (1 << 8) - 1, _min=0,
                    _val_wrapper=_CharRapper))

        for k, v in names_to_pycstructs.items():
            names_to_pycstructs[(k,)] = v

        long_val = names_to_pycstructs['int%d_t' % self.long_size]
        ulong_val = names_to_pycstructs['uint%d_t' % self.long_size]

        names_to_pycstructs[frozenset(('float', ))] = names_to_pycstructs['float32_t']
        names_to_pycstructs[frozenset(('double', ))] = names_to_pycstructs['float64_t']
        # names_to_pycstructs[frozenset(('long', 'double', ))] = float64_t

        names_to_pycstructs[frozenset(('long', 'long', ))] = names_to_pycstructs['int64_t']
        names_to_pycstructs[frozenset(('long', ))] = long_val
        names_to_pycstructs[frozenset(('int', ))] = names_to_pycstructs['int32_t']
        names_to_pycstructs[frozenset(('short', ))] = names_to_pycstructs['int16_t']
        names_to_pycstructs[frozenset(('byte', ))] = names_to_pycstructs['int8_t']
        names_to_pycstructs[frozenset(('char', ))] = names_to_pycstructs['char_t']
        names_to_pycstructs[frozenset(('unsigned', 'long', 'long', ))] = names_to_pycstructs['uint64_t']
        names_to_pycstructs[frozenset(('unsigned', 'long', ))] = ulong_val
        names_to_pycstructs[frozenset(('unsigned', 'int', ))] = names_to_pycstructs['uint32_t']
        names_to_pycstructs[frozenset(('unsigned', 'short', ))] = names_to_pycstructs['uint16_t']
        names_to_pycstructs[frozenset(('unsigned', 'byte', ))] = names_to_pycstructs['uint8_t']
        names_to_pycstructs[frozenset(('unsigned', 'char', ))] = names_to_pycstructs['uchar_t']

        names_to_pycstructs[frozenset(('void', '*', ))] = names_to_pycstructs['uint%d_t' % self.ptr_size]
        
        self.names_to_pycstructs = names_to_pycstructs

    def simplify_type(self, val):
        if type(val) in [str]:
            val = (val, )
        val = set(val)
        if val & {"short", "byte", "char", "long"}:
            val ^= val & {"int"}
        if val & {"short", "byte", "char", "int", "long"}:
            val ^= val & {"signed"}
        return frozenset(val)

    def has_type(self, val):
        return self.simplify_type(val) in self.names_to_pycstructs

    def get_type(self, val):
        return self.names_to_pycstructs[self.simplify_type(val)]

    @property
    def basics(self):
        return self.names_to_pycstructs

    def __getattr__(self, name):
        if name in ["names_to_pycstructs", "basics"] or name not in self.basics:
            return __getattribute__(self, name)

        return self.basics[name]

    def __setattr__(self, name, val):
        if hasattr(self, "names_to_pycstructs"):
            raise AttributeError("'%s' object attribute '%s' is read-only" % (type(self), name))

        return super(Config, self).__setattr__(name, val)


gcc_x86_64_le    = Config("le", 64, 64)
clang_x86_64_le  = Config("le", 64, 64)
vc_x86_64_le     = Config("le", 32, 64)
gcc_x86_le       = Config("le", 32, 32)
clang_x86_le     = Config("le", 32, 32)
vc_x86_le        = Config("le", 32, 32)

gcc_x86_64_be    = Config("be", 64, 64)
clang_x86_64_be  = Config("be", 64, 64)
vc_x86_64_be     = Config("be", 32, 64)
gcc_x86_be       = Config("be", 32, 32)
clang_x86_be     = Config("be", 32, 32)
vc_x86_be        = Config("be", 32, 32)