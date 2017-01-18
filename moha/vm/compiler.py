# -*- coding: utf-8 -*-

from rpython.rlib.parsing.tree import RPythonVisitor
from moha.vm import code
from moha.vm.objects import *
from moha.vm.utils import SortedSet, NOT_FOUND

class Compiler(RPythonVisitor):
    """Compile AST to bytecode."""

    def __init__(self, _globals=None):
        self.codes = []
        self.consts = []
        self.vars = SortedSet()
        self.names = SortedSet()
        self.exports = {}
        self.globals = _globals or SortedSet()

    def register_constant(self, v):
        self.consts.append(v)
        return len(self.consts) - 1

    def register_name(self, name):
        return self.names.add(name)

    def lookup_name(self, name):
        return self.names.get(name)

    def register_var(self, name):
        return self.vars.add(name)

    def lookup_var(self, name):
        return self.vars.get(name)

    def register_global(self, name):
        return self.globals.add(name)

    def lookup_global(self, name):
        return self.globals.get(name)

    def emit(self, bc, arg=0):
        self.codes.append(bc)
        self.codes.append(arg)

    def create_bytecode(self):
        return Bytecode(self.codes, self.consts[:], self.vars, self.names)

    def extract_string(self, string_literal):
        string = str(string_literal)
        begin = 1
        end = len(string) -1
        end = begin if end < 0 else end
        return string[begin:end]

    def visit_IDENTIFIER(self, node):
        if self.lookup_var(node.additional_info) == NOT_FOUND:
            self.emit(code.LOAD_GLOBAL, self.register_name(node.additional_info))
        else:
            self.emit(code.LOAD_VAR, self.register_var(node.additional_info))

    def visit_STRING_LITERAL(self, node):
        string = self.extract_string(node.additional_info)
        value = String(string)
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_DECIMAL_LITERAL(self, node):
        value = Integer(int(node.additional_info))
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_OCTAL_LITERAL(self, node):
        value = Integer(int(node.additional_info, 8))
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_HEX_LITERAL(self, node):
        value = Integer(int(node.additional_info, 16))
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_BIN_LITERAL(self, node):
        value = Integer(int(node.additional_info, 2))
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_FLOAT_LITERAL(self, node):
        value = Integer(float(node.additional_info))
        self.emit(code.LOAD_CONST, self.register_constant(value))

    def visit_main(self, node):
        for children in node.children:
            self.dispatch(children)

    def visit_statement(self, node):
        expression = node.children[0]
        self.dispatch(expression)
        self.emit(code.POP)

    def visit_import_members_from_module(self, node):
        module_name = self.extract_string(node.children[1].additional_info)
        self.emit(code.LOAD_CONST, self.register_constant(String(module_name)))
        self.emit(code.IMPORT_MODULE)

        for member in node.children[0].children:
            member_name = String(member.additional_info)
            self.emit(code.LOAD_CONST, self.register_constant(member_name))
            self.emit(code.IMPORT_MEMBER, self.register_var(member.additional_info))

        self.emit(code.POP)

    def visit_import_module(self, node):
        module_name = self.extract_string(node.children[0].additional_info)
        self.emit(code.LOAD_CONST, self.register_constant(String(module_name)))
        self.emit(code.IMPORT_MODULE)
        packages = module_name.split('/')
        var_name = packages[len(packages) - 1]
        self.emit(code.STORE_VAR, self.register_var(var_name))

    def visit_export_all_members_as_module(self, node):
        pass
        # module_name = self.extract_string(node.children[0].additional_info)
        # if self.globals.include(module_name):
            # print('[WARNING] module "%s" is overwritten.' % module_name)
        # bytecode = self.create_bytecode()
        # members = list(self.vars.keys)
        # module = Module(module_name, members, bytecode)
        # self.globals[module_name] = module

    def visit_export_selected_members_as_module(self, node):
        pass
        # module_name = self.extract_string(node.children[1].additional_info)
        # if module_name in self.globals:
            # print('[WARNING] module "%s" is overwritten.' % module_name)
        # self.globals[module_name] = self.create_bytecode()

        # module_name = self.extract_string(node.children[0].additional_info)
        # if module_name in self.globals:
            # print('[WARNING] module "%s" is overwritten.' % module_name)
        # bytecode = self.create_bytecode()
        # members = [chnode.additional_info for chnode in node.children[0].children]
        # module = Module(module_name, members, bytecode)
        # self.globals[module_name] = module

    def visit_abort(self, node):
        self.dispatch(node.children[0])
        self.emit(code.ABORT)

    def visit_pass(self, node):
        self.emit(code.NOOP)

    def visit_return(self, node):
        self.dispatch(node.children[0])
        self.emit(code.RETURN_VALUE)

    def visit_unbound(self, node):
        identifier = node.children[0]
        self.dispatch(identifier)
        attrs = node.children[1:]
        for attr in attrs:
            self.dispatch(attr)
        self.codes[len(self.codes) - 2] = code.MAP_DELITEM

    def visit_assignment(self, node):
        left, right = node.children[0], node.children[1]
        self.dispatch(right)
        if len(left.children) == 1: # variable
            varname = left.children[0].additional_info
            index = self.register_var(varname)
            self.emit(code.STORE_VAR, index)
        else:
            identifier = left.children[0]
            self.dispatch(identifier)
            attrs = left.children[1:]
            for attr in attrs:
                self.dispatch(attr)
            self.codes[len(self.codes) - 2] = code.MAP_SETITEM

    def visit_do(self, node):
        begin = len(self.codes)
        jmp_true_indexes = []
        for guardcommand in node.children:
            self.dispatch(guardcommand.children[0])
            self.emit(code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(self.codes) - 1)
        self.emit(code.JMP, 0)
        end_index = len(self.codes) - 1
        jmp_done_indexes = []
        for index, guardcommand in enumerate(node.children):
            pos = len(self.codes)
            self.codes[jmp_true_indexes[index]] = pos
            self.visit_guardcommand_body(guardcommand.children[1])
            self.emit(code.JMP, begin)
            jmp_done_indexes.append(len(self.codes) - 1)
        self.codes[end_index] = len(self.codes)

    def visit_if(self, node):
        jmp_true_indexes = []
        for guardcommand in node.children:
            self.dispatch(guardcommand.children[0])
            self.emit(code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(self.codes) - 1)
        self.emit(code.EXIT, 1)
        jmp_done_indexes = []
        for index, guardcommand in enumerate(node.children):
            pos = len(self.codes)
            self.codes[jmp_true_indexes[index]] = pos
            self.visit_guardcommand_body(guardcommand.children[1])
            self.emit(code.JMP, 0)
            jmp_done_indexes.append(len(self.codes) - 1)
        end = len(self.codes)
        for index in jmp_done_indexes:
            self.codes[index] = end

    def visit_def(self, node):
        def_name = node.children[0]
        def_arguments = node.children[1]
        def_block = node.children[2]
        inner_ctx = Compiler()
        for arg in def_arguments.children:
            inner_ctx.register_var(arg.additional_info)
        outer_index = self.register_var(def_name.additional_info)
        inner_index = inner_ctx.register_var(def_name.additional_info)
        inner_ctx.visit_block(def_block)
        bc = inner_ctx.create_bytecode()
        fn = Function(bc)
        self.emit(code.LOAD_CONST, self.register_constant(fn))
        self.emit(code.STORE_VAR, self.register_var(def_name.additional_info))

    def visit_unary_expression(self, node):
        op, exp = node.children
        self.dispatch(exp)
        if op.additional_info == '!':
            self.emit(code.UNARY_NOT)
        elif op.additional_info == '+':
            self.emit(code.UNARY_POSITIVE)
        elif op.additional_info == '-':
            self.emit(code.UNARY_NEGATIVE)
        elif op.additional_info == '~':
            self.emit(code.UNARY_INVERT)


    def visit_binary_expression(self, node):
        left, op, right = node.children[0:3]
        op = op.additional_info
        if op == '&&':
            self.dispatch(left)
            self.emit(code.JUMP_IF_FALSE_OR_POP)
            pos = len(self.codes) - 1
            self.dispatch(right)
            self.codes[pos] = len(self.codes)
            return
        self.dispatch(right)
        self.dispatch(left)
        if op == '+':
            self.emit(code.BINARY_ADD)
        elif op == '-':
            self.emit(code.BINARY_SUB)
        elif op == '*':
            self.emit(code.BINARY_MUL)
        elif op == '/':
            self.emit(code.BINARY_DIV)
        elif op == '<<':
            self.emit(code.BINARY_LSHIFT)
        elif op == '>>':
            self.emit(code.BINARY_RSHIFT)
        elif op == '==':
            self.emit(code.BINARY_EQUAL)
        elif op == '<':
            self.emit(code.BINARY_LT)
        elif op == '>':
            self.emit(code.BINARY_GT)
        elif op == '<=':
            self.emit(code.BINARY_LE)
        elif op == '>=':
            self.emit(code.BINARY_GE)
        elif op == '!=':
            self.emit(code.BINARY_NE)
        elif op == '&':
            self.emit(code.BINARY_AND)
        elif op == '|':
            self.emit(code.BINARY_OR)
        elif op == '&^':
            self.emit(code.BINARY_XOR)
        elif op == '%':
            self.emit(code.BINARY_MOD)
        elif op == 'in':
            self.emit(code.MAP_HASITEM)

    def visit_in(self, node):
        elem, pool = node.children[0], node.children[1]
        self.dispatch(elem)
        self.dispatch(pool)
        self.emit(code.MAP_HASITEM)

    def visit_primary_expression(self, node):
        atom = node.children[0]
        attrs = node.children[1:]
        self.dispatch(atom)
        for attr in attrs:
            self.dispatch(attr)

    def visit_primary_expression_rest(self, node):
        self.emit(code.CALL_FUNC, 0)

    def visit_arguments(self, node):
        for arg in reversed(node.children):
            self.dispatch(arg)
        self.emit(code.CALL_FUNC, len(node.children))

    def visit_index_selector(self, node):
        self.dispatch(node.children[0])
        self.emit(code.MAP_GETITEM)

    def visit_identifier_selector(self, node):
        const = String(node.children[0].additional_info)
        self.emit(code.LOAD_CONST, self.register_constant(const))
        self.emit(code.MAP_GETITEM)

    def visit_array_literal(self, node):
        for chnode in node.children:
            self.dispatch(chnode)
        self.emit(code.BUILD_ARRAY, len(node.children))

    def visit_array_elements(self, node):
        self.dispatch(node)
        for el in node.children:
            self.dispatch(el)
        self.emit(code.BUILD_ARRAY, len(node.children))

    def visit_object_literal(self, node):
        self.emit(code.BUILD_MAP, len(node.children))
        for entry in node.children:
            self.dispatch(entry)

    def visit_object_identifier_entry(self, node):
        key, value = node.children[0], node.children[1]
        entry_key = String(key.additional_info)
        # key
        self.emit(code.LOAD_CONST, self.register_constant(entry_key))
        # value
        self.dispatch(value)
        # store key:value
        self.emit(code.STORE_MAP)

    def visit_object_string_entry(self, node):
        key, value = node.children[0], node.children[1]
        entry_key = String(self.extract_string(key.additional_info))
        # key
        self.emit(code.LOAD_CONST, self.register_constant(entry_key))
        # value
        self.dispatch(value)
        # store key:value
        self.emit(code.STORE_MAP)

    def visit_closure(self, node):
        inner_ctx = Compiler()
        for arg in node.children[0].children:
            inner_ctx.register_var(arg.additional_info)
        inner_ctx.dispatch(node.children[1])
        bc = inner_ctx.create_bytecode()
        w = Function(bc)
        self.emit(code.LOAD_CONST, self.register_constant(w))

    def visit_null_literal(self, node):
        self.emit(code.LOAD_CONST, self.register_constant(Null()))

    def visit_boolean_literal(self, node):
        boolean = node.children[0].additional_info == 'true'
        self.emit(code.LOAD_CONST, self.register_constant(Boolean(boolean)))

    def visit_block(self, node):
        for statement in node.children:
            self.dispatch(statement)

    def visit_guardcommand_body(self, node):
        for statement in node.children:
            self.dispatch(statement)

    def visit_or_test(self, node):
        pos = -1
        total = len(node.children)
        for index, and_test in enumerate(node.children):
            self.dispatch(and_test)
            if pos != -1:
                self.codes[pos] = len(self.codes)
            if index < total - 1:
                self.emit(code.JUMP_IF_TRUE_OR_POP)
            pos = len(self.codes) - 1

    def visit_and_test(self, node):
        pos = -1
        total = len(node.children)
        for index, not_test in enumerate(node.children):
            self.dispatch(not_test)
            if pos != -1:
                self.codes[pos] = len(self.codes)
            if index < total - 1:
                self.emit(code.JUMP_IF_FALSE_OR_POP)
            pos = len(self.codes) - 1

    def visit_not_test(self, node):
        self.dispatch(node.children[0])
        self.emit(code.NOT)

    def visit_comparison(self, node):
        left, op, right = node.children[0:3]
        op = op.additional_info
        self.dispatch(right)
        self.dispatch(left)
        if op == '==':
            self.emit(code.BINARY_EQUAL)
        elif op == '<':
            self.emit(code.BINARY_LT)
        elif op == '>':
            self.emit(code.BINARY_GT)
        elif op == '<=':
            self.emit(code.BINARY_LE)
        elif op == '>=':
            self.emit(code.BINARY_GE)
        elif op == '!=':
            self.emit(code.BINARY_NE)
        elif op == 'in':
            self.emit(code.MAP_HASITEM)

    def visit_or_expr(self, node):
        for xor_expr in node.children:
            self.dispatch(xor_expr)
            self.emit(code.BINARY_OR)

    def visit_xor_expr(self, node):
        for and_expr in node.children:
            self.dispatch(and_expr)
            self.emit(code.BINARY_XOR)

    def visit_and_expr(self, node):
        for shift_expr in node.children:
            self.dispatch(shift_expr)
            self.emit(code.BINARY_AND)

    def visit_shift_expr(self, node):
        self.dispatch(node.children[0])
        index = 1
        while index < len(node.children):
            shift_op, arith_expr = node.children[index], node.children[index + 1]
            shift_op = shift_op.additional_info
            self.dispatch(arith_expr)
            if shift_op == '<<':
                self.emit(code.BINARY_LSHIFT)
            elif shift_op == '>>':
                self.emit(code.BINARY_RSHIFT)
            else:
                raise NotImplementedError

    def visit_arith_expr(self, node):
        self.dispatch(node.children[0])
        index = 1
        while index < len(node.children):
            arith_op, term = node.children[index], node.children[index + 1]
            arith_op = arith_op.additional_info
            self.dispatch(term)
            if arith_op == '+':
                self.emit(code.BINARY_ADD)
            elif arith_op == '-':
                self.emit(code.BINARY_SUB)
            index = index + 2

    def visit_term(self, node):
        self.dispatch(node.children[0])
        index = 1
        while index < len(node.children):
            term_op, factor = node.children[index], node.children[index + 1]
            term_op = term_op.additional_info
            self.dispatch(factor)
            if term_op == '*':
                self.emit(code.BINARY_MUL)
            elif term_op == '/':
                self.emit(code.BINARY_DIV)
            elif term_op == '%':
                self.emit(code.BINARY_MOD)
            index = index + 2

    def visit_factor(self, node):
        self.dispatch(node.children[1])
        if node.children[0].additional_info == '-':
            self.emit(code.UNARY_NEGATIVE)
        elif node.children[0].additional_info == '~':
            self.emit(code.UNARY_INVERT)
        else:
            raise NotImplementedError
