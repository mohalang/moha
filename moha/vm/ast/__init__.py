# -*- coding: utf-8 -*-

from moha.vm import code
from moha.vm.runtime import Bytecode
from moha.vm.objects import *
from moha.vm.utils import SortedSet, NOT_FOUND

class CompilerContext(object):
    def __init__(self):
        self.instructions = []
        self.constants = []
        self.vars = SortedSet()
        self.names = SortedSet()

    def register_constant(self, v):
        self.constants.append(v)
        return len(self.constants) - 1

    def register_name(self, name):
        return self.names.add(name)

    def lookup_name(self, name):
        return self.names.get(name)

    def register_var(self, name):
        return self.vars.add(name)

    def lookup_var(self, name):
        return self.vars.get(name)

    def emit(self, bc, arg=0):
        self.instructions.append(bc)
        self.instructions.append(arg)

    def create_bytecode(self):
        return Bytecode(self.instructions, self.constants[:], self.vars, self.names)



class AstNode(object):
    """ The abstract AST node
    """
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
            self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other

class AstEntry(AstNode):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def compile(self, ctx):
        self.key.compile(ctx)
        self.value.compile(ctx)

class AstAttribute(AstNode):

    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

    def compile(self, ctx):
        self.obj.compile(ctx)
        self.attr.compile(ctx)
        ctx.emit(code.MAP_GETITEM)

class AstObject(AstNode):

    def __init__(self, entries):
        self.entries = entries

    def compile(self, ctx):
        ctx.emit(code.BUILD_MAP, len(self.entries))
        for entry in self.entries:
            entry.compile(ctx)
            ctx.emit(code.STORE_MAP)

class AstArray(AstNode):
    def __init__(self, elems):
        self.elems = elems

    def compile(self, ctx):
        for elem in self.elems:
            elem.compile(ctx)
        ctx.emit(code.BUILD_ARRAY, len(self.elems))

class AstVariable(AstNode):

    def __init__(self, key):
        self.key = key

    def get_key(self):
        return self.key

    def str(self):
        return self.key

    def compile(self, ctx):
        if ctx.lookup_var(self.key) == NOT_FOUND:
            # not found, it's a global variable
            ctx.emit(code.LOAD_GLOBAL, ctx.register_name(self.key))
        else:
            ctx.emit(code.LOAD_VAR, ctx.register_var(self.key))


class AstConst(AstNode):

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def compile(self, ctx):
        ctx.emit(code.LOAD_CONST, ctx.register_constant(self.value))



class AstBlock(AstNode):
    def __init__(self, statements, pop=False):
        self.statements = statements
        self.pop = pop

    def compile(self, ctx):
        for statement in self.statements:
            statement.compile(ctx)
        if self.pop:
            ctx.emit(code.POP)

class AstReturn(AstNode):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(code.RETURN_VALUE, 0)

class AstCall(AstNode):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

    def compile(self, ctx):
        for arg in reversed(self.args):
            arg.compile(ctx)
        if isinstance(self.fn, AstAttribute):
            self.fn.obj.compile(ctx)
            argc = len(self.args) + 1
        else:
            argc = len(self.args)
        self.fn.compile(ctx)
        ctx.emit(code.CALL_FUNC, argc)


