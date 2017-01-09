# -*- coding: utf-8 -*-

import os
from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.objectmodel import we_are_translated
from moha.vm.grammar.v0_2_0 import parse_source
from moha.vm.ast import transformer, CompilerContext
from moha.vm.objects import Sys
from moha.vm.runtime import Frame, interpret_bytecode
from moha.vm.compiler import Compiler

def interpret_source(executable, filename):
    f = open_file_as_stream(filename)
    source = f.readall()
    f.close()

    bnf_node = parse_source(filename, source)
    if not bnf_node:
        return

    compiler = Compiler()
    compiler.dispatch(bnf_node)

    sys = Sys()
    if we_are_translated():
        sys.set_executable(executable)
        sys.set_cwd(os.getcwd())
    else:
        sys.set_env_path(os.getcwd())
        sys.set_executable(os.getcwd() + executable)
        sys.set_cwd(os.getcwd())

    bc = compiler.create_bytecode()
    frame = Frame(bc)
    interpret_bytecode(sys, filename, frame, bc)
