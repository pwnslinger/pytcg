#
# Build libtcg interface
#
from cffi import FFI
import logging
l = logging.getLogger('cffier')
l.setLevel(logging.DEBUG)
ffibuilder = FFI()


def doit():
    import os
    print(os.path.abspath(os.path.curdir))
    src = \
    r"""
    #include <dlfcn.h>
    #include <assert.h>
    #include <stdio.h>
    #include <libtcg.h>
    #define TARGET_LONG_BITS 64
    #define tcg_debug_assert assert
    /* tcg-common.c */
    #include "tcg.h"
    #include "tcg-target.h"
    LibTCGOpDef tcg_op_defs[] = {
    #define DEF(s, oargs, iargs, cargs, flags) \
            { #s, oargs, iargs, cargs, iargs + oargs + cargs, flags },
    #include "tcg-opc.h"
    #undef DEF
    };
    """
    ffibuilder.set_source("libtcg", src, include_dirs=['inc', 'libtcg'], libraries=['dl'])

    # FIXME: Should be generating the API.h file from libtcg, but CFFI C parser
    # is pretty picky.
    src = open('inc/api.h', 'r').read()
    src += r"""
    LibTCGOpDef tcg_op_defs[];
    """
    ffibuilder.cdef(src)
    ffibuilder.compile(verbose=True)

if __name__ == '__main__':
    logging.basicConfig(logging.DEBUG)
    doit()
