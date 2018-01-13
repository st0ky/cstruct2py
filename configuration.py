from .basics import *


class Config(object):
	def __init__(self):
		super(Config, self).__init__()
		

		names_to_pycstructs = {}
		self.names_to_pycstructs = names_to_pycstructs
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
		names_to_pycstructs[('char', )] = py_char_t
		names_to_pycstructs[('signed', 'long', 'long', )] = py_int64_t
		names_to_pycstructs[('signed', 'long', 'int', )] = py_int64_t
		names_to_pycstructs[('long', 'signed', 'int', )] = py_int64_t
		names_to_pycstructs[('signed', 'long', )] = py_int64_t
		names_to_pycstructs[('signed', 'int', )] = py_int32_t
		names_to_pycstructs[('signed', 'short', )] = py_int16_t
		names_to_pycstructs[('signed', 'byte', )] = py_int8_t
		names_to_pycstructs[('signed', 'char', )] = py_char_t
		names_to_pycstructs[('unsigned', 'long', 'long', )] = py_uint64_t
		names_to_pycstructs[('unsigned', 'long', 'int', )] = py_uint64_t
		names_to_pycstructs[('long', 'unsigned', 'int', )] = py_uint64_t
		names_to_pycstructs[('unsigned', 'long', )] = py_uint64_t
		names_to_pycstructs[('unsigned', 'int', )] = py_uint32_t
		names_to_pycstructs[('unsigned', 'short', )] = py_uint16_t
		names_to_pycstructs[('unsigned', 'byte', )] = py_uint8_t
		names_to_pycstructs[('unsigned', 'char', )] = py_uchar_t
		
		names_to_pycstructs[('void', '*', )] = py_uint64_t

	def get_basics(self):
		return self.names_to_pycstructs


gcc_x86_64_le = Config()