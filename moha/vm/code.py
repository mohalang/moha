#: do nothing.
NOOP = 14

EXIT = 8

#: remove tos
POP_TOP = 31
POP = 17

#: tos = -tos
UNARY_NEGATIVE = 32

#: tos = +tos
UNARY_POSITIVE = 46

#: tos = !tos
UNARY_NOT = 28

#: tos = ~tos
UNARY_INVERT = 33

BINARY_ADD = 3
BINARY_SUB = 4
BINARY_MUL = 34
BINARY_DIV = 35
BINARY_LSHIFT = 36
BINARY_RSHIFT = 37
BINARY_EQUAL = 7
BINARY_LT = 11
BINARY_GT = 12
BINARY_LE = 25
BINARY_GE = 26
BINARY_NE = 27
BINARY_AND = 38
BINARY_OR = 39
BINARY_XOR = 40
BINARY_MOD = 45

LOAD_VAR = 0
STORE_VAR = 1
LOAD_CONST = 2
LOAD_GLOBAL = 16

CALL_FUNC = 6
RETURN_VALUE = 5

NOT = 28
ABORT = 30
MAKE_FUNCTION = 13
CALL_CFFI = 15
LOAD_ATTR = 18

BUILD_ARRAY = 22
BUILD_MAP = 19
STORE_MAP = 20
MAP_GETITEM = 21
MAP_SETITEM = 23
MAP_HASITEM = 48
MAP_DELITEM = 49

JMP_TRUE = 9
JMP = 10
JUMP_IF_FALSE_OR_POP = 24
JUMP_IF_TRUE_OR_POP = 29
JUMP_RELATIVE_IF_FALSE = 47

IMPORT_MODULE = 41
IMPORT_MEMBER = 42
EXPORT_MODULE = 43
EXPORT_MEMBER = 44

_int_to_name = {value: key for key, value in globals().items() if key.isupper()}

def pretty(code):
    return _int_to_name[code]
