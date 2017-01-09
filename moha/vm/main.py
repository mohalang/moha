# -*- coding: utf-8 -*-

from moha.vm.grammar.v0_2_0 import parse_source
from moha.vm.ast import transformer, CompilerContext
from moha.vm.runtime import Frame, interpret_bytecode
from moha.vm.compiler import Compiler

def interpret_source(filename, source):
    bnf_node = parse_source(filename, source)
    if not bnf_node:
        return
    compiler = Compiler()
    compiler.dispatch(bnf_node)
    bc = compiler.create_bytecode()
    frame = Frame(bc)
    interpret_bytecode(frame, bc)
