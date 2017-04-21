# -*- coding:utf-8 -*-
import sys
import os
import re
import logging
import fnmatch
import doctest
import unittest
import inspect


def rglob(rootdir, pattern):
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def modules():
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for f in rglob(basedir, '*.py'):
        if os.path.basename(f) == '__init__.py':
            yield os.path.dirname(f)[1 + len(basedir):].replace('/', '.')
        elif os.path.basename(f) != '__main__.py':
            yield f[1 + len(basedir):-3].replace('/', '.')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    suites = []
    for modname in modules():
        m = __import__(modname)
        try:
            suites.append(doctest.DocTestSuite(m, exclude_empty=False))
        except ValueError:
            logging.warn('cannot add doctests for module %s' % modname)
        for testClass in [m[1] for m in inspect.getmembers(m, inspect.isclass) if unittest.case.TestCase in inspect.getmro(m[1])]:
            suites.append(unittest.makeSuite(testClass))
    for testSuite in suites:
        unittest.TextTestRunner(verbosity=2).run(testSuite)
