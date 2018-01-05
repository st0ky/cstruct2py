import os
import cStringIO
from pycparser.c_parser import CParser
import pcpp
import pycparser
from .basics import *
from .pycstruct import MetaPyStruct
from .pycunion import MetaPyUnion
from .pycarray import MetaPyArray

names_to_pycstructs = {}
names_to_pycstructs[('uint64_t', )] = py_uint64_t
names_to_pycstructs[('uint32_t', )] = py_uint32_t
names_to_pycstructs[('uint16_t', )] = py_uint16_t
names_to_pycstructs[('uint8_t', )] = py_uint8_t
names_to_pycstructs[('int64_t', )] = py_int64_t
names_to_pycstructs[('int32_t', )] = py_int32_t
names_to_pycstructs[('int16_t', )] = py_int16_t
names_to_pycstructs[('int8_t', )] = py_int8_t

names_to_pycstructs[('float', )] = py_float32_t
names_to_pycstructs[('double', )] = py_float64_t
names_to_pycstructs[('long', 'double', )] = py_float64_t

names_to_pycstructs[('long', 'long', )] = py_int64_t
names_to_pycstructs[('long', 'int', )] = py_int64_t
names_to_pycstructs[('long', )] = py_int64_t
names_to_pycstructs[('int', )] = py_int32_t
names_to_pycstructs[('short', )] = py_int16_t
names_to_pycstructs[('byte', )] = py_int8_t
names_to_pycstructs[('char', )] = py_int8_t
names_to_pycstructs[('signed', 'long', 'long', )] = py_int64_t
names_to_pycstructs[('signed', 'long', 'int', )] = py_int64_t
names_to_pycstructs[('long', 'signed', 'int', )] = py_int64_t
names_to_pycstructs[('signed', 'long', )] = py_int64_t
names_to_pycstructs[('signed', 'int', )] = py_int32_t
names_to_pycstructs[('signed', 'short', )] = py_int16_t
names_to_pycstructs[('signed', 'byte', )] = py_int8_t
names_to_pycstructs[('signed', 'char', )] = py_int8_t
names_to_pycstructs[('unsigned', 'long', 'long', )] = py_uint64_t
names_to_pycstructs[('unsigned', 'long', 'int', )] = py_uint64_t
names_to_pycstructs[('long', 'unsigned', 'int', )] = py_uint64_t
names_to_pycstructs[('unsigned', 'long', )] = py_uint64_t
names_to_pycstructs[('unsigned', 'int', )] = py_uint32_t
names_to_pycstructs[('unsigned', 'short', )] = py_uint16_t
names_to_pycstructs[('unsigned', 'byte', )] = py_uint8_t
names_to_pycstructs[('unsigned', 'char', )] = py_uint8_t

sizeof = len


global_assignment = """
global %(name)s
%(name)s = %(var)s
"""

structs_num = 0
unions_num = 0
arrays_num = 0

def typedef_handler(node):
    assert type(node) is pycparser.c_ast.Typedef
    name = node.name
    val = parse_node(node.type)
    names_to_pycstructs[name] = val
    names_to_pycstructs[(name, )] = val
    exec(global_assignment % {"name" : name, "var" : "val"})

def _field_handler(node):
    assert type(node) is pycparser.c_ast.Decl
    name = node.name
    typ = parse_node(node.type)
    return name, typ

def struct_handler(node):
    global names_to_pycstructs
    assert type(node) == pycparser.c_ast.Struct
    name = node.name
    if not node.decls:
        return names_to_pycstructs[(name, )]

    fields = []
    for decl in node.decls:
        field_name, field_type = _field_handler(decl)
        fields.append((field_name, field_type))

    global structs_num
    structs_num += 1
    if name == None:
        name = "struct_num_%d" % structs_num

    val = MetaPyStruct(name, (), {"_fields" : fields})
    val.__module__ = val.__module__.replace("pycstruct", "c2py")
    names_to_pycstructs[name] = val
    names_to_pycstructs[(name, )] = val
    exec(global_assignment % {"name" : name, "var" : "val"})
    return val

