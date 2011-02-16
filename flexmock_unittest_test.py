import sys
import unittest

from flexmock_test import TestFlexmockUnittest

if sys.version_info >= (2, 6):
  from flexmock_modern_test import TestFlexmockUnittestModern


if __name__ == '__main__':
  unittest.main()
