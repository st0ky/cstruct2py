import os
import cStringIO
from pycparser.c_parser import CParser
import pcpp
import pycparser
from .pycstruct import MetaPyStruct
from .pycunion import MetaPyUnion
from .pycarray import MetaPyArray
from .pycenum import MetaPyEnum
from .configuration import gcc_x86_64_le


sizeof = len
get_dir = lambda x: os.path.dirname(os.path.abspath(x))


class Parser(object):
    """A class for parsing C headres to python structs. It saves the context and configuration"""
    def __init__(self, conf=gcc_x86_64_le, debuglevel=0):
        super(Parser, self).__init__()
        self.conf = conf
        self.debuglevel = debuglevel

        self.basics = conf.basics
        self.names_to_pycstructs = {}

        self.structs_num = 0
        self.unions_num = 0
        self.arrays_num = 0
        self.enums_num = 0
        self.cdata = ""
        self.last_processed = ""


        funcs = {}
        funcs[pycparser.c_ast.IdentifierType]    = self.type_handler
        funcs[pycparser.c_ast.IdentifierType]    = self.type_handler
        funcs[pycparser.c_ast.Struct]            = self.struct_handler
        funcs[pycparser.c_ast.Union]             = self.union_handler
        funcs[pycparser.c_ast.Enum]              = self.enum_handler
        funcs[pycparser.c_ast.EnumeratorList]    = self.enumerator_list_handler
        funcs[pycparser.c_ast.Enumerator]        = self.enumerator_handler
        funcs[pycparser.c_ast.ArrayDecl]         = self.array_handler
        funcs[pycparser.c_ast.PtrDecl]           = self.ptr_handler
        funcs[pycparser.c_ast.Typedef]           = self.typedef_handler
        funcs[pycparser.c_ast.Typename]          = self.typename_handler
        funcs[pycparser.c_ast.TypeDecl]          = self.typedecl_handler
        funcs[pycparser.c_ast.Decl]              = self.decl_handler
        funcs[pycparser.c_ast.FuncDecl]          = self.func_decl_handler
        funcs[pycparser.c_ast.FuncDef]           = self.func_def_handler
        funcs[pycparser.c_ast.Constant]          = self.constant_handler
        funcs[pycparser.c_ast.BinaryOp]          = self.binary_op_handler
        funcs[pycparser.c_ast.UnaryOp]           = self.unary_op_handler
        funcs[pycparser.c_ast.Cast]              = self.cast_handler
        self.funcs = funcs

        self.flush()

    def flush(self):
        self.pre = pcpp.Preprocessor()
        self.pre.line_directive = None

        self.cparse = CParser()

        self.cdata = ""
        self.last_processed = ""


    def has_type(self, val):
        return self.conf.has_type(val) or val in self.names_to_pycstructs

    def get_type(self, val):
        if self.conf.has_type(val):
            return self.conf.get_type(val)
        return self.names_to_pycstructs[val]

    def set_type(self, name, val):
        self.names_to_pycstructs[name] = val
        self.names_to_pycstructs[(name, )] = val
        return val

    def typedef_handler(self, node):
        assert type(node) is pycparser.c_ast.Typedef
        name = node.name
        val = self.parse_node(node.type)
        return self.set_type(name, val)

    def _field_handler(self, node):
        assert type(node) is pycparser.c_ast.Decl
        name = node.name
        typ = self.parse_node(node.type)
        return name, typ

    def enum_handler(self, node):
        assert type(node) == pycparser.c_ast.Enum

        name = node.name
        self.enums_num += 1
        if name == None:
            name = "enum_num_%d" % self.enums_num

        values = self.parse_node(node.values)
        val = MetaPyEnum(name, (), dict(_values=values), self.conf)

        for item in val:
            self.set_type(str(item), item)

        return self.set_type(name, val)

    def enumerator_handler(self, node):
        assert type(node) == pycparser.c_ast.Enumerator
        return self.parse_node(node.value), node.name

    def enumerator_list_handler(self, node):
        assert type(node) == pycparser.c_ast.EnumeratorList
        return map(self.parse_node, node.enumerators)

    def struct_handler(self, node):
        assert type(node) == pycparser.c_ast.Struct

        fields = []
        name = node.name
        
        if not node.decls:
            if self.has_type((name, )):
                return self.get_type((name, ))
            else:
                fields = None

        
        if fields is not None:
            for decl in node.decls:
                field_name, field_type = self._field_handler(decl)
                fields.append((field_name, field_type))

        self.structs_num += 1
        if name == None:
            name = "struct_num_%d" % self.structs_num

        if self.has_type((name, )):
            val = self.get_type((name, ))
            MetaPyStruct.assign_fields(val, fields)
        else:
            val = MetaPyStruct(name, (), {"_fields" : fields})
            val.__module__ = None
            self.set_type(name, val)

        return val

    def union_handler(self, node):
        assert type(node) == pycparser.c_ast.Union
        
        fields = []
        name = node.name
        
        if not node.decls:
            if self.has_type((name, )):
                return self.get_type((name, ))
            else:
                fields = None

        if fields is not None:
            for decl in node.decls:
                field_name, field_type = self._field_handler(decl)
                fields.append((field_name, field_type))

        self.unions_num += 1
        if name == None:
            name = "union_num_%d" % self.unions_num

        if self.has_type((name, )):
            val = self.get_type((name, ))
            MetaPyUnion.assign_fields(val, fields)
        else:
            val = MetaPyUnion(name, (), {"_fields" : fields})
            val.__module__ = None
            self.set_type(name, val)
        
        return val

    def array_handler(self, node):
        assert type(node) is pycparser.c_ast.ArrayDecl
        typ = self.parse_node(node.type)
        num = self.parse_node(node.dim)
        assert num is None or type(num) in [long, int]
        self.arrays_num += 1
        val = MetaPyArray("array_num_%d" % self.arrays_num, (), {"_type" : typ, "_count" : num})
        val.__module__ = None
        return val


    def type_handler(self, node):
        assert type(node) is pycparser.c_ast.IdentifierType
        assert self.has_type(tuple(node.names)), str(tuple(node.names))
        return self.get_type(tuple(node.names))

    def typedecl_handler(self, node):
        assert type(node) is pycparser.c_ast.TypeDecl
        return self.parse_node(node.type)

    def typename_handler(self, node):
        assert type(node) is pycparser.c_ast.Typename
        return self.parse_node(node.type)

    def constant_handler(self, node):
        assert type(node) is pycparser.c_ast.Constant
        if node.type == 'char':
            return ord(eval(node.value))
        if node.type == "int":
            return eval(node.value)

        assert 0, "Unknown constant type: %s" % node.type

    def ptr_handler(self, node):
        assert type(node) is pycparser.c_ast.PtrDecl
        return self.get_type(("void", "*", ))

    def decl_handler(self, node):
        assert type(node) is pycparser.c_ast.Decl
        return self.parse_node(node.type)

    def func_decl_handler(self, node):
        assert type(node) is pycparser.c_ast.FuncDecl
        return

    def func_def_handler(self, node):
        assert type(node) is pycparser.c_ast.FuncDef
        return

    def cast_handler(self, node):
        assert type(node) is pycparser.c_ast.Cast
        val = self.parse_node(node.expr)
        obj = self.parse_node(node.to_type)()
        obj._val_property = val
        return obj._val_property


    def binary_op_handler(self, node):
        assert type(node) is pycparser.c_ast.BinaryOp

        return eval("self.parse_node(node.left) %s self.parse_node(node.right)" % node.op)

    def unary_op_handler(self, node):
        assert type(node) is pycparser.c_ast.UnaryOp
        if node.op == "sizeof":
                return sizeof(self.parse_node(node.expr))

        if node.op == "~":
            return ~self.parse_node(node.expr)

        if node.op == "-":
            return -self.parse_node(node.expr)

        assert False, "Unknown unary op: %s" % node.op

    def parse_node(self, node):
        if node is None:
            return node

        if type(node) in self.funcs:
            return self.funcs[type(node)](node)

        node.show()
        assert 0, "Unknown handler for type: %s" % repr(type(node))

    def parse_string(self, data, file_name="<unknown>", include_dirs=[get_dir(__file__)], debuglevel=None):
        if debuglevel is None:
            debuglevel = self.debuglevel

        for i in include_dirs:
            self.pre.add_path(i)
        self.pre.parse(data)
        buff = cStringIO.StringIO()
        self.pre.write(buff)
        processed = buff.getvalue()

        self.last_processed = processed

        not_found = [line for line in processed.splitlines() if "#include" in line]
        if not_found:
            print "There is unresolved includes:"
            for line in not_found:
                print line

        assert "#include " not in processed

        for macro_name, macro in self.pre.macros.items():
            if not macro.arglist:
                self.set_type(macro_name, self.pre.evalexpr(macro.value, get_strings=True))

        contents = self.cparse.parse(processed, file_name)

        self.cdata += processed

        res = []
        for ex in contents.ext:
            if debuglevel:
                ex.show()
            res.append(self.parse_node(ex))

        return res[0] if len(res) == 1 else res

    def parse_file(self, file_path, include_dirs=None, debuglevel=None):
        if include_dirs is None:
            include_dirs = [get_dir(__file__), get_dir(file_path)]

        with open(file_path, "rb") as f:
            data = f.read()

        return self.parse_string(data, file_path, include_dirs, debuglevel)

    def update_globals(self, g):
        """Enters the new classes to globals.
           You should call that functions like that: p.update_globals(globals())
        """
        g.update(self.names_to_pycstructs)


