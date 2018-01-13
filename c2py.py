import os
import cStringIO
from pycparser.c_parser import CParser
import pcpp
import pycparser
from .pycstruct import MetaPyStruct
from .pycunion import MetaPyUnion
from .pycarray import MetaPyArray
from .configuration import gcc_x86_64_le


sizeof = len
get_dir = lambda x: os.path.dirname(os.path.abspath(x))


class Parser(object):
    """A class for parsing C headres to python structs. It saves the context and configuration"""
    def __init__(self, conf=gcc_x86_64_le):
        super(Parser, self).__init__()
        self.conf = conf

        self.basics = conf.get_basics()
        self.names_to_pycstructs = {}

        self.structs_num = 0
        self.unions_num = 0
        self.arrays_num = 0

    def has_type(self, val):
        return val in self.basics or val in self.names_to_pycstructs

    def get_type(self, val):
        return self.basics[val] if val in self.basics else self.names_to_pycstructs[val]

    def typedef_handler(self, node):
        assert type(node) is pycparser.c_ast.Typedef
        name = node.name
        val = self.parse_node(node.type)
        self.names_to_pycstructs[name] = val
        self.names_to_pycstructs[(name, )] = val

    def _field_handler(self, node):
        assert type(node) is pycparser.c_ast.Decl
        name = node.name
        typ = self.parse_node(node.type)
        return name, typ

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
            val.__module__ = __name__
            self.names_to_pycstructs[name] = val
            self.names_to_pycstructs[(name, )] = val

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
            val.__module__ = __name__
            self.names_to_pycstructs[name] = val
            self.names_to_pycstructs[(name, )] = val
        
        return val

    def array_handler(self, node):
        assert type(node) is pycparser.c_ast.ArrayDecl
        typ = self.parse_node(node.type)
        num = self.parse_node(node.dim)
        assert num is None or type(num) in [long, int]
        self.arrays_num += 1
        val = MetaPyArray("array_num_%d" % self.arrays_num, (), {"_type" : typ, "_count" : num})
        val.__module__ = __name__
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

    def binary_op_handler(self, node):
        assert type(node) is pycparser.c_ast.BinaryOp

        return eval("self.parse_node(node.left) %s self.parse_node(node.right)" % node.op)

    def unary_op_handler(self, node):
        assert type(node) is pycparser.c_ast.UnaryOp
        if node.op == "sizeof":
                return sizeof(self.parse_node(node.expr))

        if node.op == "~":
            return ~self.parse_node(node.expr)

        assert False, "Unknown unary op: %s" % node.op

    def parse_node(self, node):
        if node is None:
            return node

        funcs = {}
        funcs[pycparser.c_ast.IdentifierType]    = self.type_handler
        funcs[pycparser.c_ast.IdentifierType]    = self.type_handler
        funcs[pycparser.c_ast.Struct]            = self.struct_handler
        funcs[pycparser.c_ast.Union]             = self.union_handler
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
        
        if type(node) in funcs:
            return funcs[type(node)](node)

        
        assert 0, "Unknown handler for type: %s" % repr(type(node))

    def parse_string(self, data, file_name="<unknown>", include_dirs=[get_dir(__file__)], save_tmp=False, debuglevel=0):
        pre = pcpp.Preprocessor()
        pre.line_directive = None
        for i in include_dirs:
            pre.add_path(i)
        pre.parse(data)
        buff = cStringIO.StringIO()
        pre.write(buff)
        processed = buff.getvalue()
        if save_tmp:
            tmp_path = os.path.abspath(file_name) + ".tmp"
            if debuglevel:
                print "Creating tmp file: %s" % tmp_path
            with open(tmp_path, "wb") as f:
                f.write(processed)

        for macro_name, macro in pre.macros.items():
            if not macro.arglist:
                self.names_to_pycstructs[macro_name] = pre.evalexpr(macro.value, get_strings=True)

        cparse = CParser()
        contents = cparse.parse(processed, file_name)

        for ex in contents.ext:
            if debuglevel:
                ex.show()
            self.parse_node(ex)

        if save_tmp:
            os.unlink(tmp_path)

    def parse_file(self, file_path, include_dirs=None, save_tmp=False, debuglevel=0):
        if include_dirs is None:
            include_dirs = [get_dir(__file__), get_dir(file_path)]

        with open(file_path, "rb") as f:
            data = f.read()

        self.parse_string(data, file_path, include_dirs, save_tmp, debuglevel)

    def update_globals(self, g):
        """Enters the new classes to globals.
           You should call that functions like that: p.update_globals(globals())
        """
        g.update(**self.names_to_pycstructs)


