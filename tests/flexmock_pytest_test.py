from flexmock import MethodNotCalled
from flexmock import flexmock
from flexmock_test import assertRaises
import flexmock_test
import unittest


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodNotCalled, teardown_function)


class TestForPytest(flexmock_test.RegularClass):
  def teardown_method(self, x):
    pass

  def _tear_down(self):
    return self.teardown_method(None)

  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodNotCalled, self.teardown_method)


class TestUnittestClass(flexmock_test.TestFlexmockUnittest):
  def tearDown(self):
    pass

  def test_unittest(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodNotCalled, self.tearDown)
