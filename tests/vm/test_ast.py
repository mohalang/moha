# -*- coding: utf-8 -*-

import pytest
from moha.vm.grammar.v0_2_0 import parse_source

def statement(source):
    tree = parse_source('test', source)
    return tree.children[0]

def test_import_a_member_from_module():
    tree = statement('import print from "io";')
    assert tree.symbol == 'import_members_from_module'
    assert tree.children[0].children[0].additional_info == 'print'
    assert tree.children[1].additional_info == '"io"'

def test_import_members_from_module():
    tree = statement('import print, format from "io";')
    assert tree.symbol == 'import_members_from_module'
    assert tree.children[0].children[0].additional_info == 'print'
    assert tree.children[0].children[1].additional_info == 'format'
    assert tree.children[1].additional_info == '"io"'

def test_import_module():
    tree = statement('import "io";')
    assert tree.symbol == 'import_module'
    assert tree.children[0].additional_info == '"io"'

def test_export_all_members_as_module():
    tree = statement('export * as "test";')
    assert tree.symbol == 'export_all_members_as_module'
    assert tree.children[0].additional_info == '"test"'

def test_export_selected_member_as_module():
    tree = statement('export member as "module";')
    assert tree.symbol == 'export_selected_members_as_module'
    assert tree.children[0].children[0].additional_info == 'member'
    assert tree.children[1].additional_info == '"module"'

def test_export_selected_members_as_module():
    tree = statement('export selected, members as "module";')
    assert tree.symbol == 'export_selected_members_as_module'
    assert tree.children[0].children[0].additional_info == 'selected'
    assert tree.children[0].children[1].additional_info == 'members'
    assert tree.children[1].additional_info == '"module"'

def test_statement_abort():
    tree = statement('abort 1;')
    assert tree.symbol == 'abort';
    assert tree.children[0].symbol == 'DECIMAL_LITERAL'
    assert tree.children[0].additional_info == '1'

def test_statement_pass():
    tree = statement('pass;')
    assert tree.symbol == 'pass'

def test_statement_return_empty():
    tree = statement('return;')
    assert tree.symbol == 'return'
    assert not tree.children;

def test_statement_return_null():
    tree = statement('return null;')
    assert tree.symbol == 'return';
    assert tree.children[0].symbol == 'null_literal'

def test_statement_return_const():
    tree = statement('return 1;')
    assert tree.symbol == 'return';
    assert tree.children[0].symbol == 'DECIMAL_LITERAL'
    assert tree.children[0].additional_info == '1'

def test_statement_assignment():
    tree = statement('num = 1;')
    assert tree.symbol == 'assignment'
    assert tree.children[0].symbol == 'assignment_left'
    assert tree.children[0].children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'DECIMAL_LITERAL'
    assert tree.children[1].additional_info == '1'

def test_statement_selector_assignment():
    tree = statement('obj.attribute = 1;')
    assert tree.symbol == 'assignment';
    assert tree.children[0].symbol == 'assignment_left'
    assert tree.children[0].children[0].symbol == 'IDENTIFIER'
    assert tree.children[0].children[1].symbol == 'identifier_selector'
    assert tree.children[1].symbol == 'DECIMAL_LITERAL'

def test_statement_if():
    tree = statement('if (a == 1) { a = 2; } (a == 2) { a = 1; }')
    assert tree.symbol == 'if'
    assert tree.children[0].symbol == 'guardcommand'
    assert tree.children[0].children[0].symbol == 'expression'
    assert tree.children[0].children[1].symbol == 'block'
    assert tree.children[1].symbol == 'guardcommand'

def test_statement_do():
    tree = statement('do (a == 1) { a = 2; } (a == 2) { a = 1; }')
    assert tree.symbol == 'do'
    assert tree.children[0].symbol == 'guardcommand'
    assert tree.children[0].children[0].symbol == 'expression'
    assert tree.children[0].children[1].symbol == 'block'
    assert tree.children[1].symbol == 'guardcommand'

def test_statement_def():
    tree = statement('def test() { return null; }')
    assert tree.symbol == 'def'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert len(tree.children[1].children) == 0
    assert tree.children[2].symbol == 'block'

def test_statement_def_arg():
    tree = statement('def test(arg) { return arg; }')
    assert tree.symbol == 'def'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert len(tree.children[1].children) == 1
    assert tree.children[1].children[0].symbol == 'IDENTIFIER'
    assert tree.children[2].symbol == 'block'

