import assert from "std/test";
import map from "std/fp";

def square (e) { return e * e; }
assert([1, 4, 9] == map(square, [1, 2, 3]), "Naming function should be applied to each element of array.");

assert([1, 4, 9] == map(def(e){return e*e;}, [1, 2, 3]), "Anonymous function should be applied to each element of array.");

