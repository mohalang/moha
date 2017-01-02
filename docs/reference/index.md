# The Moha Language Reference

- [Introduction](#introduction)
- [Notation](#notation)
- [Lexical analysis](#lexical-analysis)
    - [Ignore](#ignore)
    - [Comments](#comments)
    - [Tokens](#tokens)
    - [Identifiers](#identifiers)
    - [Keywords](#keywords)
    - [Operators](#operators)
    - [Delimiters](#delimiters)
    - [Literals](#literals)
        - [Integer Literals](#integer-literals)
        - [Boolean Literals](#boolean-literals)
        - [Floating Point Literals](#floating-point-literals)
        - [String Literals](#string-literals)
- [Execution Model](#execution-model)
    - [Block](#block)
    - [Constants](#constants)
    - [Variables](#variables)  
    - [Resolution](#resolution)
- [Data Models](#data-models)
    - [Null Type](#null-type)
    - [Boolean Type](#boolean-type)
    - [Integer Type](#integer-type)
    - [Float Type](#float-type)
    - [String Type](#string-type)
    - [Array Type](#array-type)
    - [Object Type](#object-type)
    - [Function Type](#function-type)
- [Expression](#expression)
    - [Atoms Expressions](#atoms-expressions)
    - [Variables Expressions](#variables-expressions)
    - [Selectors Expressions](#selectors-expressions)
    - [Array Expressions](#array-expressions)
    - [Object Expressions](#object-expressions)
    - [Primaries Expressions](#primaries-expressions)
    - [Bitwise Operations](#bitwise-operations-expression)
    - [Arithmetic Operations](#arithmetic-operations-expression)
    - [Comparison Operations](#comparison-operations-expression)
    - [Boolean Operations](#boolean-operations-expression)
    - [Closures](#closures-expression)
    - [Calls](#calls-expression)
    - [Operator Precedence](#operator-precedence)
- [Block](#block)
- [Simple Statements](#simple-statements)
    - [Empty Statements](#empty-statements)
    - [Expression Statements](#expression-statements)
    - [Assignment Statements](#assignment-statements)
    - [Return Statements](#return-statements)
    - [Pass Statements](#pass-statements)
    - [Abort Statements](#abort-statements)
- [Compound Statements](#compound-statements)
    - [If Statements](#if-statements)
    - [Do Statements](#do-statements)
    - [Def Statements](#def-statements)
- [Source File Organization](#source-file-organization)
    - [Package Naming](#package-naming)
    - [Export Package](#export-package)
    - [Import Package](#import-package)



## Introduction

This is a reference manual described the syntax for the Moha programming langugage.
For more information and other documents, please see
[mohalang.org](https://mohalang.org).

The design goal of Moha aims to be simple. The specification is terse
but regular. It's easy for developer to integrate code analysis tools.

## Notation

The syntax is specified using Extended Backus-Naur Form (EBNF).
The syntax file contains a sequence or rules. Every rule either describes a regular expression or a grammar rule. Example:

```
main: statements* [EOF];
```

[Ignore](#ignore) and [Comments](#comments) are ignored by the syntax.
Five categories of tokens form the vocabulary of Moha language.
They are [Identifiers](#identifiers), [Keywords](#keywords),
[Literals](#literals), [Operators](#operators) and [Delimiters](#delimiters).

See the full specification
in [Grammar Txt](https://github.com/mohalang/moha/blob/master/moha/vm/grammar/grammar.txt).

### Ignore

Whitespace, tab, and newline are ignored.

```
IGNORE: [ \t\n];
```

### Comments

A comment starts with `#` and stops at the end of the line.
A comment cannot start inside [string literals](#string-literals).
Comments are ignored by the syntax.

```
comment: "#.*"
```

### Identifiers

Identifiers (a.k.a. names) represent entities like variables, modules and types.

An identifier is a sequence of one or more letters and digits.
The first character in an identifier must be a letter.
Identifiers (also referred to as names) are described by the following lexical definitions.

```
identifier = letter { letter | unicode_digit };
```

Examples:

```
a
a1
_变量
server_⚙️
```

Identifiers are predeclared for builtin functions and types.

### Keywords

The following identifiers are used as reserved words, or keywords of the language, and cannot be used as ordinary identifiers.
They are:

- `true`
- `false`
- `null`
- `def`
- `if`
- `do`
- `import`
- `export`
- `as`
- `return`

### Operators

The following tokens are operators:

- `+`
- `-`
- `*`
- `/`
- `%`
- `<<`
- `>>`
- `&`
- `|`
- `~`
- `<`
- `>`
- `<=`
- `>=`
- `==`
- `!=`
- `&&`
- `||`
- `!`

### Delimiters

The following tokens are delimiters:

- `{`
- `}`
- `(`
- `)`
- `[`
- `]`
- `,`
- `.`
- `:`
- `;`
- `=`

### Literals

Literals are notations for constant values of some built-in types.

```
literal:  integer_literal | boolean_literal | float_literal | string_literal
```

#### Integer Literals

An integer literal is a sequence of digits representing an integer constant.
An optional prefix sets a non-decimal base: 0o or 0O for octal, 0b or 0B for binary, 0x or 0X for hexadecimal.
Integer literals are described by the following lexical definitions:

```
integer_literal: decimal_literal | octal_literal | hex_literal | bin_literal;
decimal_literal: "0|[1-9][0-9]*";
octal_literal: "0[oO][0-7]+";
hex_literal: "0[xX][0-9a-fA-F]+";
bin_literal: "0[bB][01]+";
```

Examples

```
42
0x93F2A32F
0b0100101000001011
0o413421
```

#### Boolean Literals

An boolean literal has only 2 forms: true of false.

```
boolean_literal: "(true)|(false)";
```

#### Floating Point Literals

A floating point literal is a decimal representation of a float constant.
Floating point literals are described by the following lexical definitions:

```
float_literal: "\-?(0|[1-9][0-9]*)(\.[0-9]+)([eE][\+\-]?[0-9]+)?";
```

#### String Literals

String literals are described by the following lexical definitions:

```
STRING: "\\"[^\\\\"]*\\"" | "'[^\\']*'";
```

## Execution Model

A Moha program is constructed from code blocks. A block is a sequence of
Moha statements executed one by one. The following are blocks:

- Guard Command Body
- Closure
- Function
- Module
- Script File

A code block is executed in an execution frame. A frame control code execution flow and procedure calls.

### Constants

There are integer constants, boolean constants, floating-point constants, and string constants. A constant means that it cannot be modified.

The constants in a code block will be registered in the frame.

### Variables

A variable is a name binding for holding a value within code blocks.

A variable's value is retrieved by referring to the variable in an expression.
A variable's value can be stored into context through [Assignment Statements](#assignment-statements),
[Function Declarations Statements](#function-declarations-statements),
and [Import Package](#import-package).

Elements in [Array](#array-expression) and [Object](#object-expression)
acts like variables.

The variables in a code block will be registered in the frame.

If a variable is bound in a block, it is a local variable of that block, unless declared as global.

Statement `del` unbind the variable and the value. The value will be
garbage-collected later automatically.

### Resolution

A scope defines the visibility of a variable within a block.

If a variable is defined in a function or closure block, its scope
is inside that block.

If a variable is defined in a module, its scope is inside that block, unless it is exported by `export` statement.

If a variable is not defined in a module, Moha will try to search variable
from builtin functions.

If a variable is not found at all, the program will abort execution.

## Data Models

Every Moha program is formed by some data types. They are Null, Boolean, Integer, Float, String, Array, Object, Function, Package, etc.

### Null Type

This is a single value. It is accessed through the built-in name null.
It represents nothing. It's false comparing with all other values except null.

### Boolean Type

Boolean type provides two single value: true or false.

### Integer Type

Integers represents numbers in an unlimited range.

### Float Type

Floats represents floating point numbers.

### String Type

A string is a sequence of characters that represent Unicode code points.

### Array Type

The items of an Array are arbitrary Moha value.

Example:

```
array = [null, true, false, 1, 1.0, 0xffff, {"key": "value"}];
```

### Object Type

The entries of an Object are a pair of String as key and artitrary Moha value as value.

Example:

```
obj = {"key": "value"};
```

In particular, the value can be an anonymous function take `this` as first
parameter. Inside function block, attribute getter syntax can be used to
retrieve or modify value through the key.

Example:

```
import "math";

def Point(x, y) {
  return {
    "x": x,
    "y": y,
    "distance": def(this, point) {
      return math.sqrt(
        math.pow(this.x - point.x, 2) + math.pow(this.y - point.y, 2)
      );
    },
    "move": def(this, x, y) {
      this.x = x;
      this.y = y;
    }
  }
}
```

### Function Type

A function declaration binds an identifier, the function name, to a function.
The function's signature declares parameters.
The function body is a statement list.

## Expression
### Atoms Expressions
### Variables Expressions
### Selectors Expressions
### Array Expressions
### Object Expressions
### Primaries Expressions
### Bitwise Operations
### Arithmetic Operations
### Comparison Operations
### Boolean Operations
### Closures
### Calls
### Operator Precedence
## Block
## Simple Statements
### Empty Statements
### Assignment Statements
### Return Statements
### Pass Statements
### Abort Statements
## Compound Statements
### If Statements
### Do Statements
### Def Statements
## Project Organization
### Package Naming
### Import Package
### Export Package
