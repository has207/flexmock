from flexmock import MethodNotCalled
from flexmock import flexmock
from flexmock_test import assertRaises

import flexmock_test


class TestPytestUnittestClass(flexmock_test.TestFlexmockUnittest):
  pass


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodNotCalled, teardown_function)


class TestForPytest:
  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodNotCalled, self.teardown_method)
