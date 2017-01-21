# -*- coding: utf-8 -*-

from moha.vm import code as Code

class W_Root(object):
    def str(self):
        return ''
    def hash(self):
        return id(self)

class Type(object):
    def __init__(self, typeval):
        self.typeval = typeval

class Null(W_Root):

    def str(self):
        return 'null'

    def __repr__(self):
        return 'null'

    @classmethod
    def singleton(cls):
        return null

null = Null()

class Boolean(W_Root):
    def __init__(self, boolval):
        self.boolval = boolval
    def str(self):
        return 'true' if self.boolval else 'false'
    def eq(self, other):
        if not isinstance(other, Boolean):
            return Boolean.from_raw(False)
        return Boolean.from_raw(self.boolval == other.boolval)
    def is_true(self):
        return self.boolval
    @classmethod
    def from_raw(cls, b):
        if b:
            return true
        else:
            return false
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
    def has(self, key):
        return Boolean.from_raw(key.str() in self.dictionary)
    def delete(self, key):
        del self.dictionary[key.str()]
    def str(self):
        return '{%s}' % ','.join(['%s:%s' % (key, value.str()) for key, value in self.dictionary.iteritems()])

class String(Object):
    def __init__(self, strval):
        self.strval = strval
        self.dictionary = {'index': Function(None, None, instancefunc_2=index_string),
                'length': Function(None, None, instancefunc_1=length_string),
                }
    def index(self, i):
        char = self.strval[int(i.intval)]
        return String(char)
    def length(self):
        return Integer(len(self.strval))
    def eq(self, other):
        return Boolean.from_raw(self.strval == other.str())
    def add(self, other):
        return String(self.strval + other.str())

    def __repr__(self):
        return "%s" % self.strval

    def str(self):
        return str(self.strval)



def push_array(array, elem):
    return array.push(elem)
def pop_array(array):
    return array.pop()
def index_array(array, index):
    return array.index(index)
def length_array(array):
    return array.length()

class Array(Object):
    def __init__(self, array=None):
        self.array = array or []
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
        return Null.singleton()
    def pop(self):
        return self.array.pop()
    def has(self, elem):
        return Boolean.from_raw(elem in self.array)
    def eq(self, other):
        if not isinstance(other, Array):
            return Boolean.from_raw(False)
        if len(other.array) != len(self.array):
            return Boolean.from_raw(False)
        for index, elem in enumerate(self.array):
            if not elem.eq(other.array[index]):
                return Boolean.from_raw(False)
        return Boolean.from_raw(True)
    def length(self):
        return Integer(len(self.array))
    def str(self):
        return '[%s]' % ','.join([a.str() for a in self.array])
    def set(self, key, value):
        self.array[key.intval] = value


class Integer(W_Root):

    def __init__(self, intval):
        self.intval = int(intval)

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

    def mul(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Integer(self.intval * other.intval)

    def div(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Integer(self.intval / other.intval)

    def mod(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Integer(self.intval % other.intval)

    def lt(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean.from_raw(self.intval < other.intval)
    def gt(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean.from_raw(self.intval > other.intval)
    def eq(self, other):
        if not isinstance(other, Integer):
            raise Exception("wrong type")
        return Boolean.from_raw(self.intval == other.intval)

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
        return Boolean.from_raw(self.floatval < other.floatval)
    def gt(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Boolean.from_raw(self.floatval > other.floatval)
    def eq(self, other):
        if not isinstance(other, Float):
            raise Exception("wrong type")
        return Boolean.from_raw(self.floatval == other.floatval)

    def str(self):
        return str(self.floatval)

class Function(W_Root):

    def __init__(self, bytecode=None, interpfunc=None, instancefunc_0=None, instancefunc_1=None, instancefunc_2=None, instancefunc_3=None, obj=None):
        self.bytecode = bytecode
        self.interpfunc = interpfunc
        self.obj = obj
        self.instancefunc_0 = instancefunc_0
        self.instancefunc_1 = instancefunc_1
        self.instancefunc_2 = instancefunc_2
        self.instancefunc_3 = instancefunc_3

    def __repr__(self):
        return '<func>'

    def str(self):
        return '<func>'

class CallableArgs(W_Root):

    def __init__(self, args):
        self.args = args

class Module(W_Root):

    def __init__(self, frame):
        self.frame = frame

    def get(self, varname):
        index = self.frame.bytecode.vars.keys_to_index[varname.str()]
        return self.frame.vars[index]

class Sys(W_Root):

    def __init__(self):
        self.data = {}

    def get_cwd(self):
        return self.data['cwd']

    def set_cwd(self, path):
        self.data['cwd'] = path

    def set_executable(self, path):
        self.data['executable'] = path

    def get_executable(self):
        return self.data['executable']

    def set_env_path(self, path):
        self.data['env_path'] = path

    def get_env_path(self):
        return self.data['env_path']

    def get_bin_path(self):
        return '%s/bin' % self.data['env_path']

    def get_libs_path(self):
        env_path = self.get_env_path()
        return '%s/libs' % env_path

class Bytecode(object):
    _immutable_fields_ = ['code', 'constants[*]', 'numvars']

    def __init__(self, code, constants, vars, names):
        self.code = code
        self.constants = constants
        self.vars = vars
        self.names = names
        self.numvars = self.vars.size()

    def __repr__(self):
        return '<bytecode>'

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
