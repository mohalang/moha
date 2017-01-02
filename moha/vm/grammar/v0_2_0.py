# -*- coding: utf-8 -*-

import os
import py
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.parsing import ParseError
from rpython.rlib.parsing.deterministic import LexerError

grammar_dir = os.path.dirname(os.path.abspath(__file__))
grammar = py.path.local(grammar_dir).join('v0_2_0.txt').read("rt")
regexs, rules, ToAST = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)

def parse_source(filename, source):
    try:
        return _parse(source)
    except ParseError as e:
        print(e.nice_error_message(filename, source))
        return
    except LexerError as e:
        print(e.nice_error_message(filename))
        return

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        source = f.read()
        tree = parse_source(sys.argv[1], source)
        print tree
