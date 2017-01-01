# -*- coding: utf-8 -*-

from moha.vm.grammar import parse_source
from moha.vm.ast import transformer, CompilerContext
from moha.vm.runtime import Frame, interpret_bytecode

def interpret_source(filename, source):
    bnf_node = parse_source(filename, source)
    if not bnf_node:
        return
    ast = transformer.visit_main(bnf_node)
    c = CompilerContext()
    ast.compile(c)
    bc = c.create_bytecode()
    frame = Frame(bc)
    interpret_bytecode(frame, bc)
