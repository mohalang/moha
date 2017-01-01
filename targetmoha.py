# -*- coding: utf-8 -*-

import os
from rpython.rlib import jit

class SortedSet(object):

    def __init__(self):
        self.keys = []
        self.keys_to_index = {}

    def get(self, key):
        if key in self.keys_to_index:
            return self.keys_to_index[key]
        else:
            return -1

    def add(self, key):
        try:
            return self.keys_to_index[key]
        except KeyError:
            self.keys.append(key)
            idx = len(self.keys) - 1
            self.keys_to_index[key] = idx
            return idx

    def size(self):
        return len(self.keys)

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
        return ByteCode(self.instructions, self.constants[:], self.vars, self.names)

class ByteCode(object):
    _immutable_fields_ = ['code', 'constants[*]', 'numvars']

    def __init__(self, code, constants, vars, names):
        self.code = code
        self.constants = constants
        self.vars = vars
        self.names = names
        self.numvars = self.vars.size()

    def dump(self):
        lines = []
        i = 0
        for i in range(0, len(self.code), 2):
            code = self.code[i]
            arg = self.code[i + 1]
            line = ""

            for attrname, attrval in Code.__dict__.iteritems():
                if attrname.isupper() and attrval == code:
                    line += "%d %s %d" % (i, attrname, arg)
                    if attrname == 'LOAD_CONST':
                        line += " (%s)" % self.constants[arg]
                    elif attrname == 'LOAD_VAR' or attrname == 'STORE_VAR':
                        line += " (%s)" % self.vars.keys[arg]
                    break
            lines.append(line)
        return '\n'.join(lines)

def get_env_path(name):
    val = os.getenv(name)
    return [] if not val  else val.split(':')

def interpret_source(filename, source):
    bnf_node = None
    try:
        bnf_node = _parse(source)
    except ParseError as e:
        print(e.nice_error_message(filename, source))
        return
    except LexerError as e:
        print(e.nice_error_message(filename))
        return
    ast = transformer.visit_main(bnf_node)
    c = CompilerContext()
    ast.compile(c)
    bc = c.create_bytecode()
    frame = Frame(bc)
    interpret_bytecode(frame, bc)
    return

def builtin_print(s):
    print(s.str())
    return Null()

def builtin_len(array):
    return Integer(array.length())

def builtin_push(array, elem):
    #array.push(elem)
    return Null()

def builtin_pop(array):
    #return array.pop()
    return Null()

def builtin_type(inst):
    return Type(type(inst))

class W_Root(object):
    def str(self):
        return ''

class Type(object):
    def __init__(self, typeval):
        self.typeval = typeval

class Null(W_Root):
    def __init__(self):
        self.nullval = None

class Boolean(W_Root):
    def __init__(self, boolval):
        self.boolval = boolval
    def str(self):
        return 'true' if self.boolval else 'false'
    def is_true(self):
        return self.boolval
true = Boolean(True)
false = Boolean(False)

def index_string(string, index):
    return string.index(index)
def length_string(string):
    return string.length()

class Object(W_Root):
    def __init__(self):
        self.dictionary = {}
    def build_map(self, data):
        size = len(data) / 2
        kv = {}
        for i in range(size):
            self.dictionary[data[i].str()] = data[i+1]
    def get(self, key):
        return self.dictionary[key.str()]
    def set(self, key, value):
        self.dictionary[key.str()] = value
    def str(self):
        return '{%s}' % ','.join(['%s:%s' % (key, value.str()) for key, value in self.dictionary.iteritems()])

class String(Object):
    def __init__(self, strval):
        self.strval = strval
        self.dictionary = {'index': Function(None, None, instancefunc_2=index_string),
                'length': Function(None, None, instancefunc_1=length_string),
                }
    def index(self, i):
        return String(self.strval[i.intval])
    def length(self):
        return Integer(len(self.strval))
    def eq(self, other):
        return Boolean(self.strval == other.strval)

    def __repr__(self):
        return "%s" % self.strval

    def str(self):
        return str(self.strval)


