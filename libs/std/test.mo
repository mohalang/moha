def assert(exp, message) {
    if (exp) {
        return exp;
    } (!exp) {
        abort message;
    }
}
