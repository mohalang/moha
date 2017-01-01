# -*- coding: utf-8 -*-

import sys

from rpython.rlib.streamio import open_file_as_stream
from rpython.jit.codewriter.policy import JitPolicy

from moha.vm.main import interpret_source


def main(argv):
    f = open_file_as_stream(argv[1])
    data = f.readall()
    f.close()
    interpret_source(argv[1], data)
    return 0

def target(driver, args):
    driver.exe_name = 'bin/moha'
    return main, None

def jitpolicy(driver):
    return JitPolicy()

if __name__ == '__main__':
    main(sys.argv)
