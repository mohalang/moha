def list() {
    return {
        "_data": [],
        "_size": 0,
        "get": def(this, index) {
            if (index < this._size) {
                return this._data[index];
            }
        },
        "set": def(this, index, value) {
            if (index < this._size) {
                this._data[index] = value;
            }
        },
        "push": def(this, element) {
            this._data.push(element);
            this._size = this._size + 1;
            return element;
        },
        "pop": def(this) {
            if (this._size == 0) {
                return null;
            } (this._size != 0) {
                element = this._data[this._size - 1];
                this._data.pop();
                this._size = this._size - 1;
                return element;
            }
        },
        "unshift": def(this, element) {
            this._data.push(element);
            this._size = this._size + 1;
            previous = element;
            index = 0;
            do (index < this._size) {
                current = this._data[index];
                this._data[index] = previous;
                previous = current;
                index = index + 1;
            }
        },
        "shift": def(this) {
            if (this._size == 0) {
                return null;
            } (this._size != 0) {
                element = this._data[0];
                index = 0;
                do (index < this._size - 1) {
                    this._data[index] = this._data[index + 1];
                    index = index + 1;
                }
                this._data.pop();
                this._size = this._size - 1;
                return element;
            }
        },
        "size": def(this) {
            return this._size;
        },
        "contains": def(this, element) {
            index = 0;
            do (index < this._size) {
                contains = (element == this._data[index]);
                if (contains) { return true; } (!contains) { pass; }
                index = index + 1;
            }
            return false;
        },
        "equal": def(this, other) {
            same_length = this._size == other.length();
            if (!same_length) {
                return false;
            } (same_length) {
                index = 0;
                do (index < this._size) {
                    same_element = this.get(index) == other.get(index);
                    if (!same_element) { return false; } (same_element) { pass; }
                    index = index + 1;
                }
                return true;
            }
        },
        "not_found": 0 - 1,
        "index_of": def(this, element) {
            index = 0;
            do (index < this._size) {
                equal = element == this._data[index];
                if (equal) { return index; } (!equal) { pass; }
                index = index + 1;
            }
            return this.not_found;
        },
        "last_index_of": def(this, element) {
            index = this._size - 1;
            do (index >= 0) {
                equal = element == this._data[index];
                if (equal) { return index; } (!equal) { pass; }
                index = index - 1;
            }
            return this.not_found;
        },
        "is_empty": def(this) {
            return this._size == 0;
        },
        "clear": def(this) {
            this._size = 0;
            del this._data;
            this._data = [];
        },
        "slice": def(this, left, right) {
            if (left < this._size && right < this._size) {
                range = list();
                do (left <= right) {
                    range.push(this._data[left]);
                    left = left + 1;
                }
                return range;
            }
        },
        "each": def(this, block) {
            index = 0;
            do (index < this._size) {
                block(this._data[index]);
                index = index + 1;
            }
        },
        "to_string": def(this) {
            # FIXME: improve my performance.
            s = "";
            index = 0;
            do (index < this._size - 1) {
                s = s + str(this._data[index]);
                s = s + ",";
                index = index + 1;
            }
            s = s + str(this._data[index]);
            return s;
        }
    };
}

def set() {
    # Data Structure: Hash Set
    # method: add
    # method: remove
    # method: size
    # method: has
    return {
        "_data": {},
        "_size": 0,
        "add": def(this, element) {
            has = element in this._data;
            if (has) {
                pass;
            } (!has) {
                this._size = this._size + 1;
                this._data[element] = 0;
            }
        },
        "remove": def(this, element) {
            has = element in this._data;
            if (has) {
                this._size = this._size - 1;
                del this._data[element];
            } (!has) {
                pass;
            }
        },
        "size": def(this, element) {
            return this._size;
        },
        "has": def(this, element) {
            return (element in this._data);
        }
    };
}
