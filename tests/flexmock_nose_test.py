from flexmock import MethodCallError
from flexmock import flexmock
from flexmock import flexmock_teardown
from flexmock_test import assertRaises
from nose import with_setup
import flexmock_test
import unittest


def test_module_level():
  m = flexmock(mod=2)
  m.should_receive('mod').once
  assertRaises(MethodCallError, flexmock_teardown)


def test_module_level_generator():
  mock = flexmock(foo=lambda x, y: None, bar=lambda: None)
  mock.should_receive('bar').never  # change never to once to observe the failure
  for i in range(0, 3):
    yield mock.foo, i, i*3


class TestRegularClass(flexmock_test.RegularClass):

  def test_regular(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodCallError, flexmock_teardown)

  def test_class_level_generator_tests(self):
    mock = flexmock(foo=lambda a, b: a)
    mock.should_receive('bar').never  # change never to once to observe the failure
    for i in range(0, 3):
      yield mock.foo, i, i*3


class TestUnittestClass(flexmock_test.TestFlexmockUnittest):

  def test_unittest(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodCallError, flexmock_teardown)

