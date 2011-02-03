from flexmock import MethodNotCalled
from flexmock import flexmock_nose as flexmock
from flexmock_test import TestFlexmock
from flexmock_test import assertRaises
import sys


def test_module_level_test_for_nose():
  flexmock(foo='bar').should_receive('foo').once
  func_name = sys._getframe().f_code.co_name
  this_func = sys._getframe().f_globals[func_name]
  assertRaises(MethodNotCalled, this_func.teardown)
