# -*- coding: utf-8 -*-

NOT_FOUND = -1

class SortedSet(object):


    def __init__(self):
        self.keys = []
        self.keys_to_index = {}

    def get(self, key):
        if key in self.keys_to_index:
            return self.keys_to_index[key]
        else:
            return NOT_FOUND

    def add(self, key):
        try:
            return self.keys_to_index[key]
        except KeyError:
            self.keys.append(key)
            idx = len(self.keys) - 1
            self.keys_to_index[key] = idx
            return idx

    def size(self):
        return len(self.keys)
