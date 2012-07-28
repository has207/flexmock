# -*- coding: utf8 -*-
from flexmock import EXACTLY
from flexmock import AT_LEAST
from flexmock import AT_MOST
from flexmock import UPDATED_ATTRS
from flexmock import Mock
from flexmock import MockBuiltinError
from flexmock import FlexmockContainer
from flexmock import FlexmockError
from flexmock import MethodSignatureError
from flexmock import ExceptionClassError
from flexmock import ExceptionMessageError
from flexmock import StateError
from flexmock import MethodCallError
from flexmock import CallOrderError
from flexmock import ReturnValue
from flexmock import flexmock
from flexmock import flexmock_teardown
from flexmock import _format_args
from flexmock import _isproperty
import re
import sys
import unittest


def module_level_function(some, args):
  return "%s, %s" % (some, args)


module_level_attribute = 'test'


class OldStyleClass:
  pass


class NewStyleClass(object):
  pass


def assertRaises(exception, method, *kargs, **kwargs):
  try:
    method(*kargs, **kwargs)
  except exception:
    return
  except:
    instance = sys.exc_info()[1]
    print('%s' % instance)
  raise Exception('%s not raised' % exception.__name__)


def assertEqual(expected, received, msg=''):
  if not msg:
    msg = 'expected %s, received %s' % (expected, received)
  if expected != received:
    raise AssertionError('%s != %s : %s' % (expected, received, msg))


