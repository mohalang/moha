# -*- coding: utf-8 -*-

from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.parsing import ParseError
from rpython.rlib.parsing.deterministic import LexerError

GRAMMAR = r"""
IGNORE: "[ \t\n]";
DECIMAL: "-?0|[1-9][0-9]*";
FLOAT: "-?(0?|[1-9][0-9]*)\.[0-9]+([eE][-+]?[0-9]+)?";
VARIABLE: "[a-zA-Z_][a-zA-Z0-9_]*";
STRING: "\\"[^\\\\"]*\\"";
BIN_SYMBOL: "[-+]";
main: statement* [EOF];
guardcommand: "(" test ")" "{" statement* "}";
args: VARIABLE [","] args | VARIABLE ;
statement: test ";" | func "=" test ";" | "return" test ";" | "do" guardcommand+ | "if" guardcommand+ | "def" VARIABLE "(" args* ")" "{" statement* "}";
object: ["{"] (entry [","])* entry ["}"];
entry: STRING [":"] entry_value;
entry_value: expr | closure;
closure: "def" "(" args* ")" "{" statement* "}";
array: ["["] callargs ["]"] | ["["] ["]"];
test: or_test;
or_test: and_test ("||" and_test)*;
and_test: not_test ("&&" not_test)*;
not_test: "!" not_test | comp;
comp: expr (comp_op expr)*;
comp_op: "==" | ">=" | "<=" | ">" | "<" | "!=";
expr: simple_expr BIN_SYMBOL expr | simple_expr;
simple_expr:  func_call | attr | object | array | atom;
attr: VARIABLE getattr+;
getattr: "." VARIABLE | ["["] test ["]"];
func: attr | VARIABLE;
func_call: func ["("] callargs [")"] | func ["("] [")"];
callargs: test [","] callargs | test;
atom: "true" | "false" | DECIMAL | FLOAT | STRING | VARIABLE;
"""

regexs, rules, ToAST = parse_ebnf(GRAMMAR)
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
