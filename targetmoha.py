# -*- coding: utf-8 -*-

import sys

from rpython.rlib.streamio import open_file_as_stream
from rpython.jit.codewriter.policy import JitPolicy

from moha.vm.main import interpret_source
from moha.vm.runtime import init_sys, load_module


def main(argv):
    executable, filename = argv[0], argv[1]
    sys = init_sys(executable)
    load_module(sys, filename)
    return 0

def target(driver, args):
    driver.exe_name = 'bin/moha'
    return main, None

def jitpolicy(driver):
    return JitPolicy()

if __name__ == '__main__':
    main(sys.argv)
