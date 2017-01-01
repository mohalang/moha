a = {"closure": def(this) { this.integer = this.integer + 1; return this.integer; }, "integer": 1};
print(a.closure());
print(a.integer);
print(a.nonexist);
