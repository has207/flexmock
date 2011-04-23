from flexmock import MethodNotCalled
from flexmock import flexmock
from flexmock_test import assertRaises
import unittest


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodNotCalled, teardown_function)


class TestForPytest:
  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodNotCalled, self.teardown_method)


class TestUnittestClass(unittest.TestCase):
  def tearDown(self):
    pass

  def test_unittest(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodNotCalled, self.tearDown)
