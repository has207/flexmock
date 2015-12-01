import sys
import unittest

from flexmock_test import TestFlexmockUnittest

if sys.version_info >= (2, 6):
  from flexmock_modern_test import TestFlexmockUnittestModern

if sys.version_info >= (3,0):
  from flexmock_test import TestPy3Features

if __name__ == '__main__':
  unittest.main()
