adder = {
    "closure": def(this) {
        this.integer = this.integer + 1;
        return this.integer;
    },
    "integer": 1
};
print(adder.closure());
print(adder.closure());
print(adder.integer);
