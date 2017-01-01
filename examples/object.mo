a = {"integer": 1, "string": "string"};
b = {"variable": a, "closure": def () { print("hello"); }};
print(b.variable.integer);
b.closure();
