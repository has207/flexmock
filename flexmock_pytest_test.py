from flexmock import MethodNotCalled
from flexmock import flexmock_pytest as flexmock
from flexmock_test import TestFlexmock
from flexmock_test import assertRaises


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodNotCalled, teardown_function)


class TestForPytest:
  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodNotCalled, self.teardown_method)
