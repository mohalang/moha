# -*- coding: utf-8 -*-

class W_Root(object):
    def str(self):
        return ''

class Type(object):
    def __init__(self, typeval):
        self.typeval = typeval

class Null(W_Root):

    def str(self):
        return 'null'

    def __repr__(self):
        return 'null'

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
        char = self.strval[int(i.intval)]
        return String(char)
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
        return Null()
    def pop(self):
        return self.array.pop()
    def length(self):
        return Integer(len(self.array))
    def str(self):
        return '[%s]' % ','.join([a.str() for a in self.array])


class Integer(W_Root):

    def __init__(self, intval):
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

class CallableArgs(W_Root):

    def __init__(self, args):
        self.args = args

class Module(W_Root):

    def __init__(self, frame):
        self.frame = frame

    def get(self, varname):
        index = self.frame.bytecode.vars.keys_to_index[varname.str()]
        return self.frame.vars[index]
