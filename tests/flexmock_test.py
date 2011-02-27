#-*- coding: utf8 -*-
from flexmock import FlexMock
from flexmock import AlreadyMocked
from flexmock import AttemptingToMockBuiltin
from flexmock import Expectation
from flexmock import FlexmockContainer
from flexmock import FlexmockError
from flexmock import InvalidMethodSignature
from flexmock import InvalidExceptionClass
from flexmock import InvalidExceptionMessage
from flexmock import MethodDoesNotExist
from flexmock import MethodNotCalled
from flexmock import MethodCalledOutOfOrder
from flexmock import ReturnValue
from flexmock import flexmock
from flexmock import _format_args
import sys
import unittest


def module_level_function(some, args):
  return "%s, %s" % (some, args)


def assertRaises(exception, method, *kargs, **kwargs):
  try:
    method(*kargs, **kwargs)
  except exception:
    assert True
    return
  except:
    pass
  raise Exception('%s not raised' % exception.__name__)


class RegularClass(object):

  def _tear_down(self):
    """Override this in the subclasses."""
    pass

  def test_flexmock_should_create_mock_object(self):
    mock = flexmock()
    assert isinstance(mock, FlexMock)

  def test_flexmock_should_create_mock_object_from_dict(self):
    mock = flexmock(foo='foo', bar='bar')
    assert 'foo' ==  mock.foo
    assert 'bar' == mock.bar

  def test_flexmock_should_add_expectations(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo')
    assert 'method_foo' in [x.method for x in mock._flexmock_expectations]

  def test_flexmock_should_return_value(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar')
    mock.should_receive('method_bar').and_return('value_baz')
    assert 'value_bar' == mock.method_foo()
    assert 'value_baz' == mock.method_bar()

  def test_flexmock_should_accept_shortcuts_for_creating_mock_object(self):
    mock = flexmock(attr1='value 1', attr2=lambda: 'returning 2')
    assert 'value 1' == mock.attr1
    assert 'returning 2' ==  mock.attr2()

  def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
    class Foo:
      def method1(self): pass
      def method2(self): pass
    foo = Foo()
    flexmock(foo, method1='returning 1', method2='returning 2')
    assert 'returning 1' == foo.method1()
    assert 'returning 2' == foo.method2()
    assert 'returning 2' == foo.method2()

  def test_flexmock_expectations_returns_all(self):
    mock = flexmock(name='temp')
    assert 0 == len(mock._flexmock_expectations)
    mock.should_receive('method_foo')
    mock.should_receive('method_bar')
    assert 2 == len(mock._flexmock_expectations)

  def test_flexmock_expectations_returns_named_expectation(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo')
    assert 'method_foo' == mock._get_flexmock_expectation('method_foo').method

  def test_flexmock_expectations_returns_none_if_not_found(self):
    mock = flexmock(name='temp')
    assert mock._get_flexmock_expectation('method_foo') is None

  def test_flexmock_should_check_parameters(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('bar').and_return(1)
    mock.should_receive('method_foo').with_args('baz').and_return(2)
    assert 1 == mock.method_foo('bar')
    assert 2 == mock.method_foo('baz')

  def test_flexmock_should_keep_track_of_calls(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('foo').and_return(0)
    mock.should_receive('method_foo').with_args('bar').and_return(1)
    mock.should_receive('method_foo').with_args('baz').and_return(2)
    mock.method_foo('bar')
    mock.method_foo('bar')
    mock.method_foo('baz')
    expectation = mock._get_flexmock_expectation('method_foo', ('foo',))
    assert 0 == expectation.times_called
    expectation = mock._get_flexmock_expectation('method_foo', ('bar',))
    assert 2 == expectation.times_called
    expectation = mock._get_flexmock_expectation('method_foo', ('baz',))
    assert 1 == expectation.times_called

  def test_flexmock_should_set_expectation_call_numbers(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').times(1)
    expectation = mock._get_flexmock_expectation('method_foo')
    assertRaises(MethodNotCalled, expectation.verify)
    mock.method_foo()
    expectation.verify()

  def test_flexmock_should_check_raised_exceptions(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      pass
    mock.should_receive('method_foo').and_raise(FakeException)
    assertRaises(FakeException, mock.method_foo)
    assert 1 == mock._get_flexmock_expectation('method_foo').times_called

  def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    mock.should_receive('method_foo').and_raise(FakeException(1, arg2=2))
    assertRaises(FakeException, mock.method_foo)
    assert 1 == mock._get_flexmock_expectation('method_foo').times_called

  def test_flexmock_should_check_raised_exceptions_class_with_args(self):
    mock = flexmock(name='temp')
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    mock.should_receive('method_foo').and_raise(FakeException, 1, arg2=2)
    assertRaises(FakeException, mock.method_foo)
    assert 1 == mock._get_flexmock_expectation('method_foo').times_called

  def test_flexmock_should_match_any_args_by_default(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar')
    mock.should_receive('method_foo').with_args('baz').and_return('baz')
    assert 'bar' == mock.method_foo()
    assert 'bar' == mock.method_foo(1)
    assert 'bar', mock.method_foo('foo' == 'bar')
    assert 'baz' == mock.method_foo('baz')

  def test_expectation_dot_mock_should_return_mock(self):
    mock = flexmock(name='temp')
    assert mock == mock.should_receive('method_foo').mock

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
    assert 'john' == user.get_name()

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
    assert 'john' == user.get_name()

  def test_flexmock_should_create_partial_new_style_class_mock(self):
    class User(object):
      def __init__(self): pass
      def get_name(self): pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    assert 'mike' == user.get_name()

  def test_flexmock_should_create_partial_old_style_class_mock(self):
    class User:
      def __init__(self): pass
      def get_name(self): pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    assert 'mike' == user.get_name()

  def test_flexmock_should_match_expectations_against_builtin_classes(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args(str).and_return('got a string')
    mock.should_receive('method_foo').with_args(int).and_return('got an int')
    assert 'got a string' == mock.method_foo('string!')
    assert 'got an int' == mock.method_foo(23)
    assertRaises(InvalidMethodSignature, mock.method_foo, 2.0)

  def test_flexmock_should_match_expectations_against_user_defined_classes(self):
    mock = flexmock(name='temp')
    class Foo:
      pass
    mock.should_receive('method_foo').with_args(Foo).and_return('got a Foo')
    assert 'got a Foo' == mock.method_foo(Foo())
    assertRaises(InvalidMethodSignature, mock.method_foo, 1)

  def test_flexmock_configures_global_mocks_dict(self):
    mock = flexmock(name='temp')
    assert mock not in FlexmockContainer.flexmock_objects
    mock.should_receive('method_foo')
    assert mock in FlexmockContainer.flexmock_objects
    assert len(FlexmockContainer.flexmock_objects[mock]) == 1

  def test_flexmock_teardown_verifies_mocks(self):
    mock = flexmock(name='temp')
    mock.should_receive('verify_expectations').times(1)
    assertRaises(MethodNotCalled, self._tear_down)

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
    assert 'john' == user.get_name()
    self._tear_down()
    assert 'mike' == user.get_name()

  def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    flexmock(User).should_receive('get_name').and_return('john')
    assert 'john' == user.get_name()
    self._tear_down()
    assert 'mike' == user.get_name()

  def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
    class User:
      def get_name(self): pass
    user = User()
    saved = user.get_name
    flexmock(user).should_receive('get_name').and_return('john')
    assert saved != user.get_name
    assert 'john' == user.get_name()
    self._tear_down()
    assert saved == user.get_name

  def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
    class User:
      def get_name(self): pass
    user = User()
    saved = user.get_name
    flexmock(User).should_receive('get_name').and_return('john')
    assert saved != user.get_name
    assert 'john' == user.get_name()
    self._tear_down()
    assert saved == user.get_name

  def test_flexmock_removes_stubs_from_multiple_objects_on_teardown(self):
    class User:
      def get_name(self): pass
    class Group:
      def get_name(self): pass
    user = User()
    group = User()
    saved1 = user.get_name
    saved2 = group.get_name
    flexmock(user).should_receive('get_name').and_return('john').once
    flexmock(group).should_receive('get_name').and_return('john').once
    assert saved1 != user.get_name
    assert saved2 != group.get_name
    assert 'john' == user.get_name()
    assert 'john' == group.get_name()
    self._tear_down()
    assert saved1 == user.get_name
    assert saved2 == group.get_name

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
    assert 'john' == user.get_name()
    assert 'john' == group.get_name()
    self._tear_down()
    assert saved1 == user.get_name
    assert saved2 == group.get_name

  def test_flexmock_respects_at_least_when_called_less_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar').at_least.twice
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_LEAST == expectation.modifier
    mock.method_foo()
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_respects_at_least_when_called_requested_number(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_least.once
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_LEAST == expectation.modifier
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_least_when_called_more_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_least.once
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_LEAST == expectation.modifier
    mock.method_foo()
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_less_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('bar').at_most.twice
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_MOST == expectation.modifier
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_requested_number(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_most.once
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_MOST == expectation.modifier
    mock.method_foo()
    self._tear_down()

  def test_flexmock_respects_at_most_when_called_more_than_requested(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').at_most.once
    expectation = mock._get_flexmock_expectation('method_foo')
    assert Expectation.AT_MOST == expectation.modifier
    mock.method_foo()
    mock.method_foo()
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_treats_once_as_times_one(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').once
    expectation = mock._get_flexmock_expectation('method_foo')
    assert 1 == expectation.expected_calls
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_treats_twice_as_times_two(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').twice.and_return('value_bar')
    expectation = mock._get_flexmock_expectation('method_foo')
    assert 2 == expectation.expected_calls
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_works_with_never_when_true(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').never
    expectation = mock._get_flexmock_expectation('method_foo')
    assert 0 == expectation.expected_calls
    self._tear_down()

  def test_flexmock_works_with_never_when_false(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').and_return('value_bar').never
    mock.method_foo()
    assertRaises(MethodNotCalled, self._tear_down)
  
  def test_flexmock_get_flexmock_expectation_should_work_with_args(self):
    mock = flexmock(name='temp')
    mock.should_receive('method_foo').with_args('value_bar')
    assert mock._get_flexmock_expectation('method_foo', 'value_bar')

  def test_flexmock_function_should_return_previously_mocked_object(self):
    class User(object): pass
    user = User()
    foo = flexmock(user)
    assert foo._object == flexmock(user)

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
    assert 'instance' == user.method()
    assert 'class' == user2.method()

  def test_flexmock_should_blow_up_on_and_execute_for_class_mock(self):
    class User:
      def foo(self):
        return 'class'
    try:
      flexmock(User).should_receive('foo').and_execute
      raise Exception('and_execute should have raised an exception')
    except FlexmockError:
      pass

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
    assert group.__class__ == Group().__class__

  def test_flexmock_should_cleanup_added_methods_and_attributes(self):
    class Group(object): pass
    flexmock(Group)
    self._tear_down()
    for method in FlexMock.UPDATED_ATTRS:
      assert method not in dir(Group)

  def test_flexmock_should_cleanup_after_exception(self):
    class User:
      def method2(self): pass
    class Group:
      def method1(self): pass
    flexmock(Group)
    flexmock(User)
    Group.should_receive('method1').once
    User.should_receive('method2').once
    assertRaises(MethodNotCalled, self._tear_down)
    for method in FlexMock.UPDATED_ATTRS:
      assert method not in dir(Group)
    for method in FlexMock.UPDATED_ATTRS:
      assert method not in dir(User)

  def test_flexmock_and_execute_respects_matched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self, arg):
        return arg
    group = Group()
    flexmock(group).should_receive('method1').twice.and_execute
    assert 'a:c' == group.method1('a', arg2='c')
    assert 'a:b' == group.method1('a')
    group.should_receive('method2').once.with_args('c').and_execute
    assert 'c' == group.method2('c')
    self._tear_down()

  def test_flexmock_and_execute_respects_unmatched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self): pass
    group = Group()
    flexmock(group).should_receive('method1').at_least.once.and_execute
    assertRaises(MethodNotCalled, self._tear_down)
    flexmock(group)
    group.should_receive('method2').with_args('a').once.and_execute
    group.should_receive('method2').with_args('not a')
    group.method2('not a')
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_doesnt_error_on_properly_ordered_expectations(self):
    class Foo(object):
      def foo(self): pass
      def method1(self): pass
      def bar(self): pass
      def baz(self): pass
    flexmock(Foo).should_receive('foo')
    flexmock(Foo).should_receive('method1').with_args('a').ordered
    flexmock(Foo).should_receive('bar')
    flexmock(Foo).should_receive('method1').with_args('b').ordered
    flexmock(Foo).should_receive('baz')
    Foo.bar()
    Foo.method1('a')
    Foo.method1('b')
    Foo.baz()
    Foo.foo()

  def test_flexmock_errors_on_improperly_ordered_expectations(self):
    class Foo(object):
      def foo(self): pass
      def method1(self): pass
      def bar(self): pass
      def baz(self): pass
    flexmock(Foo)
    Foo.should_receive('foo')
    Foo.should_receive('method1').with_args('a').ordered
    Foo.should_receive('bar')
    Foo.should_receive('method1').with_args('b').ordered
    Foo.should_receive('baz')
    Foo.bar()
    Foo.bar()
    Foo.foo()
    assertRaises(MethodCalledOutOfOrder, Foo.method1, 'b')

  def test_flexmock_should_accept_multiple_return_values(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 5).and_return(2)
    assert (1, 5) == foo.method1()
    assert 2 == foo.method1()
    assert (1, 5) == foo.method1()
    assert 2 == foo.method1()

  def test_flexmock_should_accept_multiple_return_values_with_shortcut(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 2).one_by_one
    assert 1 == foo.method1()
    assert 2 == foo.method1()
    assert 1 == foo.method1()
    assert 2 == foo.method1()

  def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1).and_raise(Exception)
    assert 1 == foo.method1()
    assertRaises(Exception, foo.method1)
    assert 1 == foo.method1()
    assertRaises(Exception, foo.method1)

  def test_flexmock_should_match_types_on_multiple_arguments(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(str, int).and_return('ok')
    assert 'ok', foo.method1('some string' == 12)
    assertRaises(InvalidMethodSignature, foo.method1, 12, 32)
    assertRaises(InvalidMethodSignature, foo.method1, 12, 'some string')
    assertRaises(InvalidMethodSignature, foo.method1, 'string', 12, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_generic(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(
        object, object, object).and_return('ok')
    assert 'ok', foo.method1('some string', None == 12)
    assert 'ok', foo.method1((1,), None == 12)
    assert 'ok', foo.method1(12, 14 == [])
    assert 'ok', foo.method1('some string', 'another one' == False)
    assertRaises(InvalidMethodSignature, foo.method1, 'string', 12)
    assertRaises(InvalidMethodSignature, foo.method1, 'string', 12, 13, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_classes(self):
    class Foo:
      def method1(self): pass
    class Bar: pass
    foo = Foo()
    bar = Bar()
    flexmock(foo).should_receive('method1').with_args(
        object, Bar).and_return('ok')
    assert 'ok', foo.method1('some string' == bar)
    assertRaises(InvalidMethodSignature, foo.method1, bar, 'some string')
    assertRaises(InvalidMethodSignature, foo.method1, 12, 'some string')

  def test_flexmock_should_match_keyword_arguments(self):
    class Foo:
      def method1(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2).twice
    foo.method1(1, arg2=2, arg3=3)
    foo.method1(1, arg3=3, arg2=2)
    self._tear_down()
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2)
    assertRaises(InvalidMethodSignature, foo.method1, arg2=2, arg3=3)
    assertRaises(InvalidMethodSignature, foo.method1, 1, arg2=2, arg3=4)
    assertRaises(InvalidMethodSignature, foo.method1, 1)

  def test_flexmock_should_match_keyword_arguments_works_with_and_execute(self):
    class Foo:
      def method1(self, arg1, arg2=None, arg3=None):
        return '%s%s%s' % (arg1, arg2, arg3)
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(
        1, arg3=3, arg2=2).and_execute.once
    assert '123' == foo.method1(1, arg2=2, arg3=3)

  def test_flexmock_should_mock_private_methods(self):
    class Foo:
      def __private_method(self):
        return 'foo'
      def public_method(self):
        return self.__private_method()
    foo = Foo()
    flexmock(foo).should_receive('__private_method').and_return('bar')
    assert 'bar' == foo.public_method()

  def test_flexmock_should_mock_private_class_methods(self):
    class Foo:
      def __iter__(self): pass
    flexmock(Foo).should_receive('__iter__').and_yield(1, 2, 3)
    assert [1, 2, 3] == [x for x in Foo()]

  def test_flexmock_should_mock_generators(self):
    class Gen:
      def foo(self): pass
    gen = Gen()
    flexmock(gen).should_receive('foo').and_yield(*range(1, 10))
    output = [val for val in gen.foo()]
    assert [val for val in range(1, 10)] == output

  def test_flexmock_should_verify_correct_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_return('real', 'stuff')
    assert ('real', 'stuff') == user.get_stuff()

  def test_flexmock_should_verify_spy_raises_correct_exception_class(self):
    class FakeException(Exception):
      def __init__(self, param, param2):
        self.message = '%s, %s' % (param, param2)
        Exception.__init__(self)
    class User:
      def get_stuff(self): raise FakeException(1, 2)
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_raise(FakeException, 1, 2)
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
      def get_stuff(self): raise FakeException(1, 2)
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_raise(FakeException, 2, 1)
    assertRaises(InvalidExceptionMessage, user.get_stuff)

  def test_flexmock_should_blow_up_on_wrong_exception_type(self):
    class User:
      def get_stuff(self): raise AlreadyMocked('foo')
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_raise(MethodNotCalled)
    assertRaises(InvalidExceptionClass, user.get_stuff)

  def test_flexmock_should_blow_up_on_wrong_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
      def get_more_stuff(self): return 'other', 'stuff'
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_return('other', 'stuff')
    assertRaises(InvalidMethodSignature, user.get_stuff)
    flexmock(user).should_receive(
        'get_more_stuff').and_execute.and_return()
    assertRaises(InvalidMethodSignature, user.get_more_stuff)

  def test_flexmock_should_mock_same_class_twice(self):
    class Foo: pass
    flexmock(Foo)
    flexmock(Foo)

  def test_flexmock_and_execute_should_not_clobber_original_method(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_receive('get_stuff').and_execute
    flexmock(user).should_receive('get_stuff').and_execute
    assert ('real', 'stuff') == user.get_stuff()

  def test_flexmock_should_properly_restore_static_methods(self):
    class User:
      @staticmethod
      def get_stuff(): return 'ok!'
    assert 'ok!' == User.get_stuff()
    flexmock(User).should_receive('get_stuff')
    assert User.get_stuff() is None
    self._tear_down()
    assert 'ok!' == User.get_stuff()

  def test_flexmock_should_properly_restore_undecorated_static_methods(self):
    class User:
      def get_stuff(): return 'ok!'
      get_stuff = staticmethod(get_stuff)
    assert 'ok!' == User.get_stuff()
    flexmock(User).should_receive('get_stuff')
    assert User.get_stuff() is None
    self._tear_down()
    assert 'ok!' == User.get_stuff()

  def test_flexmock_should_properly_restore_module_level_functions(self):
    if 'flexmock_test' in sys.modules:
      mod = sys.modules['flexmock_test']
    else:
      mod = sys.modules['__main__']
    flexmock(mod).should_receive('module_level_function')
    assert None ==  module_level_function(1, 2)
    self._tear_down()
    assert '1, 2' == module_level_function(1, 2)

  def test_flexmock_should_properly_restore_class_methods(self):
    class User:
      @classmethod
      def get_stuff(cls):
        return cls.__name__
    assert 'User' == User.get_stuff()
    flexmock(User).should_receive('get_stuff').and_return('foo')
    assert 'foo' == User.get_stuff()
    self._tear_down()
    assert 'User' == User.get_stuff()

  def test_and_execute_should_match_return_value_class(self):
    class User: pass
    user = User()
    foo = flexmock(foo=lambda: ('bar', 'baz'),
                   bar=lambda: user,
                   baz=lambda: None,
                   bax=lambda: None)
    foo.should_receive('foo').and_execute.and_return(str, str)
    foo.should_receive('bar').and_execute.and_return(User)
    foo.should_receive('baz').and_execute.and_return(object)
    foo.should_receive('bax').and_execute.and_return(None)
    assert ('bar', 'baz') == foo.foo()
    assert user == foo.bar()
    assert None == foo.baz()
    assert None == foo.bax()

  def test_new_instances_should_blow_up_on_should_receive(self):
    class User(object): pass
    mock = flexmock(User).new_instances(None).mock
    assertRaises(FlexmockError, mock.should_receive, 'foo')

  def test_should_call_alias_should_receive_and_execute(self):
    class Foo:
      def get_stuff(self):
        return 'yay'
    foo = Foo()
    flexmock(foo).should_call('get_stuff').and_return('yay').once
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_should_fail_mocking_nonexistent_methods(self):
    class User: pass
    user = User()
    assertRaises(MethodDoesNotExist,
                 flexmock(user).should_receive, 'nonexistent')

  def test_flexmock_should_not_explode_on_unicode_formatting(self):
    if sys.version_info >= (3, 0):
      formatted = _format_args(
          'method', {'kargs' : (chr(0x86C7),), 'kwargs' : {}})
      assert formatted == 'method("蛇")'
    else:
      formatted = _format_args(
          'method', {'kargs' : (unichr(0x86C7),), 'kwargs' : {}})
      assert formatted == 'method("%s")' % unichr(0x86C7)

  def test_return_value_should_not_explode_on_unicode_values(self):
    class Foo:
      def method(self): pass
    if sys.version_info >= (3, 0):
      return_value = ReturnValue(chr(0x86C7))
      assert '%s' % return_value == '蛇'
    else:
      return_value = ReturnValue(unichr(0x86C7))
      assert unicode(return_value) == unichr(0x86C7)

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
    assert obj.n == 1
  
  def test_should_call_works_for_same_method_with_different_args(self):
    class Foo:
      def method(self, arg):
        pass
    foo = Foo()
    flexmock(foo).should_call('method').with_args('foo').once
    flexmock(foo).should_call('method').with_args('bar').once
    foo.method('foo')
    foo.method('bar')
    self._tear_down()

  def test_should_call_fails_properly_for_same_method_with_different_args(self):
    class Foo:
      def method(self, arg):
        pass
    foo = Foo()
    flexmock(foo).should_call('method').with_args('foo').once
    flexmock(foo).should_call('method').with_args('bar').once
    foo.method('foo')
    assertRaises(MethodNotCalled, self._tear_down)

  def test_flexmock_should_give_reasonable_error_for_builtins(self):
    assertRaises(AttemptingToMockBuiltin, flexmock, object)

  def test_mock_chained_method_calls_works_with_one_level(self):
    class Foo:
      def method2(self):
        return 'foo'
    class Bar:
      def method1(self):
        return Foo()
    foo = Bar()
    assert 'foo' == foo.method1().method2()
    flexmock(foo).should_receive('method1.method2').and_return('bar')
    assert 'bar' == foo.method1().method2()

  def test_mock_chained_method_supports_args_and_mocks(self):
    class Foo:
      def method2(self, arg):
        return arg
    class Bar:
      def method1(self):
        return Foo()
    foo = Bar()
    assert 'foo' == foo.method1().method2('foo')
    flexmock(foo).should_receive('method1.method2').with_args(
        'foo').and_return('bar').once
    assert 'bar' == foo.method1().method2('foo')
    self._tear_down()
    flexmock(foo).should_receive('method1.method2').with_args(
        'foo').and_return('bar').once
    assertRaises(MethodNotCalled, self._tear_down)

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
    assert 'foo' == foo.method1().method2().method3()
    flexmock(foo).should_receive('method1.method2.method3').and_return('bar')
    assert 'bar' == foo.method1().method2().method3()

  def test_flexmock_should_replace_method(self):
    class Foo:
      def method(self, arg):
        return arg
    foo = Foo()
    flexmock(foo).should_receive('method').replace_with(lambda x: x == 5)
    assert foo.method(5) == True
    assert foo.method(4) == False

  def test_flexmock_should_mock_the_same_method_multiple_times(self):
    class Foo:
      def method(self): pass
    foo = Foo()
    flexmock(foo).should_receive('method').and_return(1)
    assert foo.method() == 1
    flexmock(foo).should_receive('method').and_return(2)
    assert foo.method() == 2
    flexmock(foo).should_receive('method').and_return(3)
    assert foo.method() == 3
    flexmock(foo).should_receive('method').and_return(4)
    assert foo.method() == 4

  def test_new_instances_should_be_a_method(self):
    class Foo(object): pass
    flexmock(Foo).new_instances('bar')
    assert 'bar' == Foo()
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
    assert 'foo' == Foo()
    assert 'bar' == Foo()

  def test_should_receive_should_not_replace_flexmock_methods(self):
    class Foo:
      def bar(self): pass
    foo = Foo()
    flexmock(foo)
    assertRaises(FlexmockError, foo.should_receive, 'should_receive')


class TestFlexmockUnittest(RegularClass, unittest.TestCase):
  def _tear_down(self):
    return unittest.TestCase.tearDown(self)


if __name__ == '__main__':
  unittest.main()