class AstAssignment(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        if isinstance(self.left, AstVariable):
            ctx.emit(code.STORE_VAR, ctx.register_var(self.left.get_key()))
        elif isinstance(self.left, AstAttribute):
            self.left.obj.compile(ctx)
            self.left.attr.compile(ctx)
            ctx.emit(code.MAP_SETITEM)


class AstClosure(AstNode):

    def __init__(self, arguments, block):
        self.arguments = arguments
        self.block = block

    def compile(self, ctx):
        inner_ctx = CompilerContext()
        for argument in self.arguments:
            inner_ctx.register_var(argument)
        self.block.compile(inner_ctx)
        bc = inner_ctx.create_bytecode()
        w = Function(bc)
        ctx.emit(code.LOAD_CONST, ctx.register_constant(w))

class AstDef(AstNode):
    def __init__(self, name, arguments, block):
        self.name = name
        self.arguments = arguments
        self.block = block

    def compile(self, ctx):
        inner_ctx = CompilerContext()
        # vars[0..arguments.len] is used for storing arguments
        for argument in self.arguments:
            inner_ctx.register_var(argument)
        outer_index = ctx.register_var(self.name)
        # vars[arguments.len] is used for function referrence itself
        inner_index = inner_ctx.register_var(self.name)

        self.block.compile(inner_ctx)
        bc = inner_ctx.create_bytecode()
        w = Function(bc)
        ctx.emit(code.LOAD_CONST, ctx.register_constant(w))
        ctx.emit(code.STORE_VAR, ctx.register_var(self.name))


class AstSub(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_SUB)

class AstNot(AstNode):

    def __init__(self, val):
        self.val = val

    def compile(self, ctx):
        self.val.compile(ctx)
        ctx.emit(code.NOT)

class AstOr(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(code.JUMP_IF_TRUE_OR_POP, 0)
        index = len(ctx.instructions) - 1
        self.right.compile(ctx)
        end = len(ctx.instructions)
        ctx.instructions[index] = end

class AstAnd(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(code.JUMP_IF_FALSE_OR_POP, 0)
        index = len(ctx.instructions) - 1
        self.right.compile(ctx)
        end = len(ctx.instructions)
        ctx.instructions[index] = end

class AstAdd(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_ADD)


class AstGuardCommand(AstNode):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

class AstIf(AstNode):
    def __init__(self, guardcommands):
        self.guardcommands = guardcommands

    def compile(self, ctx):
        jmp_true_indexes = []
        for guardcommand in self.guardcommands:
            guardcommand.condition.compile(ctx)
            ctx.emit(code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(ctx.instructions) - 1)
        ctx.emit(code.EXIT, 1)

        jmp_done_indexes = []
        for index, guardcommand in enumerate(self.guardcommands):
            pos = len(ctx.instructions)
            ctx.instructions[jmp_true_indexes[index]] = pos
            guardcommand.block.compile(ctx)
            ctx.emit(code.JMP, 0)
            jmp_done_indexes.append(len(ctx.instructions) - 1)

        end = len(ctx.instructions)
        for index in jmp_done_indexes:
            ctx.instructions[index] = end


class AstDo(AstNode):
    def __init__(self, guardcommands):
        self.guardcommands = guardcommands

    def compile(self, ctx):
        begin = len(ctx.instructions)

        jmp_true_indexes = []
        for guardcommand in self.guardcommands:
            guardcommand.condition.compile(ctx)
            ctx.emit(code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(ctx.instructions) - 1)

        ctx.emit(code.JMP, 0)
        end_index = len(ctx.instructions) - 1

        jmp_done_indexes = []
        for index, guardcommand in enumerate(self.guardcommands):
            pos = len(ctx.instructions)
            ctx.instructions[jmp_true_indexes[index]] = pos
            guardcommand.block.compile(ctx)
            ctx.emit(code.JMP, begin)
            jmp_done_indexes.append(len(ctx.instructions) - 1)

        ctx.instructions[end_index] = len(ctx.instructions)


class AstLt(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_LT)


class AstGt(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_GT)

class AstGe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_GE)

class AstLe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_LE)

class AstNe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_NE)

