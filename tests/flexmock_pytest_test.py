from flexmock import MethodCallError
from flexmock import flexmock_teardown
from flexmock import flexmock
from flexmock_test import assertRaises
import flexmock_test
import unittest


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodCallError, flexmock_teardown)


class TestForPytest(flexmock_test.RegularClass):

  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodCallError, flexmock_teardown)


class TestUnittestClass(flexmock_test.TestFlexmockUnittest):

  def test_unittest(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodCallError, flexmock_teardown)