def union_handler(node):
    global names_to_pycstructs
    assert type(node) == pycparser.c_ast.Union
    name = node.name
    if not node.decls:
        return names_to_pycstructs[(name, )]

    fields = []
    for decl in node.decls:
        field_name, field_type = _field_handler(decl)
        fields.append((field_name, field_type))

    global unions_num
    unions_num += 1
    if name == None:
        name = "unions_num_%d" % unions_num

    val = MetaPyUnion(name, (), {"_fields" : fields})
    val.__module__ = val.__module__.replace("pycunion", "c2py")
    names_to_pycstructs[name] = val
    names_to_pycstructs[(name, )] = val
    exec(global_assignment % {"name" : name, "var" : "val"})
    return val

def array_handler(node):
    assert type(node) is pycparser.c_ast.ArrayDecl
    typ = parse_node(node.type)
    num = parse_node(node.dim)
    assert num is None or type(num) in [long, int]
    global arrays_num
    arrays_num += 1
    val = MetaPyArray("array_num_%d" % arrays_num, (), {"_type" : typ, "_count" : num})
    val.__module__ = val.__module__.replace("pycarray", "c2py")
    return val


def type_handler(node):
    assert type(node) is pycparser.c_ast.IdentifierType
    assert tuple(node.names) in names_to_pycstructs, str(tuple(node.names))
    return names_to_pycstructs[tuple(node.names)]

def typedecl_handler(node):
    assert type(node) is pycparser.c_ast.TypeDecl
    return parse_node(node.type)

def typename_handler(node):
    assert type(node) is pycparser.c_ast.Typename
    return parse_node(node.type)

def constant_handler(node):
    assert type(node) is pycparser.c_ast.Constant
    if node.type == 'char':
        return ord(eval(node.value))
    if node.type == "int":
        return eval(node.value)

    assert 0, "Unknown constant type: %s" % node.type

def ptr_handler(node):
    assert type(node) is pycparser.c_ast.PtrDecl
    return py_uint64_t

def decl_handler(node):
    assert type(node) is pycparser.c_ast.Decl
    return parse_node(node.type)

def func_decl_handler(node):
    assert type(node) is pycparser.c_ast.FuncDecl
    return

def parse_node(node):
    if node is None:
        return node

    if type(node) is pycparser.c_ast.IdentifierType:
        return type_handler(node)

    if type(node) is pycparser.c_ast.Struct:
        return struct_handler(node)

    if type(node) is pycparser.c_ast.Union:
        return union_handler(node)

    if type(node) is pycparser.c_ast.ArrayDecl:
        return array_handler(node)

    if type(node) is pycparser.c_ast.PtrDecl:
        return ptr_handler(node)

    if type(node) is pycparser.c_ast.Typedef:
        return typedef_handler(node)

    if type(node) is pycparser.c_ast.Typename:
        return typename_handler(node)

    if type(node) is pycparser.c_ast.TypeDecl:
        return typedecl_handler(node)

    if type(node) is pycparser.c_ast.Decl:
        return decl_handler(node)

    if type(node) is pycparser.c_ast.FuncDecl:
        return func_decl_handler(node)

    if type(node) == pycparser.c_ast.Constant:
        return constant_handler(node)

    if type(node) == pycparser.c_ast.BinaryOp:
        return eval("parse_node(node.left) %s parse_node(node.right)" % node.op)

    if type(node) == pycparser.c_ast.UnaryOp:
        if node.op == "sizeof":
            return sizeof(parse_node(node.expr))

        if node.op == "~":
            return ~parse_node(node.expr)

    else:
        assert 0, "Unknown handler for type: %s" % repr(type(node))
get_dir = lambda x: os.path.dirname(os.path.abspath(x))
def parse_string(data, file_name="<unknown>", include_dirs=[get_dir(__file__)], save_tmp=False, debuglevel=0):
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
            tmp = pre.evalexpr(macro.value, get_strings=True)
            exec(global_assignment % {"name" : macro_name, "var" : "tmp"})

    cparse = CParser()
    contents = cparse.parse(processed, file_name)

    for ex in contents.ext:
        if debuglevel:
            ex.show()
        parse_node(ex)

    if save_tmp:
        os.unlink(tmp_path)

def parse_file(file_path, include_dirs=None, save_tmp=False, debuglevel=0):
    if include_dirs is None:
        include_dirs = [get_dir(__file__), get_dir(file_path)]

    with open(file_path, "rb") as f:
        data = f.read()

    parse_string(data, file_path, include_dirs, save_tmp, debuglevel)


