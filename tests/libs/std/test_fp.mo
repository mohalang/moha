import assert from "std/test";
import map, filter from "std/fp";

def square (e) { return e * e; }
assert([1, 4, 9] == map(square, [1, 2, 3]), "Naming function should be applied to each element of array.");

assert([1, 4, 9] == map(def(e){return e*e;}, [1, 2, 3]), "Anonymous function should be applied to each element of array.");

assert([2, 4] == filter(def(e) { return (e % 2) == 0; }, [1, 2, 3, 4]), "Anonymous function should filter some elements in array.");
