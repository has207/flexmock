from flexmock import MethodCallError
from flexmock import flexmock_teardown
from flexmock_test import assertRaises
import flexmock
import flexmock_test
import unittest
import pytest


def test_module_level_test_for_pytest():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodCallError, flexmock_teardown)


@pytest.fixture()
def runtest_hook_fixture():
  return flexmock(foo='bar').should_receive('foo').once.mock()

def test_runtest_hook_with_fixture_for_pytest(runtest_hook_fixture):
  runtest_hook_fixture.foo()


class TestForPytest(flexmock_test.RegularClass):

  def test_class_level_test_for_pytest(self):
    flexmock(foo='bar').should_receive('foo').once
    assertRaises(MethodCallError, flexmock_teardown)


class TestUnittestClass(flexmock_test.TestFlexmockUnittest):

  def test_unittest(self):
    a = flexmock(a=2)
    a.should_receive('a').once
    assertRaises(MethodCallError, flexmock_teardown)


class TestFailureOnException(object):

  @pytest.mark.xfail(raises=RuntimeError)
  def test_exception(self):
    raise RuntimeError("TEST ERROR")

