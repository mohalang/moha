# -*- coding: utf-8 -*-

import sys

from rpython.rlib.streamio import open_file_as_stream
from rpython.jit.codewriter.policy import JitPolicy

from moha.vm.main import interpret_source


def main(argv):
    interpret_source(argv[0], argv[1])
    return 0

def target(driver, args):
    driver.exe_name = 'bin/moha'
    return main, None

def jitpolicy(driver):
    return JitPolicy()

if __name__ == '__main__':
    main(sys.argv)