def test_statement_def_args():
    tree = statement('def test(arg1, arg2) { return arg; }')
    assert tree.symbol == 'def'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert len(tree.children[1].children) == 2
    assert tree.children[2].symbol == 'block'

def test_expression_decimal():
    tree = statement('1;')
    assert tree.symbol == 'DECIMAL_LITERAL';

def test_expression_octal():
    tree = statement('0o1;')
    assert tree.symbol == 'OCTAL_LITERAL';
    tree = statement('0O1;')
    assert tree.symbol == 'OCTAL_LITERAL';

def test_expression_hex_literal():
    tree = statement('0xffff;')
    assert tree.symbol == 'HEX_LITERAL';
    tree = statement('0XFFFF;')
    assert tree.symbol == 'HEX_LITERAL';

def test_expression_bin_literal():
    tree = statement('0b101;');
    assert tree.symbol == 'BIN_LITERAL';
    tree = statement('0B101;');
    assert tree.symbol == 'BIN_LITERAL';

def test_expression_float_literal():
    tree = statement('1.0;');
    assert tree.symbol == 'FLOAT_LITERAL';

def test_expression_string_literal():
    tree = statement('"hello world";');
    assert tree.symbol == 'STRING_LITERAL';

def test_expression_plus_expression():
    tree = statement('+1;');
    assert tree.symbol == 'unary_expression'
    assert tree.children[0].additional_info == '+'
    assert tree.children[1].symbol == 'DECIMAL_LITERAL';

def test_expression_minus_expression():
    tree = statement('-1;');
    assert tree.symbol == 'unary_expression'
    assert tree.children[0].additional_info == '-'
    assert tree.children[1].symbol == 'DECIMAL_LITERAL';

def test_expression_not_expression():
    tree = statement('!true;');
    assert tree.symbol == 'unary_expression'
    assert tree.children[0].additional_info == '!'
    assert tree.children[1].symbol == 'boolean_literal';

@pytest.mark.parametrize('op', ['||', '&&', '==', '!=', '<', '>', '<=', '>=', '+', '-', '|', '^', '*', '/', '%', '<<', '>>', '&', '&^'])
def test_expression_bin_expression(op):
    tree = statement('1 %s 1;' % op);
    assert tree.symbol == 'expression'
    assert tree.children[0].symbol == 'DECIMAL_LITERAL'
    assert tree.children[1].additional_info == op
    assert tree.children[2].symbol == 'DECIMAL_LITERAL'

def test_expression_identifier_selector():
    tree = statement('object.selector;')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'identifier_selector'
    assert tree.children[1].children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].children[0].additional_info == 'selector'

def test_expression_index_selector():
    tree = statement('object["selector"];')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'index_selector'
    assert tree.children[1].children[0].symbol == 'STRING_LITERAL'
    assert tree.children[1].children[0].additional_info == '"selector"'

def test_expression_argument():
    tree = statement('funccall();')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'arguments'
    assert len(tree.children[1].children) == 0

def test_expression_argument():
    tree = statement('funccall(1);')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'arguments'
    assert len(tree.children[1].children) == 1

def test_expression_argument():
    tree = statement('funccall(1, 2);')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'arguments'
    assert len(tree.children[1].children) == 2

def test_expression_selector_mix_argument():
    tree = statement('object.method(1, 2);')
    assert tree.symbol == 'primary_expression'
    assert tree.children[0].symbol == 'IDENTIFIER'
    assert tree.children[1].symbol == 'identifier_selector'
    assert tree.children[2].symbol == 'arguments'

def test_expression_empty_array():
    tree = statement('[];')
    assert tree.symbol == 'array_literal'
    assert len(tree.children) == 0

def test_expression_single_element_array():
    tree = statement('[1];')
    assert tree.symbol == 'array_literal'
    assert len(tree.children) == 1
    assert tree.children[0].symbol == 'DECIMAL_LITERAL'

def test_expression_multiple_elements_array():
    tree = statement('[1, 2];')
    assert tree.symbol == 'array_literal'
    assert len(tree.children) == 2
    assert tree.children[1].symbol == 'DECIMAL_LITERAL'

def test_expression_empty_object():
    tree = statement('{};')
    assert tree.symbol == 'object_literal'
    assert len(tree.children) == 0

def test_expression_single_entry_object():
    tree = statement('{"integer": 1};')
    assert tree.symbol == 'object_literal'
    assert len(tree.children) == 1

def test_expression_multi_entries_object():
    tree = statement('{"integer": 1, "float": 1.0};')
    assert tree.symbol == 'object_literal'
    assert len(tree.children) == 1
