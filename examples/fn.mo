import map, filter from "std/fp";

def even(num) {
    return (num % 2) == 0;
}

def double(num) {
    return num * 2;
}

print(filter(even, [1, 2, 3, 4]));
print(map(double, [1, 2, 3, 4]));
print(map(def(el) {return el * 2;}, [1, 2, 3, 4]));
