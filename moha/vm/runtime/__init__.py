# -*- coding: utf-8 -*-

from rpython.rlib import jit

from moha.vm import code as Code
from moha.vm.grammar import parse_source
from moha.vm.objects import Function, Boolean, Null, Object, Array

def builtin_print(s):
    print(s.str())
    return Null()

def printable_loc(pc, code, bc):
    return "%d %d" % (pc, code[pc])

driver = jit.JitDriver(greens = ['pc', 'bytecode', 'bc'],
                       reds = ['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)

class Bytecode(object):
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
            _code = self.code[i]
            arg = self.code[i + 1]
            line = ""
            attrname = Code.pretty(_code)
            line += "%d %s %d" % (i, attrname, arg)
            if attrname == 'LOAD_CONST':
                line += " (%s)" % self.constants[arg]
            elif attrname == 'LOAD_VAR' or attrname == 'STORE_VAR':
                line += " (%s)" % self.vars.keys[arg]
            lines.append(line)
        return '\n'.join(lines)


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

def interpret_bytecode(frame, bc):
    bytecode = bc.code
    pc = 0
    frame_stack = []
    while True:
        driver.jit_merge_point(pc=pc, bytecode=bytecode, bc=bc, frame=frame)
        if pc >= len(bytecode):
            break
        c = bytecode[pc]
        arg = bytecode[pc + 1]
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
                    # builtin function
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
        elif c == Code.MAP_SETITEM:
            attr = frame.pop()
            obj = frame.pop()
            val = frame.pop()
            obj.set(attr, val)
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
                bytecode = bc.code
                for index, arg in enumerate(args):
                    frame.vars[index] = arg
                if len(args) != len(frame.vars):
                    frame.vars[len(args)] = Function(bc, None)
        elif c == Code.RETURN_VALUE:
            retval = frame.pop()
            frame, bc, pc = frame_stack.pop()
            bytecode = bc.code
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
                pval = Boolean(False)
            else:
                pval = Boolean(True)
            frame.push(pval)
        elif c == Code.ABORT:
            raise Exception("abort!");
        elif c == Code.NOOP:
            pass
