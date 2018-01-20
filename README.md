# cstruct2py

Pure python library for generate python classes from code C and use them to pack and unpack data

## Credits
The library uses [pcpp](https://github.com/ned14/pcpp) to preprocess the C code and [pycparser](https://github.com/eliben/pycparser) to make ast from the C code.

## How to use
##### First we need to generate the pythonic structs:
```
import cstruct2py
parser = cstruct2py.c2py.Parser()
parser.parse_file('examples/example.h')
```
Now we can import all names from the C code:
```
parser.update_globals(globals())
```
We can also do that directly:
```
A = parser.parse_string('struct A { int x; int y;};')
```
##### Using types and defines from the C code
```
a = A()
a.x = 45
print a
buf = a.packed
b = A(buf)
print b
c = A('aaaa11112222', 2)
print c
print repr(c)
```
The output will be:
```
{'x':0x2d, 'y':0x0}
{'x':0x2d, 'y':0x0}
{'x':0x31316161, 'y':0x32323131}
A('aa111122', x=0x31316161, y=0x32323131)
```

## Clone the project
For clone this project run:
```
git clone https://github.com/st0ky/cstruct2py.git --recursive
```