from rpython.tool.sourcetools import func_with_new_name

def push_array(array, elem):
    return array.push(elem)
def pop_array(array):
    return array.pop()
def index_array(array, index):
    return array.index(index)
def length_array(array):
    return array.length()

class Array(Object):
    def __init__(self):
        self.array = []
        self.dictionary = {'push': Function(None, None, instancefunc_2=push_array),
                'pop': Function(None, None, instancefunc_1=pop_array),
                'index': Function(None, None, instancefunc_2=index_array),
                'length': Function(None, None, instancefunc_1=length_array),
                }
    def get(self, i):
        if isinstance(i, Integer):
            return self.index(i)
        return self.dictionary[i.str()]
    def copy(self, array):
        for item in array:
            self.array.append(item)
    def index(self, i):
        return self.array[int(i.intval)]
    def push(self, elem):
        self.array.append(elem)
        return Null()
    def pop(self):
        return self.array.pop()
    def length(self):
        return Integer(len(self.array))
    def str(self):
        return '[%s]' % ','.join([a.str() for a in self.array])


class Integer(W_Root):
    def __init__(self, intval):
        assert(isinstance(intval, int))
        self.intval = intval

    def __repr__(self):
        return '%d' % self.intval

    def str(self):
        return self.__repr__()

    def neg(self):
        return Integer(-1 * self.intval)

    def add(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Integer(self.intval + other.intval)

    def lt(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean(self.intval < other.intval)
    def gt(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean(self.intval > other.intval)
    def eq(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean(self.intval == other.intval)

    def is_true(self):
        return self.intval != 0

    def str(self):
        return str(self.intval)


class Float(W_Root):
    def __init__(self, floatval):
        assert(isinstance(floatval, float))
        self.floatval = floatval

    def __repr__(self):
        return "%f" % self.floatval

    def str(self):
        return self.__repr__()

    def neg(self):
        return Float(-1 * self.floatval)

    def add(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Float(self.floatval + other.floatval)

    def lt(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Boolean(self.floatval < other.floatval)
    def gt(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Boolean(self.floatval > other.floatval)
    def eq(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Boolean(self.floatval == other.floatval)

    def str(self):
        return str(self.floatval)

class Function(W_Root):

    def __init__(self, bytecode=None, interpfunc=None, instancefunc_0=None, instancefunc_1=None, instancefunc_2=None, instancefunc_3=None):
        self.bytecode = bytecode
        self.interpfunc = interpfunc
        self.instancefunc_0 = instancefunc_0
        self.instancefunc_1 = instancefunc_1
        self.instancefunc_2 = instancefunc_2
        self.instancefunc_3 = instancefunc_3

    def __repr__(self):
        return '<func>'

    def str(self):
        return '<func>'

class Frame(object):
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, bc):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.valuestack = [None] * 5 # safe estimate!
        self.vars = [None] * bc.numvars
        self.valuestack_pos = 0

    def load_var(self, index):
        val = self.vars[index]
        self.push(val)

    def store_var(self, index):
        val = self.pop()
        self.vars[index] = val

    def push(self, v):
        pos = jit.hint(self.valuestack_pos, promote=True)
        assert pos >= 0
        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v

    def top(self):
        return self.valuestack[self.valuestack_pos]


class Code(object):
    LOAD_VAR = 0
    STORE_VAR = 1
    LOAD_CONST = 2
    BINARY_ADD = 3
    BINARY_SUB = 4
    RETURN_VALUE = 5
    CALL_FUNC = 6
    BINARY_EQUAL = 7
    EXIT = 8
    JMP_TRUE = 9
    JMP = 10
    BINARY_LT = 11
    BINARY_GT = 12
    MAKE_FUNCTION = 13
    NOOP = 14
    CALL_CFFI = 15
    LOAD_GLOBAL = 16
    POP = 17
    LOAD_ATTR = 18
    BUILD_MAP = 19
    STORE_MAP = 20
    MAP_GETITEM = 21
    BUILD_ARRAY = 22
    MAP_SETITEM = 23
    JUMP_IF_FALSE_OR_POP = 24
    BINARY_LE = 25
    BINARY_GE = 26
    BINARY_NE = 27
    NOT = 28
    JUMP_IF_TRUE_OR_POP = 29
    ABORT = 30

    @classmethod
    def pretty(cls, code):
        for attrname, attrval in cls.__dict__.iteritems():
            if attrname.isupper() and attrval == code:
                return attrname



def printable_loc(pc, code, bc):
    return "%d %d" % (pc, code[pc])

driver = jit.JitDriver(greens = ['pc', 'code', 'bc'],
                       reds = ['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)

def interpret_bytecode(frame, bc):
    code = bc.code
    pc = 0
    frame_stack = []
    while True:
        driver.jit_merge_point(pc=pc, code=code, bc=bc, frame=frame)
        if pc >= len(code):
            break
        c = code[pc]
        arg = code[pc + 1]
        pc += 2
        if c == Code.POP:
            frame.pop();
        elif c == Code.LOAD_GLOBAL:
            name = bc.names.keys[arg]
            idx = len(frame_stack) - 1
            while idx >= 0:
                var_idx = frame_stack[idx][1].vars.get(name)
                if var_idx == -1:
                    idx -= 1
                else:
                    frame.push(frame_stack[idx][0].vars[var_idx])
                    break
            else:
                if idx < 0:
                    frame.push(Function(None, name, None))
                else:
                    raise Exception('Unresolved variable: %s' % name)
        elif c == Code.LOAD_VAR:
            frame.load_var(arg)
        elif c == Code.STORE_VAR:
            frame.store_var(arg)
        elif c == Code.LOAD_CONST:
            frame.push(bc.constants[arg])
        elif c == Code.BUILD_MAP:
            map = Object()
            frame.push(map)
        elif c == Code.BUILD_ARRAY:
            array = Array()
            idx = 0
            args = []
            while idx < arg:
                elem = frame.pop()
                args.append(elem)
                idx += 1
            array.copy(reversed(args))
            frame.push(array)
        elif c == Code.MAP_GETITEM:
            attr = frame.pop()
            obj = frame.pop()
            val = obj.get(attr)
            frame.push(val)
        elif c == Code.STORE_MAP:
            value = frame.pop()
            key = frame.pop()
            map = frame.pop()
            map.set(key, value)
            frame.push(map)
        elif c == Code.CALL_FUNC:
            w_func_bc = frame.pop()

            idx = 0
            args = []
            while idx < arg:
                args.append(frame.pop())
                idx += 1

            if w_func_bc.instancefunc_0 or w_func_bc.instancefunc_1 or w_func_bc.instancefunc_2 or w_func_bc.instancefunc_3:
                # interp
                args.append(frame.pop())
                if len(args) == 0 and w_func_bc.instancefunc_0:
                    retval = w_func_bc.instancefunc_0()
                elif len(args) == 1 and w_func_bc.instancefunc_1:
                    retval = w_func_bc.instancefunc_1(args[0])
                elif len(args) == 2 and w_func_bc.instancefunc_2:
                    retval = w_func_bc.instancefunc_2(args[0], args[1])
                elif len(args) == 3 and w_func_bc.instancefunc_3:
                    retval = w_func_bc.instancefunc_3(args[0], args[1], args[2])
                else:
                    raise Exception("oops.")
                frame.push(retval)
            elif w_func_bc.interpfunc:
                func_interp = w_func_bc.interpfunc
                if func_interp == 'print':
                    retval = builtin_print(args[0])
                else:
                    raise Exception("Unresolved variable %s" % func_interp)
                frame.push(retval)
            else:
                func_bc = w_func_bc.bytecode
                frame_stack.append((frame, bc, pc))
                bc = func_bc
                frame = Frame(bc)
                pc = 0
                code = bc.code
                for index, arg in enumerate(args):
                    frame.vars[index] = arg
                if len(args) != len(frame.vars):
                    frame.vars[len(args)] = Function(bc, None)
            print bc.dump()
        elif c == Code.RETURN_VALUE:
            retval = frame.pop()
            frame, bc, pc = frame_stack.pop()
            code = bc.code
            frame.push(retval)
        elif c == Code.EXIT:
            pc = len(bc.code)
        elif c == Code.JMP_TRUE:
            if frame.pop().is_true():
                pc = arg
        elif c == Code.JUMP_IF_FALSE_OR_POP:
            top = frame.pop()
            if not top.is_true():
                pc = arg
                frame.push(top)
        elif c == Code.JUMP_IF_TRUE_OR_POP:
            top = frame.pop()
            if top.is_true():
                pc = arg
                frame.push(top)
        elif c == Code.JMP:
            pc = arg
        elif c == Code.BINARY_ADD:
            left = frame.pop()
            right = frame.pop()
            frame.push(left.add(right))
        elif c == Code.BINARY_SUB:
            left = frame.pop()
            right = frame.pop()
            frame.push(left.add(right.neg()))
        elif c == Code.BINARY_EQUAL:
            left = frame.pop()
            right = frame.pop()
            frame.push(left.eq(right))
        elif c == Code.BINARY_GT:
            left = frame.pop()
            right = frame.pop()
            frame.push(left.gt(right))
        elif c == Code.BINARY_LT:
            left = frame.pop()
            right = frame.pop()
            frame.push(left.lt(right))
        elif c == Code.BINARY_LE:
            left = frame.pop()
            right = frame.pop()
            frame.push(Boolean(left.lt(right).boolval or left.eq(right).boolval))
        elif c == Code.BINARY_GE:
            left = frame.pop()
            right = frame.pop()
            frame.push(Boolean(left.gt(right).boolval or left.eq(right).boolval))
        elif c == Code.BINARY_NE:
            left = frame.pop()
            right = frame.pop()
            frame.push(Boolean(not left.eq(right).boolval))
        elif c == Code.NOT:
            val = frame.pop()
            if val.is_true():
                pval = false
            else:
                pval = true
            frame.push(pval)
        elif c == Code.ABORT:
            raise Exception("abort!");
        elif c == Code.NOOP:
            #frame.pop()
            pass


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
        ctx.emit(Code.MAP_GETITEM)

class AstObject(AstNode):

    def __init__(self, entries):
        self.entries = entries

    def compile(self, ctx):
        ctx.emit(Code.BUILD_MAP, len(self.entries))
        for entry in self.entries:
            entry.compile(ctx)
            ctx.emit(Code.STORE_MAP)

class AstArray(AstNode):
    def __init__(self, elems):
        self.elems = elems

    def compile(self, ctx):
        for elem in self.elems:
            elem.compile(ctx)
        ctx.emit(Code.BUILD_ARRAY, len(self.elems))

class AstVariable(AstNode):

    def __init__(self, key):
        self.key = key

    def get_key(self):
        return self.key

    def str(self):
        return self.key

    def compile(self, ctx):
        if ctx.lookup_var(self.key) == -1:
            # not found, it's a global variable
            ctx.emit(Code.LOAD_GLOBAL, ctx.register_name(self.key))
        else:
            ctx.emit(Code.LOAD_VAR, ctx.register_var(self.key))


class AstConst(AstNode):

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def compile(self, ctx):
        ctx.emit(Code.LOAD_CONST, ctx.register_constant(self.value))



class AstBlock(AstNode):
    def __init__(self, statements, pop=False):
        self.statements = statements
        self.pop = pop

    def compile(self, ctx):
        for statement in self.statements:
            statement.compile(ctx)
        if self.pop:
            ctx.emit(Code.POP)

class AstReturn(AstNode):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(Code.RETURN_VALUE, 0)

class AstCall(AstNode):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

    def compile(self, ctx):
        for arg in reversed(self.args):
            arg.compile(ctx)
        if isinstance(self.fn, AstAttribute):
            self.fn.obj.compile(ctx)
        self.fn.compile(ctx)
        ctx.emit(Code.CALL_FUNC, len(self.args))


class AstAssignment(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        ctx.emit(Code.STORE_VAR, ctx.register_var(self.left.get_key()))


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
        ctx.emit(Code.LOAD_CONST, ctx.register_constant(w))

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
        ctx.emit(Code.LOAD_CONST, ctx.register_constant(w))
        ctx.emit(Code.STORE_VAR, ctx.register_var(self.name))


class AstSub(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_SUB)

class AstNot(AstNode):

    def __init__(self, val):
        self.val = val

    def compile(self, ctx):
        self.val.compile(ctx)
        ctx.emit(Code.NOT)

class AstOr(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(Code.JUMP_IF_TRUE_OR_POP, 0)
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
        ctx.emit(Code.JUMP_IF_FALSE_OR_POP, 0)
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
        ctx.emit(Code.BINARY_ADD)


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
            ctx.emit(Code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(ctx.instructions) - 1)
        ctx.emit(Code.EXIT, 1)

        jmp_done_indexes = []
        for index, guardcommand in enumerate(self.guardcommands):
            pos = len(ctx.instructions)
            ctx.instructions[jmp_true_indexes[index]] = pos
            guardcommand.block.compile(ctx)
            ctx.emit(Code.JMP, 0)
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
            ctx.emit(Code.JMP_TRUE, 0)
            jmp_true_indexes.append(len(ctx.instructions) - 1)

        ctx.emit(Code.JMP, 0)
        end_index = len(ctx.instructions) - 1

        jmp_done_indexes = []
        for index, guardcommand in enumerate(self.guardcommands):
            pos = len(ctx.instructions)
            ctx.instructions[jmp_true_indexes[index]] = pos
            guardcommand.block.compile(ctx)
            ctx.emit(Code.JMP, begin)
            jmp_done_indexes.append(len(ctx.instructions) - 1)

        ctx.instructions[end_index] = len(ctx.instructions)


class AstLt(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_LT)


class AstGt(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_GT)

class AstGe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_GE)

class AstLe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_LE)

class AstNe(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_NE)

class AstEq(AstNode):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.right.compile(ctx)
        self.left.compile(ctx)
        ctx.emit(Code.BINARY_EQUAL)


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
statement: test ";" | VARIABLE "=" test ";" | "return" test ";" | "do" guardcommand+ | "if" guardcommand+ | "def" VARIABLE "(" args* ")" "{" statement* "}";
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

from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.parsing import ParseError
from rpython.rlib.parsing.deterministic import LexerError
regexs, rules, ToAST = parse_ebnf(GRAMMAR)
_parse = make_parse_function(regexs, rules, eof=True)

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
        if node.children[0].symbol == 'test':
            return AstBlock([self.visit_test(node.children[0])], pop=True)
        if node.children[0].additional_info == 'if':
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
        elif node.children[1].additional_info == "=":
            return AstAssignment(self.visit_VARIABLE(node.children[0]), self.visit_test(node.children[2]))
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



### targetmoha
import sys
from rpython.rlib.streamio import open_file_as_stream
from rpython.jit.codewriter.policy import JitPolicy
def main(argv):
    f = open_file_as_stream(argv[1])
    data = f.readall()
    f.close()
    interpret_source(argv[1], data)
    return 0
def target(driver, args):
    driver.exe_name = 'bin/moha'
    return main, None
def jitpolicy(driver):
    return JitPolicy()
if __name__ == '__main__':
    main(sys.argv)
