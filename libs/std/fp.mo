def map(fn, array) {
    index = 0;
    length = array.length();
    result = [];
    do (index < length) {
        elem = array.index(index);
        elem = fn(elem);
        result.push(elem);
        index = index + 1;
    }
    return result;
}

def filter(fn, array) {
    index = 0;
    length = array.length();
    result = [];
    do (index < length) {
        elem = array.index(index);
        flag = fn(elem);
        if (flag) {
            result.push(elem);
        } (!flag) {
            pass;
        }
        index = index + 1;
    }
    return result;
}
