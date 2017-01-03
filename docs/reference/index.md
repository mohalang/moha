# The Moha Language Reference

- [Introduction](#introduction)
- [Notation](#notation)
- [Lexical Analysis](#lexical-analysis)
    - [Ignore](#ignore)
    - [Comments](#comments)
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
    - [Parenthesized Form](#parenthesized-form)
    - [Atoms Expressions](#atoms-expressions)
    - [Variables Expressions](#variables-expressions)
    - [Array Expressions](#array-expressions)
    - [Object Expressions](#object-expressions)
    - [Primaries Expressions](#primaries-expressions)
    - [Calls](#calls-expression)
- [Block](#block)
- [Simple Statements](#simple-statements)
    - [Pass Statements](#pass-statements)
    - [Abort Statements](#abort-statements)
    - [Assignment Statements](#assignment-statements)
    - [Return Statements](#return-statements)
    - [Expression Statements](#expression-statements)
- [Compound Statements](#compound-statements)
    - [If Statements](#if-statements)
    - [Do Statements](#do-statements)
    - [Def Statements](#def-statements)
- [Organization](#organization)
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
The syntax file contains a sequence or rules. Every rule either describes a regular expression or a grammar rule.

Grammar:

    main: export? import* statement* [EOF];

[Ignore](#ignore) and [Comments](#comments) are ignored by the syntax.
Five categories of tokens form the vocabulary of Moha language.
They are [Identifiers](#identifiers), [Keywords](#keywords),
[Literals](#literals), [Operators](#operators) and [Delimiters](#delimiters).

See the full specification
in [Grammar Txt](https://github.com/mohalang/moha/blob/master/moha/vm/grammar/v0_2_0.txt).

## Lexical Analysis

### Ignore

Whitespace, tab, and newline are ignored.

Grammar:

    IGNORE: [ \t\n];

### Comments

A comment starts with `#` and stops at the end of the line.
A comment cannot start inside [string literals](#string-literals).
Comments are ignored by the syntax.

Grammar:

    comment: "#.*"

### Identifiers

Identifiers (a.k.a. names) represent entities like variables, modules and types.

An identifier is a sequence of one or more letters and digits.
The first character in an identifier must be a letter.
Identifiers (also referred to as names) are described by the following lexical definitions.

Grammar:

    IDENTIFIER: "[a-zA-Z_][a-zA-Z0-9_]*";

Examples:

    tmp
    filename
    _variable
    serverConfiguration

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

Grammar:

    literal: "true" | "false" | integer_literal | FLOAT_LITERAL | STRING_LITERAL;

#### Integer Literals

An integer literal is a sequence of digits representing an integer constant.
An optional prefix sets a non-decimal base: 0o or 0O for octal, 0b or 0B for binary, 0x or 0X for hexadecimal.
Integer literals are described by the following lexical definitions:

Grammar:

    integer_literal: DECIMAL_LITERAL | OCTAL_LITERAL | HEX_LITERAL | BIN_LITERAL;
    DECIMAL_LITERAL: "0|[1-9][0-9]*";
    OCTAL_LITERAL: "0[oO][0-7]+";
    HEX_LITERAL: "0[xX][0-9a-fA-F]+";
    BIN_LITERAL: "0[bB][0-1]+";

Examples

    42
    0x93F2A32F
    0b0100101000001011
    0O413421

#### Boolean Literals

A Boolean literal is either a `true` or `false` value.

#### Floating Point Literals

A floating point literal is a decimal representation of a float constant.
Floating point literals are described by the following lexical definitions:

Grammar:

    FLOAT_LITERAL: "\-?(0|[1-9][0-9]*)(\.[0-9]+)([eE][\+\-]?[0-9]+)?";

#### String Literals

String literals are described by the following lexical definitions:

Grammar:

    STRING_LITERAL: "\\"[^\\\\"]*\\"" | "'[^\\']*'";

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

    array = [null, true, false, 1, 1.0, 0xffff, {"key": "value"}];

### Object Type

The entries of an Object are a pair of String as key and artitrary Moha value as value.

Example:

    obj = {"key": "value"};

In particular, the value can be an anonymous function take `this` as first
parameter. Inside function block, attribute getter syntax can be used to
retrieve or modify value through the key.

Example:

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

### Function Type

A function declaration binds an identifier, the function name, to a function.
The function's signature declares parameters.
The function body is a statement list.

### Module Type

A module is formed by module members.
These module members can be accessed by selector grammar.

## Expression

An expression specifies the evaluation of a value.

Grammar:

    expression: unary_expression | binary_expression;
    unary_expression: primary_expression | unary_op unary_expression;
    binary_expression: expression binary_op expression;
    unary_op: "+" | "-" | "!";
    binary_op: "||" | "&&" | "==" | "!=" | "<" | "<=" | ">" | ">=" | "+" | "-" | "|" | "^" | "*" | "/" | "%" | "<<" | ">>" | "&" | "&^";

### Parenthesized Form

    parenthesized_form: ["("] <expression> [")"];

### Atoms Expressions

    atom: literal | IDENTIFIER | array_literal | object_literal | parenthesized_form;

### Variables Expressions

See section [Identifiers](#identifiers) for lexical definition.
See section [Variables](#variables) and [Resolution](#resolution) for binding and resolution.

### Array Expressions

Grammar:

    array_literal: "[" array_elements? "]";
    array_elements: expression ([","] expression)* ","?;

Example:

    // array without elements
    []

    // array contains numbers
    [1, 2, 3, 4]
    [1, 2, 3, 4, ]

    // array contains hybird types values
    [1, "string", true, null, ]

### Object Expressions

Grammar:

    object_literal: "{" object_entries? "}";
    object_entries: object_entry ([","] object_entry)* ","?;
    object_entry: object_identifier_entry | object_string_entry;
    object_identifier_entry: IDENTIFIER ":" object_entry_value;
    object_string_entry: STRING_LITERAL ":" object_entry_value;
    object_entry_value: closure | expression;
    closure: "def" ["("] args [")"] block;
    args: IDENTIFIER [","] args | IDENTIFIER;

Example:

    // an object contains one entry
    {"integer": 1}

    // an object contains closure
    {
        "integer": 1,
            "add_integer": def (this) {
                this.integer = this.integer + 1;
            }
    }

### Primaries Expressions

Grammar:

    primary_expression: atom primary_expression_rest*;
    primary_expression_rest: selector | arguments;

    selector: <identifier_selector> | <index_selector>;
    identifier_selector: ["."] IDENTIFIER;
    index_selector: ["["] expression ["]"];

    arguments: ["("] (expressions ","?)? [")"];

    expressions: expression ([","] <expression>)*;

## Statements

Grammar:

    statement: compound_statement | simple_statement [";"];

## Simple Statements

Simple statements are minimal execution instruction.

Grammar:

    simple_statement: pass | abort | return | assignment | expression ;

### Pass Statements

Pass statements do nothing.

Grammar:

    pass: "pass";

### Abort Statements

Abort statements would terminate the execution of the program.
It's unlike raise Exception or Error in other language.
There is no way for Moha to `catch` these exceptions and then recovery execution.

Grammar:

    abort: "abort" expression;

### Assignment Statements

Assignment statements bind the value to the identifier under a certain scope.

Grammar:

    assignment: IDENTIFIER selector* ["="] expression;
    selector: <identifier_selector> | <index_selector>;
    identifier_selector: ["."] IDENTIFIER;
    index_selector: ["["] expression ["]"];

Example:

    // assign to a variable
    num = 1;

    // assign to attribute of an object
    obj.integer = 1;

### Return Statements

A "return" statement in a function F terminates the execution of F.
The returned expression could be omitted.

```
return: "return" expression*;
```

## Compound Statements

There are 4 compound statements: block, if, do, def.

    compound_statement: block | if | do | def;

### Block Statements

Block statements are composed by a sequence of simple statements, wrapped by "{" and "}".

Grammar:

    block: "{" statement* "}";


A block creates a variable scope. Any variables defined inside this scope is invisible from outside.

Example:

```moha
{
    a = 1;
    print(a);
}
print(a); // `a` is an unresolved variable here.
```

### If Statements

`If` statements are composed by several guardcommands.
`If` statements would iterate guardcommands until a truthy guardcommand expression found.
`If` statements would abort execution if no truthy guardcommand found.
Guardcommands specify the the conditional execution of block according to the value of expression.
`If` statements complete its execution after all statements in one of the guardcommand's block were executed.

Grammar:

    if: "if" guardcommand+;
    guardcommand: "(" expression ")" block;

Good Example:

    a = input_number();
    if (a > 1) { print("lt"); } (a < 1) { print("lt"); } (a == 1) { print("eq"); }

Bad Example:

    if (false) { print("failed"); } // abort!

### Do Statements

`Do` statements are composed by several guardcommands.
`Do` statements would iterate guardcommands until a truthy guardcommand expression found.
`Do` statements would repeat iteration execution until no truthy guardcommand found.

Grammar:

    do: "do" guardcommand+;

Example:

    a = 0
    do (a < 10) { a = a + 1; }
    print(a);

Infinite loop:

    do (true) { print("yes!"); }
    print("unreachable here.");

### Def Statements

`Def` statements specify user-defined function objects.
The function definition does not execute the function body; this gets executed only when the function is called.

Grammar:

    def: "def" IDENTIFIER "(" args? ")" block;

Example:

    def add_zero(num) {
        return num + 0;
    }

## Organization

Moha programs are organized by import and export.

A package is exposed to other modules by `export` members to them.
Other modules can `import` either entire module or members from modules.
Members can be identifiers of variables and functions.

Export statement should be written as the first statement of the source file.
Export statement should only appear once at most.
Export statement could be omitted if the source file is served as a entry script.

Import statement should follow export statement and be written before any other statements.

Example:

    export * as "http";

    import request from "http/request";

    def get(url, params, headers) {
        return request('get', url, params, headers);
    }

### Export Package

Grammar:

    export: export_all_members_as_module [";"] | export_selected_members_as_module [";"];
    export_all_members_as_module: "export" "*" "as" STRING_LITERAL;
    export_selected_members_as_module: "export" export_members "as" STRING_LITERAL;

Example:

    // export all members as package
    export * as "http";

    // export selected members as package
    export get, post, put, delete as "http";

### Import Package

Grammar:

    import: import_module [";"] | import_members_from_module [";"];
    import_module: "import" STRING_LITERAL;
    import_members_from_module: "import" import_members "from" STRING_LITERAL;
    import_members: (IDENTIFIER ",")* IDENTIFIER;

Example:

    // import_module
    import "io";

    // import_members_from_module
    import print from "io";
    import print, open from "io";
