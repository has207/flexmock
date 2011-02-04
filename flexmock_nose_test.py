from flexmock import MethodNotCalled
from flexmock import flexmock_nose as flexmock
from flexmock import get_current_function
from flexmock import flexmock_teardown
from flexmock_test import TestFlexmock
from flexmock_test import assertRaises
from nose import with_setup


def empty_setup():
  pass


def test_module_level_test_for_nose():
  flexmock(foo='bar').should_receive('foo').once
  assertRaises(MethodNotCalled, get_current_function().teardown)


@with_setup(empty_setup, flexmock_teardown())
def test_module_level_generator():
  mock = flexmock()
  mock.should_receive('foo').times(3)  # change the number here to observe failure
  for i in range(0, 3):
    yield mock.foo, i, i*3


class TestClassForNose:
  def test_method_inside_class(self):
    flexmock(foo='bar').should_receive('foo').once
    this_func = get_current_function()
    assertRaises(MethodNotCalled, this_func.teardown)

  @with_setup(empty_setup, flexmock_teardown())
  def test_class_level_generator_tests(self):
    mock = flexmock(foo=lambda a, b: a)
    mock.should_receive('bar').never  # change never to once to observe the failure
    for i in range(0, 3):
      yield mock.foo, i, i*3