class RegularClass(object):

  def _tear_down(self):
    return flexmock_teardown()

  def test_flexmock_should_create_mock_object(self):
    mock = flexmock()
    assert isinstance(mock, Mock)

  def test_flexmock_should_create_mock_object_from_dict(self):
    mock = flexmock(foo='foo', bar='bar')
    assertEqual('foo',  mock.foo)
    assertEqual('bar', mock.bar)

  def test_flexmock_should_add_expectations(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo')
    assert ('method_foo' in
            [x.name for x in FlexmockContainer.flexmock_objects[mock]])

  def test_flexmock_should_return_value(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar')
    mock.should_receive('method_bar').and_return('value_baz')
    assertEqual('value_bar', mock.method_foo())
    assertEqual('value_baz', mock.method_bar())

  def test_flexmock_should_accept_shortcuts_for_creating_mock_object(self):
    mock = flexmock(attr1='value 1', attr2=lambda: 'returning 2')
    assertEqual('value 1', mock.attr1)
    assertEqual('returning 2',  mock.attr2())

  def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
    class Foo:
      def method1(self): pass
      def method2(self): pass
    foo = Foo()
    flexmock(foo, method1='returning 1', method2='returning 2')
    assertEqual('returning 1', foo.method1())
    assertEqual('returning 2', foo.method2())
    assertEqual('returning 2', foo.method2())

  def test_flexmock_expectations_returns_all(self):
    mock = flexmock(name='temp')
    assert mock not in FlexmockContainer.flexmock_objects
    mock.should_receive('method_foo')
    mock.should_receive('method_bar')
    assertEqual(2, len(FlexmockContainer.flexmock_objects[mock]))

  def test_flexmock_expectations_returns_named_expectation(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo')
    assertEqual('method_foo',
                FlexmockContainer.get_flexmock_expectation(
                     mock, 'method_foo').name)

  def test_flexmock_expectations_returns_none_if_not_found(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo')
    assert (FlexmockContainer.get_flexmock_expectation(
       mock, 'method_bar') is None)

  def test_flexmock_should_check_parameters(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('bar').and_return(1)
    mock.should_receive('method_foo').with_args('baz').and_return(2)
    assertEqual(1, mock.method_foo('bar'))
    assertEqual(2, mock.method_foo('baz'))

  def test_flexmock_should_keep_track_of_calls(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('foo').and_return(0)
    mock.should_receive('method_foo').with_args('bar').and_return(1)
    mock.should_receive('method_foo').with_args('baz').and_return(2)
    mock.method_foo('bar')
    mock.method_foo('bar')
    mock.method_foo('baz')
    expectation = FlexmockContainer.get_flexmock_expectation(
        mock, 'method_foo', ('foo',))
    assertEqual(0, expectation.times_called)
    expectation = FlexmockContainer.get_flexmock_expectation(
        mock, 'method_foo', ('bar',))
    assertEqual(2, expectation.times_called)
    expectation = FlexmockContainer.get_flexmock_expectation(
        mock, 'method_foo', ('baz',))
    assertEqual(1, expectation.times_called)

  def test_flexmock_should_set_expectation_call_numbers(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').times(1)
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertRaises(MethodCallError, expectation.verify)
    mock.method_foo()
    expectation.verify()

  def test_flexmock_should_check_raised_exceptions(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      pass
    mock.should_receive('method_foo').and_raise(FakeException)
    assertRaises(FakeException, mock.method_foo)
    assertEqual(1,
                FlexmockContainer.get_flexmock_expectation(
                    mock, 'method_foo').times_called)

  def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    mock.should_receive('method_foo').and_raise(FakeException(1, arg2=2))
    assertRaises(FakeException, mock.method_foo)
    assertEqual(1,
                FlexmockContainer.get_flexmock_expectation(
                    mock, 'method_foo').times_called)

  def test_flexmock_should_check_raised_exceptions_class_with_args(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    mock.should_receive('method_foo').and_raise(FakeException, 1, arg2=2)
    assertRaises(FakeException, mock.method_foo)
    assertEqual(1,
                FlexmockContainer.get_flexmock_expectation(
                    mock, 'method_foo').times_called)

  def test_flexmock_should_match_any_args_by_default(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar')
    mock.should_receive('method_foo').with_args('baz').and_return('baz')
    assertEqual('bar', mock.method_foo())
    assertEqual('bar', mock.method_foo(1))
    assertEqual('bar', mock.method_foo('foo', 'bar'))
    assertEqual('baz', mock.method_foo('baz'))

  def test_flexmock_should_fail_to_match_exactly_no_args_when_calling_with_args(self):
    mock = flexmock()
    mock.should_receive('method_foo').with_args()
    assertRaises(MethodSignatureError, mock.method_foo, 'baz')

  def test_flexmock_should_match_exactly_no_args(self):
    class Foo:
      def bar(self): pass
    foo = Foo()
    flexmock(foo).should_receive('bar').with_args().and_return('baz')
    assertEqual('baz', foo.bar())

  def test_expectation_dot_mock_should_return_mock(self):
    mock = flexmock(name='temp')
    assertEqual(mock, mock.should_receive('method_foo').mock)

  def test_flexmock_should_create_partial_new_style_object_mock(self):
    class User(object):
      def __init__(self, name=None):
        self.name = name
      def get_name(self):
        return self.name
      def set_name(self, name):
        self.name = name
    user = User()
    flexmock(user)
    user.should_receive('get_name').and_return('john')
    user.set_name('mike')
    assertEqual('john', user.get_name())

  def test_flexmock_should_create_partial_old_style_object_mock(self):
    class User:
      def __init__(self, name=None):
        self.name = name
      def get_name(self):
        return self.name
      def set_name(self, name):
        self.name = name
    user = User()
    flexmock(user)
    user.should_receive('get_name').and_return('john')
    user.set_name('mike')
    assertEqual('john', user.get_name())

  def test_flexmock_should_create_partial_new_style_class_mock(self):
    class User(object):
      def __init__(self): pass
      def get_name(self): pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    assertEqual('mike', user.get_name())

  def test_flexmock_should_create_partial_old_style_class_mock(self):
    class User:
      def __init__(self): pass
      def get_name(self): pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    assertEqual('mike', user.get_name())

  def test_flexmock_should_match_expectations_against_builtin_classes(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args(str).and_return('got a string')
    mock.should_receive('method_foo').with_args(int).and_return('got an int')
    assertEqual('got a string', mock.method_foo('string!'))
    assertEqual('got an int', mock.method_foo(23))
    assertRaises(MethodSignatureError, mock.method_foo, 2.0)

  def test_flexmock_should_match_expectations_against_user_defined_classes(self):
    mock = flexmock(name='temp')
    class Foo:
      pass
    mock.should_receive('method_foo').with_args(Foo).and_return('got a Foo')
    assertEqual('got a Foo', mock.method_foo(Foo()))
    assertRaises(MethodSignatureError, mock.method_foo, 1)

  def test_flexmock_configures_global_mocks_dict(self):
    mock = flexmock(name='temp')
    assert mock not in FlexmockContainer.flexmock_objects
    mock.should_receive('method_foo')
    assert mock in FlexmockContainer.flexmock_objects
    assertEqual(len(FlexmockContainer.flexmock_objects[mock]), 1)

  def test_flexmock_teardown_verifies_mocks(self):
    mock = flexmock(name='temp')
    mock.should_receive('verify_expectations').times(1)
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_teardown_does_not_verify_stubs(self):
    mock = flexmock(name='temp')
    mock.should_receive('verify_expectations')
    self._tear_down()

  def test_flexmock_preserves_stubbed_object_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    flexmock(user).should_receive('get_name').and_return('john')
    assertEqual('john', user.get_name())
    self._tear_down()
    assertEqual('mike', user.get_name())

  def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    flexmock(User).should_receive('get_name').and_return('john')
    assertEqual('john', user.get_name())
    self._tear_down()
    assertEqual('mike', user.get_name())

  def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
    class User:
      def get_name(self): pass
    user = User()
    saved = user.get_name
    flexmock(user).should_receive('get_name').and_return('john')
    assert saved != user.get_name
    assertEqual('john', user.get_name())
    self._tear_down()
    assertEqual(saved, user.get_name)

  def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
    class User:
      def get_name(self): pass
    user = User()
    saved = user.get_name
    flexmock(User).should_receive('get_name').and_return('john')
    assert saved != user.get_name
    assertEqual('john', user.get_name())
    self._tear_down()
    assertEqual(saved, user.get_name)

  def test_flexmock_removes_stubs_from_multiple_objects_on_teardown(self):
    class User:
      def get_name(self): pass
    class Group:
      def get_name(self): pass
    user = User()
    group = User()
    saved1 = user.get_name
    saved2 = group.get_name
    flexmock(user).should_receive('get_name').and_return('john').once()
    flexmock(group).should_receive('get_name').and_return('john').once()
    assert saved1 != user.get_name
    assert saved2 != group.get_name
    assertEqual('john', user.get_name())
    assertEqual('john', group.get_name())
    self._tear_down()
    assertEqual(saved1, user.get_name)
    assertEqual(saved2, group.get_name)

  def test_flexmock_removes_stubs_from_multiple_classes_on_teardown(self):
    class User:
      def get_name(self): pass
    class Group:
      def get_name(self): pass
    user = User()
    group = User()
    saved1 = user.get_name
    saved2 = group.get_name
    flexmock(User).should_receive('get_name').and_return('john')
    flexmock(Group).should_receive('get_name').and_return('john')
    assert saved1 != user.get_name
    assert saved2 != group.get_name
    assertEqual('john', user.get_name())
    assertEqual('john', group.get_name())
    self._tear_down()
    assertEqual(saved1, user.get_name)
    assertEqual(saved2, group.get_name)

  def test_flexmock_respects_at_least_when_called_less_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar').at_least().twice()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_LEAST, expectation.modifier)
    mock.method_foo()
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_respects_at_least_when_called_requested_number(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_least().once()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_LEAST, expectation.modifier)
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_least_when_called_more_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_least().once()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_LEAST, expectation.modifier)
    mock.method_foo()
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_less_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar').at_most().twice()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_MOST, expectation.modifier)
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_requested_number(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_most().once()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_MOST, expectation.modifier)
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_more_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_most().once()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(AT_MOST, expectation.modifier)
    mock.method_foo()
    assertRaises(MethodCallError, mock.method_foo)

  def test_flexmock_treats_once_as_times_one(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').once()
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(1, expectation.expected_calls[EXACTLY])
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_treats_twice_as_times_two(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').twice().and_return('value_bar')
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(2, expectation.expected_calls[EXACTLY])
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_works_with_never_when_true(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').never
    expectation = FlexmockContainer.get_flexmock_expectation(mock, 'method_foo')
    assertEqual(0, expectation.expected_calls[EXACTLY])
    self._tear_down()

  def test_flexmock_works_with_never_when_false(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').never
    assertRaises(MethodCallError, mock.method_foo)
  
  def test_flexmock_get_flexmock_expectation_should_work_with_args(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('value_bar')
    assert FlexmockContainer.get_flexmock_expectation(
        mock, 'method_foo', 'value_bar')

  def test_flexmock_function_should_return_previously_mocked_object(self):
    class User(object): pass
    user = User()
    foo = flexmock(user)
    assert foo == user
    assert foo == flexmock(user)

  def test_flexmock_should_not_return_class_object_if_mocking_instance(self):
    class User:
      def method(self): pass
    user = User()
    user2 = User()
    class_mock = flexmock(User).should_receive(
        'method').and_return('class').mock
    user_mock = flexmock(user).should_receive(
        'method').and_return('instance').mock
    assert class_mock is not user_mock
    assertEqual('instance', user.method())
    assertEqual('class', user2.method())

  def test_should_call_on_class_mock(self):
    class User:
      def foo(self): return 'class'
    user1 = User()
    user2 = User()
    flexmock(User).should_call('foo').once()
    assertRaises(MethodCallError, self._tear_down)
    flexmock(User).should_call('foo').twice()
    assertEqual('class', user1.foo())
    assertEqual('class', user2.foo())

  def test_flexmock_should_not_blow_up_on_should_call_for_class_methods(self):
    class User:
      @classmethod
      def foo(self):
        return 'class'
    flexmock(User).should_call('foo')
    assertEqual('class', User.foo())

  def test_flexmock_should_not_blow_up_on_should_call_for_static_methods(self):
    class User:
      @staticmethod
      def foo():
        return 'static'
    flexmock(User).should_call('foo')
    assertEqual('static', User.foo())

  def test_flexmock_should_mock_new_instances_with_multiple_params(self):
    class User(object): pass
    class Group(object):
      def __init__(self, arg, arg2):
        pass
    user = User()
    flexmock(Group).new_instances(user)
    assert user is Group(1, 2)

  def test_flexmock_should_revert_new_instances_on_teardown(self):
    class User(object): pass
    class Group(object): pass
    user = User()
    group = Group()
    flexmock(Group).new_instances(user)
    assert user is Group()
    self._tear_down()
    assertEqual(group.__class__, Group().__class__)

  def test_flexmock_should_cleanup_added_methods_and_attributes(self):
    class Group(object): pass
    group = Group()
    flexmock(Group)
    assert 'should_receive' in Group.__dict__
    assert 'should_receive' not in group.__dict__
    flexmock(group)
    assert 'should_receive' in group.__dict__
    self._tear_down()
    for method in UPDATED_ATTRS:
      assert method not in Group.__dict__
      assert method not in group.__dict__

  def test_flexmock_should_cleanup_after_exception(self):
    class User:
      def method2(self): pass
    class Group:
      def method1(self): pass
    flexmock(Group)
    flexmock(User)
    Group.should_receive('method1').once()
    User.should_receive('method2').once()
    assertRaises(MethodCallError, self._tear_down)
    for method in UPDATED_ATTRS:
      assert method not in dir(Group)
    for method in UPDATED_ATTRS:
      assert method not in dir(User)

  def test_flexmock_should_call_respects_matched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self, arg):
        return arg
    group = Group()
    flexmock(group).should_call('method1').twice()
    assertEqual('a:c', group.method1('a', arg2='c'))
    assertEqual('a:b', group.method1('a'))
    group.should_call('method2').once().with_args('c')
    assertEqual('c', group.method2('c'))
    self._tear_down()

  def test_flexmock_should_call_respects_unmatched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self, a): pass
    group = Group()
    flexmock(group).should_call('method1').at_least().once()
    assertRaises(MethodCallError, self._tear_down)
    flexmock(group)
    group.should_call('method2').with_args('a').once()
    group.should_receive('method2').with_args('not a')
    group.method2('not a')
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_doesnt_error_on_properly_ordered_expectations(self):
    class Foo(object):
      def foo(self): pass
      def method1(self, a): pass
      def bar(self): pass
      def baz(self): pass
    foo = Foo()
    flexmock(foo).should_receive('foo')
    flexmock(foo).should_receive('method1').with_args('a').ordered()
    flexmock(foo).should_receive('bar')
    flexmock(foo).should_receive('method1').with_args('b').ordered()
    flexmock(foo).should_receive('baz')
    foo.bar()
    foo.method1('a')
    foo.method1('b')
    foo.baz()
    foo.foo()

  def test_flexmock_errors_on_improperly_ordered_expectations(self):
    class Foo(object):
      def method1(self, a): pass
    foo = Foo()
    flexmock(foo)
    foo.should_receive('method1').with_args('a').ordered()
    foo.should_receive('method1').with_args('b').ordered()
    assertRaises(CallOrderError, foo.method1, 'b')

  def test_flexmock_should_accept_multiple_return_values(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 5).and_return(2)
    assertEqual((1, 5), foo.method1())
    assertEqual(2, foo.method1())
    assertEqual((1, 5), foo.method1())
    assertEqual(2, foo.method1())

  def test_flexmock_should_accept_multiple_return_values_with_shortcut(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 2).one_by_one()
    assertEqual(1, foo.method1())
    assertEqual(2, foo.method1())
    assertEqual(1, foo.method1())
    assertEqual(2, foo.method1())

  def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1).and_raise(Exception)
    assertEqual(1, foo.method1())
    assertRaises(Exception, foo.method1)
    assertEqual(1, foo.method1())
    assertRaises(Exception, foo.method1)

  def test_flexmock_should_match_types_on_multiple_arguments(self):
    class Foo:
      def method1(self, a, b): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(str, int).and_return('ok')
    assertEqual('ok', foo.method1('some string', 12))
    assertRaises(MethodSignatureError, foo.method1, 12, 32)
    flexmock(foo).should_receive('method1').with_args(str, int).and_return('ok')
    assertRaises(MethodSignatureError, foo.method1, 12, 'some string')
    flexmock(foo).should_receive('method1').with_args(str, int).and_return('ok')
    assertRaises(MethodSignatureError, foo.method1, 'string', 12, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_generic(self):
    class Foo:
      def method1(self, a, b, c): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(
        object, object, object).and_return('ok')
    assertEqual('ok', foo.method1('some string', None, 12))
    assertEqual('ok', foo.method1((1,), None, 12))
    assertEqual('ok', foo.method1(12, 14, []))
    assertEqual('ok', foo.method1('some string', 'another one', False))
    assertRaises(MethodSignatureError, foo.method1, 'string', 12)
    flexmock(foo).should_receive('method1').with_args(
        object, object, object).and_return('ok')
    assertRaises(MethodSignatureError, foo.method1, 'string', 12, 13, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_classes(self):
    class Foo:
      def method1(self, a, b): pass
    class Bar: pass
    foo = Foo()
    bar = Bar()
    flexmock(foo).should_receive('method1').with_args(
        object, Bar).and_return('ok')
    assertEqual('ok', foo.method1('some string', bar))
    assertRaises(MethodSignatureError, foo.method1, bar, 'some string')
    flexmock(foo).should_receive('method1').with_args(
        object, Bar).and_return('ok')
    assertRaises(MethodSignatureError, foo.method1, 12, 'some string')

  def test_flexmock_should_match_keyword_arguments(self):
    class Foo:
      def method1(self, a, **kwargs): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2).twice()
    foo.method1(1, arg2=2, arg3=3)
    foo.method1(1, arg3=3, arg2=2)
    self._tear_down()
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2)
    assertRaises(MethodSignatureError, foo.method1, arg2=2, arg3=3)
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2)
    assertRaises(MethodSignatureError, foo.method1, 1, arg2=2, arg3=4)
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2)
    assertRaises(MethodSignatureError, foo.method1, 1)

  def test_flexmock_should_call_should_match_keyword_arguments(self):
    class Foo:
      def method1(self, arg1, arg2=None, arg3=None):
        return '%s%s%s' % (arg1, arg2, arg3)
    foo = Foo()
    flexmock(foo).should_call('method1').with_args(1, arg3=3, arg2=2).once()
    assertEqual('123', foo.method1(1, arg2=2, arg3=3))

  def test_flexmock_should_mock_private_methods(self):
    class Foo:
      def __private_method(self):
        return 'foo'
      def public_method(self):
        return self.__private_method()
    foo = Foo()
    flexmock(foo).should_receive('__private_method').and_return('bar')
    assertEqual('bar', foo.public_method())

  def test_flexmock_should_mock_special_methods(self):
    class Foo:
      def __special_method__(self):
        return 'foo'
      def public_method(self):
        return self.__special_method__()
    foo = Foo()
    flexmock(foo).should_receive('__special_method__').and_return('bar')
    assertEqual('bar', foo.public_method())

  def test_flexmock_should_mock_double_underscore_method(self):
    class Foo:
      def __(self):
        return 'foo'
      def public_method(self):
        return self.__()
    foo = Foo()
    flexmock(foo).should_receive('__').and_return('bar')
    assertEqual('bar', foo.public_method())

  def test_flexmock_should_mock_private_class_methods(self):
    class Foo:
      def __iter__(self): pass
    flexmock(Foo).should_receive('__iter__').and_yield(1, 2, 3)
    assertEqual([1, 2, 3], [x for x in Foo()])

  def test_flexmock_should_mock_iter_on_new_style_instances(self):
    class Foo(object):
      def __iter__(self):
        yield None
    old = Foo.__iter__
    foo = Foo()
    foo2 = Foo()
    foo3 = Foo()
    flexmock(foo, __iter__=iter([1, 2, 3]))
    flexmock(foo2, __iter__=iter([3, 4, 5]))
    assertEqual([1, 2, 3], [x for x in foo])
    assertEqual([3, 4, 5], [x for x in foo2])
    assertEqual([None], [x for x in foo3])
    assertEqual(False, foo.__iter__ == old)
    assertEqual(False, foo2.__iter__ == old)
    assertEqual(False, foo3.__iter__ == old)
    self._tear_down()
    assertEqual([None], [x for x in foo])
    assertEqual([None], [x for x in foo2])
    assertEqual([None], [x for x in foo3])
    assertEqual(True, Foo.__iter__ == old, '%s != %s' % (Foo.__iter__, old))

  def test_flexmock_should_mock_private_methods_with_leading_underscores(self):
    class _Foo:
      def __stuff(self): pass
      def public_method(self):
        return self.__stuff()
    foo = _Foo()
    flexmock(foo).should_receive('__stuff').and_return('bar')
    assertEqual('bar', foo.public_method())

  def test_flexmock_should_mock_generators(self):
    class Gen:
      def foo(self): pass
    gen = Gen()
    flexmock(gen).should_receive('foo').and_yield(*range(1, 10))
    output = [val for val in gen.foo()]
    assertEqual([val for val in range(1, 10)], output)

  def test_flexmock_should_verify_correct_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_call('get_stuff').and_return('real', 'stuff')
    assertEqual(('real', 'stuff'), user.get_stuff())

  def test_flexmock_should_verify_correct_spy_regexp_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_call('get_stuff').and_return(
        re.compile('ea.*'), re.compile('^stuff$'))
    assertEqual(('real', 'stuff'), user.get_stuff())

  def test_flexmock_should_verify_spy_raises_correct_exception_class(self):
    class FakeException(Exception):
      def __init__(self, param, param2):
        self.message = '%s, %s' % (param, param2)
        Exception.__init__(self)
    class User:
      def get_stuff(self): raise FakeException(1, 2)
    user = User()
    flexmock(user).should_call('get_stuff').and_raise(FakeException, 1, 2)
    user.get_stuff()

  def test_flexmock_should_verify_spy_matches_exception_message(self):
    class FakeException(Exception):
      def __init__(self, param, param2):
        self.p1 = param
        self.p2 = param2
        Exception.__init__(self, param)
      def __str__(self):
        return '%s, %s' % (self.p1, self.p2)
    class User:
      def get_stuff(self): raise FakeException('1', '2')
    user = User()
    flexmock(user).should_call('get_stuff').and_raise(FakeException, '2', '1')
    assertRaises(ExceptionMessageError, user.get_stuff)

  def test_flexmock_should_verify_spy_matches_exception_regexp(self):
    class User:
      def get_stuff(self): raise Exception('123asdf345')
    user = User()
    flexmock(user).should_call(
        'get_stuff').and_raise(Exception, re.compile('asdf'))
    user.get_stuff()
    self._tear_down()

  def test_flexmock_should_verify_spy_matches_exception_regexp_mismatch(self):
    class User:
      def get_stuff(self): raise Exception('123asdf345')
    user = User()
    flexmock(user).should_call(
        'get_stuff').and_raise(Exception, re.compile('^asdf'))
    assertRaises(ExceptionMessageError, user.get_stuff)

  def test_flexmock_should_blow_up_on_wrong_spy_exception_type(self):
    class User:
      def get_stuff(self): raise CallOrderError('foo')
    user = User()
    flexmock(user).should_call('get_stuff').and_raise(MethodCallError)
    assertRaises(ExceptionClassError, user.get_stuff)

  def test_flexmock_should_match_spy_exception_parent_type(self):
    class User:
      def get_stuff(self): raise CallOrderError('foo')
    user = User()
    flexmock(user).should_call('get_stuff').and_raise(FlexmockError)
    user.get_stuff()

  def test_flexmock_should_blow_up_on_wrong_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
      def get_more_stuff(self): return 'other', 'stuff'
    user = User()
    flexmock(user).should_call('get_stuff').and_return('other', 'stuff')
    assertRaises(MethodSignatureError, user.get_stuff)
    flexmock(user).should_call('get_more_stuff').and_return()
    assertRaises(MethodSignatureError, user.get_more_stuff)

  def test_flexmock_should_mock_same_class_twice(self):
    class Foo: pass
    flexmock(Foo)
    flexmock(Foo)

  def test_flexmock_spy_should_not_clobber_original_method(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_call('get_stuff')
    flexmock(user).should_call('get_stuff')
    assertEqual(('real', 'stuff'), user.get_stuff())

  def test_flexmock_should_properly_restore_static_methods(self):
    class User:
      @staticmethod
      def get_stuff(): return 'ok!'
    assertEqual('ok!', User.get_stuff())
    flexmock(User).should_receive('get_stuff')
    assert User.get_stuff() is None
    self._tear_down()
    assertEqual('ok!', User.get_stuff())

  def test_flexmock_should_properly_restore_undecorated_static_methods(self):
    class User:
      def get_stuff(): return 'ok!'
      get_stuff = staticmethod(get_stuff)
    assertEqual('ok!', User.get_stuff())
    flexmock(User).should_receive('get_stuff')
    assert User.get_stuff() is None
    self._tear_down()
    assertEqual('ok!', User.get_stuff())

  def test_flexmock_should_properly_restore_module_level_functions(self):
    if 'flexmock_test' in sys.modules:
      mod = sys.modules['flexmock_test']
    else:
      mod = sys.modules['__main__']
    flexmock(mod).should_receive('module_level_function').with_args(1, 2)
    assertEqual(None,  module_level_function(1, 2))
    self._tear_down()
    assertEqual('1, 2', module_level_function(1, 2))

  def test_flexmock_should_support_mocking_old_style_classes_as_functions(self):
    if 'flexmock_test' in sys.modules:
      mod = sys.modules['flexmock_test']
    else:
      mod = sys.modules['__main__']
    flexmock(mod).should_receive('OldStyleClass').and_return('yay')
    assertEqual('yay', OldStyleClass())

  def test_flexmock_should_support_mocking_new_style_classes_as_functions(self):
    if 'flexmock_test' in sys.modules:
      mod = sys.modules['flexmock_test']
    else:
      mod = sys.modules['__main__']
    flexmock(mod).should_receive('NewStyleClass').and_return('yay')
    assertEqual('yay', NewStyleClass())

  def test_flexmock_should_properly_restore_class_methods(self):
    class User:
      @classmethod
      def get_stuff(cls):
        return cls.__name__
    assertEqual('User', User.get_stuff())
    flexmock(User).should_receive('get_stuff').and_return('foo')
    assertEqual('foo', User.get_stuff())
    self._tear_down()
    assertEqual('User', User.get_stuff())

  def test_spy_should_match_return_value_class(self):
    class User: pass
    user = User()
    foo = flexmock(foo=lambda: ('bar', 'baz'),
                   bar=lambda: user,
                   baz=lambda: None,
                   bax=lambda: None)
    foo.should_call('foo').and_return(str, str)
    foo.should_call('bar').and_return(User)
    foo.should_call('baz').and_return(object)
    foo.should_call('bax').and_return(None)
    assertEqual(('bar', 'baz'), foo.foo())
    assertEqual(user, foo.bar())
    assertEqual(None, foo.baz())
    assertEqual(None, foo.bax())

  def test_new_instances_should_blow_up_on_should_receive(self):
    class User(object): pass
    mock = flexmock(User).new_instances(None).mock
    assertRaises(FlexmockError, mock.should_receive, 'foo')

  def test_should_call_alias_should_create_a_spy(self):
    class Foo:
      def get_stuff(self):
        return 'yay'
    foo = Foo()
    flexmock(foo).should_call('get_stuff').and_return('yay').once()
    assertRaises(MethodCallError, self._tear_down)

  def test_flexmock_should_fail_mocking_nonexistent_methods(self):
    class User: pass
    user = User()
    assertRaises(FlexmockError,
                 flexmock(user).should_receive, 'nonexistent')

  def test_flexmock_should_not_explode_on_unicode_formatting(self):
    if sys.version_info >= (3, 0):
      formatted = _format_args(
          'method', {'kargs' : (chr(0x86C7),), 'kwargs' : {}})
      assertEqual('method("蛇")', formatted)
    else:
      formatted = _format_args(
          'method', {'kargs' : (unichr(0x86C7),), 'kwargs' : {}})
      assertEqual('method("%s")' % unichr(0x86C7), formatted)

  def test_return_value_should_not_explode_on_unicode_values(self):
    class Foo:
      def method(self): pass
    if sys.version_info >= (3, 0):
      return_value = ReturnValue(chr(0x86C7))
      assertEqual('"蛇"', '%s' % return_value)
      return_value = ReturnValue((chr(0x86C7), chr(0x86C7)))
      assertEqual('("蛇", "蛇")', '%s' % return_value)
    else:
      return_value = ReturnValue(unichr(0x86C7))
      assertEqual('"%s"' % unichr(0x86C7), unicode(return_value))

  def test_pass_thru_should_call_original_method_only_once(self):
    class Nyan(object):
      def __init__(self):
          self.n = 0
      def method(self):
          self.n += 1
    obj = Nyan()
    flexmock(obj)
    obj.should_call('method')
    obj.method()
    assertEqual(obj.n, 1)
  
  def test_should_call_works_for_same_method_with_different_args(self):
    class Foo:
      def method(self, arg):
        pass
    foo = Foo()
    flexmock(foo).should_call('method').with_args('foo').once()
    flexmock(foo).should_call('method').with_args('bar').once()
    foo.method('foo')
    foo.method('bar')
    self._tear_down()

  def test_should_call_fails_properly_for_same_method_with_different_args(self):
    class Foo:
      def method(self, arg):
        pass
    foo = Foo()
    flexmock(foo).should_call('method').with_args('foo').once()
    flexmock(foo).should_call('method').with_args('bar').once()
    foo.method('foo')
    assertRaises(MethodCallError, self._tear_down)

  def test_should_give_reasonable_error_for_builtins(self):
    assertRaises(MockBuiltinError, flexmock, object)

  def test_should_give_reasonable_error_for_instances_of_builtins(self):
    assertRaises(MockBuiltinError, flexmock, object())

  def test_mock_chained_method_calls_works_with_one_level(self):
    class Foo:
      def method2(self):
        return 'foo'
    class Bar:
      def method1(self):
        return Foo()
    foo = Bar()
    assertEqual('foo', foo.method1().method2())
    flexmock(foo).should_receive('method1.method2').and_return('bar')
    assertEqual('bar', foo.method1().method2())

  def test_mock_chained_method_supports_args_and_mocks(self):
    class Foo:
      def method2(self, arg):
        return arg
    class Bar:
      def method1(self):
        return Foo()
    foo = Bar()
    assertEqual('foo', foo.method1().method2('foo'))
    flexmock(foo).should_receive('method1.method2').with_args(
        'foo').and_return('bar').once()
    assertEqual('bar', foo.method1().method2('foo'))
    self._tear_down()
    flexmock(foo).should_receive('method1.method2').with_args(
        'foo').and_return('bar').once()
    assertRaises(MethodCallError, self._tear_down)

  def test_mock_chained_method_calls_works_with_more_than_one_level(self):
    class Baz:
      def method3(self):
        return 'foo'
    class Foo:
      def method2(self):
        return Baz()
    class Bar:
      def method1(self):
        return Foo()
    foo = Bar()
    assertEqual('foo', foo.method1().method2().method3())
    flexmock(foo).should_receive('method1.method2.method3').and_return('bar')
    assertEqual('bar', foo.method1().method2().method3())

  def test_flexmock_should_replace_method(self):
    class Foo:
      def method(self, arg):
        return arg
    foo = Foo()
    flexmock(foo).should_receive('method').replace_with(lambda x: x == 5)
    assertEqual(foo.method(5), True)
    assertEqual(foo.method(4), False)

  def test_flexmock_should_replace_cannot_be_specified_twice(self):
    class Foo:
      def method(self, arg):
        return arg
    foo = Foo()
    expectation = flexmock(foo).should_receive(
        'method').replace_with(lambda x: x == 5)
    assertRaises(FlexmockError,
                 expectation.replace_with, lambda x: x == 3)

  def test_flexmock_should_mock_the_same_method_multiple_times(self):
    class Foo:
      def method(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method').and_return(1)
    assertEqual(foo.method(), 1)
    flexmock(foo).should_receive('method').and_return(2)
    assertEqual(foo.method(), 2)
    flexmock(foo).should_receive('method').and_return(3)
    assertEqual(foo.method(), 3)
    flexmock(foo).should_receive('method').and_return(4)
    assertEqual(foo.method(), 4)

  def test_new_instances_should_be_a_method(self):
    class Foo(object): pass
    flexmock(Foo).new_instances('bar')
    assertEqual('bar', Foo())
    self._tear_down()
    assert 'bar' != Foo()

  def test_new_instances_raises_error_when_not_a_class(self):
    class Foo(object): pass
    foo = Foo()
    flexmock(foo)
    assertRaises(FlexmockError, foo.new_instances, 'bar')

  def test_new_instances_works_with_multiple_return_values(self):
    class Foo(object): pass
    flexmock(Foo).new_instances('foo', 'bar')
    assertEqual('foo', Foo())
    assertEqual('bar', Foo())

  def test_should_receive_should_not_replace_flexmock_methods(self):
    class Foo:
      def bar(self): pass
    foo = Foo()
    flexmock(foo)
    assertRaises(FlexmockError, foo.should_receive, 'should_receive')

  def test_flexmock_should_not_add_methods_if_they_already_exist(self):
    class Foo:
      def should_receive(self):
        return 'real'
      def bar(self): pass
    foo = Foo()
    mock = flexmock(foo)
    assertEqual(foo.should_receive(), 'real')
    assert 'should_call' not in dir(foo)
    assert 'new_instances' not in dir(foo)
    mock.should_receive('bar').and_return('baz')
    assertEqual(foo.bar(), 'baz')
    self._tear_down()
    assertEqual(foo.should_receive(), 'real')

  def test_flexmock_should_not_add_class_methods_if_they_already_exist(self):
    class Foo:
      def should_receive(self):
        return 'real'
      def bar(self): pass
    foo = Foo()
    mock = flexmock(Foo)
    assertEqual(foo.should_receive(), 'real')
    assert 'should_call' not in dir(Foo)
    assert 'new_instances' not in dir(Foo)
    mock.should_receive('bar').and_return('baz')
    assertEqual(foo.bar(), 'baz')
    self._tear_down()
    assertEqual(foo.should_receive(), 'real')

  def test_expectation_properties_work_with_parens(self):
    foo = flexmock().should_receive(
        'bar').at_least().once().and_return('baz').mock()
    assertEqual('baz', foo.bar())

  def test_mocking_down_the_inheritance_chain_class_to_class(self):
    class Parent(object):
      def foo(self): pass
    class Child(Parent):
      def bar(self): pass

    flexmock(Parent).should_receive('foo').and_return('outer')
    flexmock(Child).should_receive('bar').and_return('inner')
    assert 'outer', Parent().foo()
    assert 'inner', Child().bar()

  def test_arg_matching_works_with_regexp(self):
    class Foo:
      def foo(self, arg1, arg2): pass
    foo = Foo()
    flexmock(foo).should_receive('foo').with_args(
        re.compile('^arg1.*asdf$'), arg2=re.compile('f')).and_return('mocked')
    assertEqual('mocked', foo.foo('arg1somejunkasdf', arg2='aadsfdas'))

  def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_karg(self):
    class Foo:
      def foo(self, arg1, arg2): pass
    foo = Foo()
    flexmock(foo).should_receive('foo').with_args(
        re.compile('^arg1.*asdf$'), arg2=re.compile('a')).and_return('mocked')
    assertRaises(MethodSignatureError, foo.foo, 'arg1somejunkasdfa', arg2='a')

  def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_kwarg(self):
    class Foo:
      def foo(self, arg1, arg2): pass
    foo = Foo()
    flexmock(foo).should_receive('foo').with_args(
        re.compile('^arg1.*asdf$'), arg2=re.compile('a')).and_return('mocked')
    assertRaises(MethodSignatureError, foo.foo, 'arg1somejunkasdf', arg2='b')

  def test_flexmock_class_returns_same_object_on_repeated_calls(self):
    class Foo: pass
    a = flexmock(Foo)
    b = flexmock(Foo)
    assertEqual(a, b)

  def test_flexmock_object_returns_same_object_on_repeated_calls(self):
    class Foo: pass
    foo = Foo()
    a = flexmock(foo)
    b = flexmock(foo)
    assertEqual(a, b)

  def test_flexmock_ordered_worked_after_default_stub(self):
    foo = flexmock()
    foo.should_receive('bar')
    foo.should_receive('bar').with_args('a').ordered()
    foo.should_receive('bar').with_args('b').ordered()
    assertRaises(CallOrderError, foo.bar, 'b')

  def test_state_machine(self):
    class Radio:
      def __init__(self): self.is_on = False
      def switch_on(self): self.is_on = True
      def switch_off(self): self.is_on = False
      def select_channel(self): return None
      def adjust_volume(self, num): self.volume = num

    radio = Radio()
    flexmock(radio)
    radio.should_receive('select_channel').once().when(
        lambda: radio.is_on)
    radio.should_call('adjust_volume').once().with_args(5).when(
        lambda: radio.is_on)

    assertRaises(StateError, radio.select_channel)
    assertRaises(StateError, radio.adjust_volume, 5)
    radio.is_on = True
    radio.select_channel()
    radio.adjust_volume(5)

  def test_support_at_least_and_at_most_together(self):
    class Foo:
      def bar(self): pass

    foo = Foo()
    flexmock(foo).should_call('bar').at_least().once().at_most().twice()
    assertRaises(MethodCallError, self._tear_down)

    flexmock(foo).should_call('bar').at_least().once().at_most().twice()
    foo.bar()
    foo.bar()
    assertRaises(MethodCallError, foo.bar)

    flexmock(foo).should_call('bar').at_least().once().at_most().twice()
    foo.bar()
    self._tear_down()

    flexmock(foo).should_call('bar').at_least().once().at_most().twice()
    foo.bar()
    foo.bar()
    self._tear_down()

  def test_at_least_cannot_be_used_twice(self):
    class Foo:
      def bar(self): pass

    expectation = flexmock(Foo).should_receive('bar')
    try:
      expectation.at_least().at_least()
      raise Exception('should not be able to specify at_least twice')
    except FlexmockError:
      pass
    except Exception:
      raise

  def test_at_most_cannot_be_used_twice(self):
    class Foo:
      def bar(self): pass

    expectation = flexmock(Foo).should_receive('bar')
    try:
      expectation.at_most().at_most()
      raise Exception('should not be able to specify at_most twice')
    except FlexmockError:
      pass
    except Exception:
      raise

  def test_at_least_cannot_be_specified_until_at_most_is_set(self):
    class Foo:
      def bar(self): pass

    expectation = flexmock(Foo).should_receive('bar')
    try:
      expectation.at_least().at_most()
      raise Exception('should not be able to specify at_most if at_least unset')
    except FlexmockError:
      pass
    except Exception:
      raise

  def test_at_most_cannot_be_specified_until_at_least_is_set(self):
    class Foo:
      def bar(self): pass

    expectation = flexmock(Foo).should_receive('bar')
    try:
      expectation.at_most().at_least()
      raise Exception('should not be able to specify at_least if at_most unset')
    except FlexmockError:
      pass
    except Exception:
      raise

  def test_proper_reset_of_subclass_methods(self):
    class A:
      def x(self):
        return 'a'
    class B(A):
      def x(self):
        return 'b'
    flexmock(B).should_receive('x').and_return('1')
    self._tear_down()
    assertEqual('b', B().x())

  def test_format_args_supports_tuples(self):
    formatted = _format_args('method', {'kargs' : ((1, 2),), 'kwargs' : {}})
    assertEqual('method((1, 2))', formatted)

  def test_mocking_subclass_of_str(self):
    class String(str): pass
    s = String()
    flexmock(s, endswith='fake')
    assertEqual('fake', s.endswith('stuff'))
    self._tear_down()
    assertEqual(False, s.endswith('stuff'))

  def test_ordered_on_different_methods(self):
    class String(str): pass
    s = String('abc')
    flexmock(s)
    s.should_call('startswith').with_args('asdf').ordered()
    s.should_call('endswith').ordered()
    assertRaises(CallOrderError, s.endswith, 'c')

  def test_fake_object_takes_properties(self):
    foo = flexmock(bar=property(lambda self: 'baz'))
    bar = flexmock(foo=property(lambda self: 'baz'))
    assertEqual('baz', foo.bar)
    assertEqual('baz', bar.foo)

  def test_replace_non_callable_class_attributes(self):
    class Foo:
      bar = 1
    foo = Foo()
    bar = Foo()
    flexmock(foo, bar=2)
    assertEqual(2, foo.bar)
    assertEqual(1, bar.bar)
    self._tear_down()
    assertEqual(1, foo.bar)

  def test_should_chain_attributes(self):
    class Baz:
      x = 1
    class Bar:
      baz = Baz()
    class Foo:
      bar = Bar()

    foo = Foo()
    foo = flexmock(foo)
    foo.should_receive('bar.baz.x').and_return(2)
    assertEqual(2, foo.bar.baz.x)
    self._tear_down()
    assertEqual(1, foo.bar.baz.x)

  def test_replace_non_callable_instance_attributes(self):
    class Foo:
      def __init__(self):
        self.bar = 1
    foo = Foo()
    bar = Foo()
    flexmock(foo, bar=2)
    flexmock(bar, bar=1)
    assertEqual(2, foo.bar)
    self._tear_down()
    assertEqual(1, foo.bar)

  def test_replace_non_callable_module_attributes(self):
    if 'flexmock_test' in sys.modules:
      mod = sys.modules['flexmock_test']
    else:
      mod = sys.modules['__main__']
    flexmock(mod, module_level_attribute='yay')
    assertEqual('yay',  module_level_attribute)
    self._tear_down()
    assertEqual('test', module_level_attribute)

  def test_non_callable_attributes_fail_to_set_expectations(self):
    class Foo:
      bar = 1
    foo = Foo()
    e = flexmock(foo).should_receive('bar').and_return(2)
    assertRaises(FlexmockError, e.times, 1)
    assertRaises(FlexmockError, e.with_args, ())
    assertRaises(FlexmockError, e.replace_with, lambda x: x)
    assertRaises(FlexmockError, e.and_raise, Exception)
    assertRaises(FlexmockError, e.when, lambda x: x)
    assertRaises(FlexmockError, e.and_yield, 1)
    assertRaises(FlexmockError, object.__getattribute__(e, 'ordered'))
    assertRaises(FlexmockError, object.__getattribute__(e, 'at_least'))
    assertRaises(FlexmockError, object.__getattribute__(e, 'at_most'))
    assertRaises(FlexmockError, object.__getattribute__(e, 'one_by_one'))

  def test_and_return_defaults_to_none_with_no_arguments(self):
    foo = flexmock()
    foo.should_receive('bar').and_return()
    assertEqual(None, foo.bar())

  def test_should_replace_attributes_that_are_instances_of_classes(self):
    class Foo(object):
      pass
    class Bar(object):
      foo = Foo()
    bar = Bar()
    flexmock(bar, foo='test')
    assertEqual('test', bar.foo)

  def test_isproperty(self):
    class Foo:
      @property
      def bar(self): pass
      def baz(self): pass
    class Bar(Foo): pass
    foo = Foo()
    bar = Bar()
    assertEqual(True, _isproperty(foo, 'bar'))
    assertEqual(False, _isproperty(foo, 'baz'))
    assertEqual(True, _isproperty(Foo, 'bar'))
    assertEqual(False, _isproperty(Foo, 'baz'))
    assertEqual(True, _isproperty(bar, 'bar'))
    assertEqual(False, _isproperty(bar, 'baz'))
    assertEqual(True, _isproperty(Bar, 'bar'))
    assertEqual(False, _isproperty(Bar, 'baz'))
    assertEqual(False, _isproperty(Mock(), 'baz'))

  def test_fake_object_supporting_iteration(self):
    foo = flexmock()
    foo.should_receive('__iter__').and_yield(1, 2, 3)
    assertEqual([1, 2, 3], [i for i in foo])

  def test_with_args_for_single_named_arg_with_optional_args(self):
    class Foo(object):
      def bar(self, one, two='optional'): pass
    e = flexmock(Foo).should_receive('bar')
    e.with_args(one=1)

  def test_with_args_doesnt_set_max_when_using_varargs(self):
    class Foo(object):
      def bar(self, *kargs): pass
    flexmock(Foo).should_receive('bar').with_args(1, 2, 3)

  def test_with_args_doesnt_set_max_when_using_kwargs(self):
    class Foo(object):
      def bar(self, **kwargs): pass
    flexmock(Foo).should_receive('bar').with_args(1, 2, 3)

  def test_with_args_blows_up_on_too_few_args(self):
    class Foo(object):
      def bar(self, a, b, c=1): pass
    e = flexmock(Foo).should_receive('bar')
    assertRaises(MethodSignatureError, e.with_args, 1)

  def test_with_args_blows_up_on_too_few_args_with_kwargs(self):
    class Foo(object):
      def bar(self, a, b, c=1): pass
    e = flexmock(Foo).should_receive('bar')
    assertRaises(MethodSignatureError, e.with_args, 1, c=2)

  def test_with_args_blows_up_on_too_many_args(self):
    class Foo(object):
      def bar(self, a, b, c=1): pass
    e = flexmock(Foo).should_receive('bar')
    assertRaises(MethodSignatureError, e.with_args, 1, 2, 3, 4)

  def test_with_args_blows_up_on_kwarg_overlapping_positional(self):
    class Foo(object):
      def bar(self, a, b, c=1, **kwargs): pass
    e = flexmock(Foo).should_receive('bar')
    assertRaises(MethodSignatureError, e.with_args, 1, 2, 3, c=2)

  def test_with_args_blows_up_on_invalid_kwarg(self):
    class Foo(object):
      def bar(self, a, b, c=1): pass
    e = flexmock(Foo).should_receive('bar')
    assertRaises(MethodSignatureError, e.with_args, 1, 2, d=2)

  def test_with_args_ignores_invalid_args_on_flexmock_instances(self):
    foo = flexmock(bar=lambda x: x)
    foo.should_receive('bar').with_args('stuff')
    foo.bar('stuff')

  def test_with_args_does_not_compensate_for_self_on_static_instance_methods(self):
    class Foo(object):
      @staticmethod
      def bar(x): pass
    foo = Foo()
    flexmock(foo).should_receive('bar').with_args('stuff')
    foo.bar('stuff')

  def test_with_args_does_not_compensate_for_self_on_static_class_methods(self):
    class Foo(object):
      @staticmethod
      def bar(x): pass
    flexmock(Foo).should_receive('bar').with_args('stuff')
    Foo.bar('stuff')

  def test_with_args_does_compensate_for_cls_on_class_methods(self):
    class Foo(object):
      @classmethod
      def bar(cls, x): pass
    foo = Foo()
    flexmock(foo).should_receive('bar').with_args('stuff')
    foo.bar('stuff')

  def test_calling_with_keyword_args_matches_mock_with_positional_args(self):
    class Foo(object):
      def bar(self, a, b, c): pass
    foo = Foo()
    flexmock(foo).should_receive('bar').with_args(1,2,3).once()
    foo.bar(a=1, b=2, c=3)

  def test_calling_with_positional_args_matches_mock_with_kwargs(self):
    class Foo(object):
      def bar(self, a, b, c): pass
    foo = Foo()
    flexmock(foo).should_receive('bar').with_args(a=1,b=2,c=3).once()
    foo.bar(1, 2, c=3)

  def test_use_replace_with_for_callable_shortcut_kwargs(self):
    class Foo(object):
      def bar(self): return 'bar'
    foo = Foo()
    flexmock(foo, bar=lambda: 'baz')
    assertEqual('baz', foo.bar())

  def test_mock_property_with_attribute_on_instance(self):
    class Foo(object):
      @property
      def bar(self): return 'bar'
    foo = Foo()
    foo2 = Foo()
    foo3 = Foo()
    flexmock(foo, bar='baz')
    flexmock(foo2, bar='baz2')
    assertEqual('baz', foo.bar)
    assertEqual('baz2', foo2.bar)
    assertEqual('bar', foo3.bar)
    self._tear_down()
    assertEqual(False, hasattr(Foo, '_flexmock__bar'),
                'Property bar not cleaned up')
    assertEqual('bar', foo.bar)
    assertEqual('bar', foo2.bar)
    assertEqual('bar', foo3.bar)

  def test_mock_property_with_attribute_on_class(self):
    class Foo(object):
      @property
      def bar(self): return 'bar'
    foo = Foo()
    foo2 = Foo()
    flexmock(Foo, bar='baz')
    assertEqual('baz', foo.bar)
    assertEqual('baz', foo2.bar)
    self._tear_down()
    assertEqual(False, hasattr(Foo, '_flexmock__bar'),
                'Property bar not cleaned up')
    assertEqual('bar', foo.bar)
    assertEqual('bar', foo2.bar)


class TestFlexmockUnittest(RegularClass, unittest.TestCase):
  def tearDown(self):
    pass

  def _tear_down(self):
    return flexmock_teardown()


if sys.version_info >= (2, 6):
  import flexmock_modern_test

  class TestUnittestModern(flexmock_modern_test.TestFlexmockUnittestModern):
    pass



if __name__ == '__main__':
  unittest.main()
