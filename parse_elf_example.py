import sys
import cstruct2py

cstruct2py.c2py.parse_file("cstruct2py/example.h")
from cstruct2py.c2py import *

sizeof = len

def main(file_path):

    data = open(file_path, "rb").read()

    expected_magic = [ELFMAG0, ord(ELFMAG1), ord(ELFMAG2), ord(ELFMAG3)]
    elf_hdr = Elf64_Ehdr(data)
    print elf_hdr.e_ident
    # assert elf_hdr.e_ident == expected_magic
    assert elf_hdr.e_ident[EI_CLASS] == ELFCLASS64
    # assert elf_hdr.e_ident[EI_OSABI] == ELFOSABI_LINUX
    assert elf_hdr.e_machine == EM_X86_64

    print "program header offset: %d" % elf_hdr.e_phoff
    print "program header num: %d" % elf_hdr.e_phnum
    print "section header offset: %d" % elf_hdr.e_shoff
    print "section header num: %d" % elf_hdr.e_shnum
    print "section header string table: %d" % elf_hdr.e_shstrndx

    string_offset = elf_hdr.e_shstrndx;
    print "string offset at %d\n" % string_offset
    print 

    for i in xrange(elf_hdr.e_phnum):
        offset = elf_hdr.e_phoff + i * elf_hdr.e_phentsize;
        phdr = Elf64_Phdr(data, offset);
        print "PROGRAM HEADER %d, offset = %d" % (i, offset)
        print "========================"
        print ("p_type = ", )
        if phdr.p_type == PT_NULL: 
            print "PT_NULL"
        elif phdr.p_type == PT_LOAD:
            print "PT_LOAD"
        elif phdr.p_type == PT_DYNAMIC:
            print "PT_DYNAMIC"
        elif phdr.p_type == PT_INTERP:
            print "PT_INTERP"
        elif phdr.p_type == PT_NOTE:
            print "PT_NOTE"
        elif phdr.p_type == PT_SHLIB:
            print "PT_SHLIB"
        elif phdr.p_type == PT_PHDR:
            print "PT_PHDR"
        elif phdr.p_type == PT_LOPROC:
            print "PT_LOPROC"
        elif phdr.p_type == PT_HIPROC:
            print "PT_HIPROC"
        elif phdr.p_type == PT_GNU_STACK:
            print "PT_GNU_STACK"
        else:
            print "UNKNOWN/%d" % phdr.p_type
        break;
    
        print "p_offset = %d" % phdr.p_offset
        print "p_vaddr = %d" % phdr.p_vaddr
        print "p_paddr = %d" % phdr.p_paddr
        print "p_filesz = %d" % phdr.p_filesz
        print "p_memsz = %d" % phdr.p_memsz
        print "p_flags = %d" % phdr.p_flags
        print "p_align = %lu" % phdr.p_align
        print
  

    dynstr_off = 0
    dynsym_off = 0
    dynsym_sz = 0

    for i in xrange(elf_hdr.e_shnum):
        offset = elf_hdr.e_shoff + i * elf_hdr.e_shentsize
        shdr = Elf64_Shdr(data, offset)
        if shdr.sh_type == SHT_SYMTAB or shdr.sh_type == SHT_STRTAB:
            # // TODO: have to handle multiple string tables better
            if not dynstr_off:
                print "found string table at %d" % shdr.sh_offset
                dynstr_off = shdr.sh_offset
        elif shdr.sh_type == SHT_DYNSYM:
            dynsym_off = shdr.sh_offset
            dynsym_sz = shdr.sh_size
            print "found dynsym table at %d, size %d" % (shdr.sh_offset, shdr.sh_size)
    assert(dynstr_off);
    assert(dynsym_off);
    print "final value for dynstr_off = %d" % dynstr_off
    print "final value for dynsym_off = %d" % dynsym_off
    print "final value for dynsym_sz = %d" % dynsym_sz

    for j in xrange(dynsym_sz / sizeof(Elf64_Sym)):
        absoffset = dynsym_off + j * sizeof(Elf64_Sym);
        sym =  Elf64_Sym(data, absoffset)
        print "SYMBOL TABLE ENTRY %d" % j
        print "st_name = %d" % sym.st_name
        if sym.st_name:
            print " (%s)" % data[dynstr_off + sym.st_name:dynstr_off + sym.st_name + data[dynstr_off + sym.st_name:].index("\x00") + 1]
        
        print "st_info = %d" % sym.st_info
        print "st_other = %d" % sym.st_other
        print "st_shndx = %d" % sym.st_shndx
        print "st_value = %#X" % sym.st_value
        print "st_size = %d" % sym.st_size



if __name__ == '__main__':
    main()