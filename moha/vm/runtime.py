# -*- coding: utf-8 -*-

import os
from rpython.rlib import jit
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib.streamio import open_file_as_stream

from moha.vm import code as Code
from moha.vm.objects import Function, Boolean, Null, Object, Array, Module, Sys, Bytecode, String
from moha.vm.grammar.v0_2_0 import parse_source
from moha.vm.compiler import Compiler

def builtin_str(s):
    return String(s.str())

def builtin_print(s):
    print(s.str())
    return Null.singleton()

def builtin_id(s):
    return Integer(s.hash())

def printable_loc(pc, code, bc):
    return "%d %d" % (pc, code[pc])

driver = jit.JitDriver(greens = ['pc', 'bytecode', 'bc'],
                       reds = ['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)


class Frame(object):
    #_virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, bc):
        #self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.bytecode = bc
        self.vars = [None] * bc.numvars
        self.valuestack = []

    def load_var(self, index):
        val = self.vars[index]
        self.push(val)

    def store_var(self, index):
        val = self.pop()
        self.vars[index] = val

    def push(self, v):
        self.valuestack.append(v)

    def pop(self):
        return self.valuestack.pop()

    def top(self):
        return self.valuestack[len(self.valuestack) - 1] if len(self.valuestack) >= 1 else None

def interpret_bytecode(sys, filename, frame, bc):
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
        # print pc - 2, Code.pretty(c), arg
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
        elif c == Code.DEL_VAR:
            pass
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
        elif c == Code.MAP_HASITEM:
            left = frame.pop()
            right = frame.pop()
            is_in = right.has(left)
            frame.push(is_in)
        elif c == Code.MAP_GETITEM:
            attr = frame.pop()
            obj = frame.pop()
            val = obj.get(attr)
            if isinstance(val, Function):
                val.obj = obj
            frame.push(val)
        elif c == Code.MAP_SETITEM:
            attr = frame.pop()
            obj = frame.pop()
            val = frame.pop()
            obj.set(attr, val)
        elif c == Code.MAP_DELITEM:
            attr = frame.pop()
            obj = frame.pop()
            obj.delete(attr)
        elif c == Code.STORE_MAP:
            value = frame.pop()
            key = frame.pop()
            map = frame.pop()
            map.set(key, value)
            frame.push(map)
        elif c == Code.CALL_FUNC:
            idx = 0
            args = []
            while idx < arg:
                args.append(frame.pop())
                idx += 1

            w_func_bc = frame.pop()
            if w_func_bc.obj:
                args = [w_func_bc.obj] + args

            if w_func_bc.instancefunc_0 or w_func_bc.instancefunc_1 or w_func_bc.instancefunc_2 or w_func_bc.instancefunc_3:
                # interp
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
                elif func_interp == 'str':
                    retval = builtin_str(args[0])
                elif func_interp == 'id':
                    retval = builtin_id(args[0])
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
                if len(args) != len(frame.vars): # recursion
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
            right = frame.pop()
            left = frame.pop()
            frame.push(left.add(right))
        elif c == Code.BINARY_SUB:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.add(right.neg()))
        elif c == Code.BINARY_MUL:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.mul(right))
        elif c == Code.BINARY_DIV:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.div(right))
        elif c == Code.BINARY_MOD:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.mod(right))
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
            frame.push(Boolean.from_raw(left.lt(right).boolval or left.eq(right).boolval))
        elif c == Code.BINARY_GE:
            left = frame.pop()
            right = frame.pop()
            frame.push(Boolean.from_raw(left.gt(right).boolval or left.eq(right).boolval))
        elif c == Code.BINARY_NE:
            left = frame.pop()
            right = frame.pop()
            frame.push(Boolean.from_raw(not left.eq(right).boolval))
        elif c == Code.NOT:
            val = frame.pop()
            if val.is_true():
                pval = Boolean.from_raw(False)
            else:
                pval = Boolean.from_raw(True)
            frame.push(pval)
        elif c == Code.ABORT:
            raise Exception("abort!");
        elif c == Code.NOOP:
            pass
        elif c == Code.IMPORT_MODULE:
            module_name = frame.pop()
            path = find_module(sys, filename, module_name)
            module = load_module(sys, path)
            frame.push(module)
        elif c == Code.IMPORT_MEMBER:
            member_name = frame.pop()
            module = frame.pop()
            member = module.get(member_name)
            frame.vars[arg] = member
            frame.push(module)


def find_module(sys, filename, module_name):
    if module_name.strval.startswith('./'):
        idx = len(filename) - 1
        while idx >= 0 and filename[idx] != '/':
            idx -= 1
        cwd = filename[0:idx] if idx >= 0 else filename
        return '%s/%s.mo' % (cwd, module_name.strval[2:len(module_name.strval)])
    else:
        return '%s/%s.mo' % (sys.get_libs_path(), module_name.strval)

def read_source(filename):
    f = open_file_as_stream(filename)
    source = f.readall()
    f.close()
    sources = source.splitlines()
    sources = [line for line in sources if not line.strip().startswith('#')]
    source = '\n'.join(sources)
    return source

def compile_source(filename, source):
    bnf_node = parse_source(filename, source)
    if not bnf_node:
        raise Exception("We cannot get source bnf node.")
        return

    compiler = Compiler()
    compiler.dispatch(bnf_node)
    bc = compiler.create_bytecode()
    return Frame(bc)

def init_sys(executable):
    sys = Sys()
    if we_are_translated():
        # XXX: should be at installed dir.
        sys.set_env_path(os.getcwd())
        sys.set_executable(executable)
        sys.set_cwd(os.getcwd())
    else:
        sys.set_env_path(os.getcwd())
        sys.set_executable(os.getcwd() + executable)
        sys.set_cwd(os.getcwd())
    return sys

def load_module(sys, filename):
    source = read_source(filename)
    frame = compile_source(filename, source)
    interpret_bytecode(sys, filename, frame, frame.bytecode)
    return Module(frame)
