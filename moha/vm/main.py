# -*- coding: utf-8 -*-

from moha.vm.runtime import init_sys, load_module

def interpret_source(executable, filename):
    sys = init_sys(executable)
    load_module(sys, filename)
