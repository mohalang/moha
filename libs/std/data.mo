def set() {
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