class AstEq(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(code.BINARY_EQUAL)

class Transformer(object):

    def visit_test(self, node):
        return self.visit_or_test(node.children[0])

    def visit_or_test(self, node):
        and_test = self.visit_and_test(node.children[0])
        or_test = and_test
        if len(node.children) > 1:
            star = node.children[1]
            while len(star.children) == 3:
                or_test = AstOr(or_test, self.visit_and_test(star.children[1]))
                star = star.children[2]
                if len(star.children) == 2:
                    or_test = AstOr(or_test, self.visit_and_test(star.children[1]))
                    break
        return or_test


    def visit_and_test(self, node):
        not_test = self.visit_not_test(node.children[0])
        and_test = not_test
        if len(node.children) > 1:
            star = node.children[1]
            while len(star.children) == 3:
                and_test = AstAnd(and_test, self.visit_not_test(star.children[1]))
                star = star.children[1]
                if len(star.children) == 2:
                    and_test = AstAnd(and_test, self.visit_not_test(star.children[1]))
                    break
        return and_test

    def visit_not_test(self, node):
        if len(node.children) == 2:
            return AstNot(self.visit_not_test(node.children[1]))
        else:
            return self.visit_comp(node.children[0])

    def visit_comp_op(self, node):
        return node.children[0].additional_info

    def visit_comp(self, node):
        expr = self.visit_expr(node.children[0])
        if len(node.children) == 1:
            return expr
        elif len(node.children) == 2:
            rest = node.children[1]
            right_expr = self.visit_expr(rest.children[1])
            op = self.visit_comp_op(rest.children[0])
            if op == '<':
                return AstLt(expr, right_expr)
            elif op == '>':
                return AstGt(expr, right_expr)
            elif op == '==':
                return AstEq(expr, right_expr)
            elif op == '<=':
                return AstLe(expr, right_expr)
            elif op == '>=':
                return AstGe(expr, right_expr)
            elif op == '!=':
                return AstNe(expr, right_expr)
        raise NotImplementedError


    def visit_func(self, node):
        if node.children[0].symbol == 'VARIABLE':
            return self.visit_VARIABLE(node.children[0])
        elif node.children[0].symbol == 'attr':
            return self.visit_attr(node.children[0])

    def visit_getattr(self, node):
        if node.children[0].additional_info == '.':
            attr = AstConst(String(node.children[1].additional_info))
        else:
            attr = self.visit_test(node.children[1])
        return attr

    def visit_getattr_plus(self, node, attrs):
        for child in node.children:
            if 'plus_symbol' in child.symbol:
                attr = self.visit_getattr(child.children[0])
                attrs.append(attr)
                self.visit_getattr_plus(child.children[0], attrs)
            if child.symbol == 'getattr':
                attrs.append(self.visit_getattr(child))
        return attrs

    def visit_attr(self, node):
        if node.children[0].symbol == 'func_call':
            obj = self.visit_func_call(node.children[0])
        elif node.children[0].symbol == 'object':
            obj = self.visit_object(node.children[0])
        elif node.children[0].symbol == 'VARIABLE':
            obj = self.visit_VARIABLE(node.children[0])
        else:
            raise NotImplementedError
        getattrs = self.visit_getattr_plus(node.children[1], [])
        attr = obj
        for getter in getattrs:
            attr = AstAttribute(attr, getter)
        return attr

    def visit_entries(self, node, entries):
        for child in node.children:
            if 'star_symbol' in child.symbol:
                entry = self.visit_entry(child.children[0])
                entries.append(entry)
                self.visit_entries(child.children[0], entries)
            elif child.symbol == 'entry':
                entry = self.visit_entry(child)
                entries.append(entry)
        return entries

    def visit_array(self, node):
        if len(node.children) == 2:
            elems = []
        else:
            elems = self.visit_callargs(node.children[1], [])
        return AstArray(elems)

    def visit_object(self, node):
        entries = self.visit_entries(node, [])
        return AstObject(entries)

    def visit_entry(self, node):
        key = self.visit_STRING(node.children[0])
        value = self.visit_entry_value(node.children[2])
        return AstEntry(key, value)

    def visit_entry_value(self, node):
        if node.children[0].symbol == 'expr':
            return self.visit_expr(node.children[0])
        elif node.children[0].symbol == 'closure':
            return self.visit_closure(node.children[0])
        raise NotImplementedError

    def visit_closure(self, node):
        if len(node.children) == 3:
            arguments = []
            block = self.visit_closure_rest(node.children[2])
        else:
            arguments = self.visit_args_star(node.children[2])
            block = self.visit_closure_rest(node.children[3])
        return AstClosure(arguments, block)

    def visit_closure_rest(self, node):
        statement_star = node.children[2]
        return AstBlock(self._grab_stmts(statement_star), pop=False)

    def visit_DECIMAL(self, node):
        return AstConst(Integer(int(node.additional_info)))

    def visit_FLOAT(self, node):
        return AstConst(Float(float(node.additional_info)))

    def visit_STRING(self, node):
        string = str(node.additional_info)
        begin = 1
        end = len(string) -1
        end = begin if end < 0 else end
        string = string[begin:end]
        return AstConst(String(string))

    def visit_VARIABLE(self, node):
        return AstVariable(node.additional_info)

    def visit_simple_expr(self, node):
        if node.children[0].symbol == 'func_call':
            return self.visit_func_call(node.children[0])
        elif node.children[0].symbol == 'atom':
            return self.visit_atom(node.children[0])
        elif node.children[0].symbol == 'object':
            return self.visit_object(node.children[0])
        elif node.children[0].symbol == 'attr':
            return self.visit_attr(node.children[0])
        elif node.children[0].symbol == 'array':
            return self.visit_array(node.children[0])
        raise NotImplementedError

    def visit_atom(self, node):
        if node.children[0].symbol == 'DECIMAL':
            return self.visit_DECIMAL(node.children[0])
        if node.children[0].symbol == 'FLOAT':
            return self.visit_FLOAT(node.children[0])
        if node.children[0].symbol == 'STRING':
            return self.visit_STRING(node.children[0])
        if node.children[0].symbol == 'VARIABLE':
            return self.visit_VARIABLE(node.children[0])
        if node.children[0].additional_info == 'true':
            return self.visit_BOOLEAN(node.children[0])
        if node.children[0].additional_info == 'false':
            return self.visit_BOOLEAN(node.children[0])

    def visit_BOOLEAN(self, node):
        if node.additional_info == 'true':
            return AstConst(Boolean(True))
        else:
            return AstConst(Boolean(False))

    def visit_func_call(self, node):
        func = self.visit_func(node.children[0])
        if len(node.children) == 3:
            args = []
        else:
            args = self.visit_callargs(node.children[2], [])
        return AstCall(func, args)

    def visit_callargs(self, node, args):
        for expr in node.children:
            if expr.symbol == 'test':
                arg = self.visit_test(expr)
                args.append(arg)
            elif expr.symbol == 'callargs':
                return self.visit_callargs(expr, args)
        return args

    def visit_expr(self, node):
        if len(node.children) == 1:
            return self.visit_simple_expr(node.children[0])
        elif node.children[1].additional_info == '+':
            return AstAdd(self.visit_simple_expr(node.children[0]), self.visit_expr(node.children[2]))
        elif node.children[1].additional_info == '-':
            return AstSub(self.visit_simple_expr(node.children[0]), self.visit_expr(node.children[2]))
        raise NotImplementedError()

    def visit_guardcommand(self, node):
        return AstGuardCommand(self.visit_test(node.children[1]),
                AstBlock(self._grab_stmts(node.children[4]), False))

    def visit_args_star(self, node):
        args = []
        for child in node.children:
            if child.symbol == 'args':
                args.append(child.children[0].additional_info)
        return args

    def visit_args(self, node):
        return self.visit_VARIABLE(node.children[0])

    def visit_statement(self, node):
        if len(node.children) == 4 and node.children[1].additional_info == "=":
            return AstAssignment(self.visit_func(node.children[0]), self.visit_test(node.children[2]))
        elif node.children[0].symbol == 'test':
            return AstBlock([self.visit_test(node.children[0])], pop=True)
        elif node.children[0].additional_info == 'if':
            return AstIf(self._grab_guardcommand(node.children[1]))
        elif node.children[0].additional_info == 'do':
            return AstDo(self._grab_guardcommand(node.children[1]))
        elif node.children[0].additional_info == 'def':
            name = node.children[1].additional_info
            args = node.children[3].children[0]
            arguments = []
            while len(args.children) == 3:
                variable = args.children[0]
                arguments.append(variable.additional_info)
                args = args.children[2]
                if len(args.children) == 1:
                    variable = args.children[0]
                    arguments.append(variable.additional_info)
                    break
            else:
                variable = args.children[0]
                arguments.append(variable.additional_info)
            if len(node.children) == 5:
                rest = node.children[4]
            else:
                rest = node.children[3]
            block = AstBlock(self._grab_stmts(rest.children[2]), pop=False)
            return AstDef(name, arguments, block)
        elif node.children[0].additional_info == 'return':
            return AstReturn(self.visit_test(node.children[1]))
        elif len(node.children) == 2 and node.children[1].additional_info == ";":
            return AstBlock([self.visit_test(node.children[0])], pop=True)
        raise NotImplementedError

    def _grab_guardcommand(self, star):
        stmts = []
        while len(star.children) == 2:
            stmts.append(self.visit_guardcommand(star.children[0]))
            star = star.children[1]
        stmts.append(self.visit_guardcommand(star.children[0]))
        return stmts

    def _grab_stmts(self, star):
        stmts = []
        while len(star.children) == 2:
            stmts.append(self.visit_statement(star.children[0]))
            star = star.children[1]
        stmts.append(self.visit_statement(star.children[0]))
        return stmts

    def visit_main(self, node):
        return AstBlock(self._grab_stmts(node.children[0]), pop=False)

transformer = Transformer()



