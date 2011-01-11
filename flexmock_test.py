from flexmock import FlexMock
from flexmock import AlreadyMocked
from flexmock import AndExecuteInvalidMethod
from flexmock import AndExecuteNotSupportedForClassMocks
from flexmock import Expectation
from flexmock import FlexmockException
from flexmock import InvalidMethodSignature
from flexmock import InvalidExceptionClass
from flexmock import InvalidExceptionMessage
from flexmock import MethodNotCalled
from flexmock import MethodCalledOutOfOrder
from flexmock import flexmock
import sys
import unittest


def module_level_function(some, args):
  return "%s, %s" % (some, args)


class Testflexmock(unittest.TestCase):
  def setUp(self):
    self.mock = flexmock(name='temp')

  def test_flexmock_should_create_mock_object(self):
    mock = flexmock()
    self.assertEqual(FlexMock, type(mock))

  def test_flexmock_should_create_mock_object_from_dict(self):
    mock = flexmock(foo='foo', bar='bar')
    self.assertEqual(FlexMock, type(mock))
    self.assertEqual('foo', mock.foo)
    self.assertEqual('bar', mock.bar)

  def test_flexmock_should_add_expectations(self):
    self.mock.should_receive('method_foo')
    self.assertTrue('method_foo' in
        [x.method for x in self.mock._flexmock_expectations])

  def test_flexmock_should_return_value(self):
    self.mock.should_receive('method_foo').and_return('value_bar')
    self.mock.should_receive('method_bar').and_return('value_baz')
    self.assertEqual('value_bar', self.mock.method_foo())
    self.assertEqual('value_baz', self.mock.method_bar())

  def test_flexmock_should_accept_shortcuts_for_creating_mock_object(self):
    mock = flexmock(attr1='value 1', attr2=lambda: 'returning 2')
    self.assertEqual('value 1', mock.attr1)
    self.assertEqual('returning 2', mock.attr2())

  def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo, method1='returning 1', method2='returning 2')
    self.assertEqual('returning 1', foo.method1())
    self.assertEqual('returning 2', foo.method2())
    self.assertEqual('returning 2', foo.method2())

  def test_flexmock_expectations_returns_all(self):
    self.assertEqual(0, len(self.mock._flexmock_expectations))
    self.mock.should_receive('method_foo')
    self.mock.should_receive('method_bar')
    self.assertEqual(2, len(self.mock._flexmock_expectations))

  def test_flexmock_expectations_returns_named_expectation(self):
    self.mock.should_receive('method_foo')
    self.assertEqual(
        'method_foo',
        self.mock._get_flexmock_expectation('method_foo').method)

  def test_flexmock_expectations_returns_none_if_not_found(self):
    self.assertEqual(
        None, self.mock._get_flexmock_expectation('method_foo'))

  def test_flexmock_should_check_parameters(self):
    self.mock.should_receive('method_foo').with_args('bar').and_return(1)
    self.mock.should_receive('method_foo').with_args('baz').and_return(2)
    self.assertEqual(1, self.mock.method_foo('bar'))
    self.assertEqual(2, self.mock.method_foo('baz'))

  def test_flexmock_should_keep_track_of_calls(self):
    self.mock.should_receive('method_foo').with_args('foo').and_return(0)
    self.mock.should_receive('method_foo').with_args('bar').and_return(1)
    self.mock.should_receive('method_foo').with_args('baz').and_return(2)
    self.mock.method_foo('bar')
    self.mock.method_foo('bar')
    self.mock.method_foo('baz')
    expectation = self.mock._get_flexmock_expectation('method_foo', ('foo',))
    self.assertEqual(0, expectation.times_called)
    expectation = self.mock._get_flexmock_expectation('method_foo', ('bar',))
    self.assertEqual(2, expectation.times_called)
    expectation = self.mock._get_flexmock_expectation('method_foo', ('baz',))
    self.assertEqual(1, expectation.times_called)

  def test_flexmock_should_set_expectation_call_numbers(self):
    self.mock.should_receive('method_foo').times(1)
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertRaises(MethodNotCalled, expectation.verify)
    self.mock.method_foo()
    expectation.verify()

  def test_flexmock_should_check_raised_exceptions(self):
    class FakeException(Exception):
      pass
    self.mock.should_receive('method_foo').and_raise(FakeException)
    self.assertRaises(FakeException, self.mock.method_foo)
    self.assertEqual(1, self.mock._get_flexmock_expectation(
        'method_foo').times_called)

  def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    self.mock.should_receive('method_foo').and_raise(FakeException(1, arg2=2))
    self.assertRaises(FakeException, self.mock.method_foo)
    self.assertEqual(1, self.mock._get_flexmock_expectation(
        'method_foo').times_called)

  def test_flexmock_should_check_raised_exceptions_class_with_args(self):
    class FakeException(Exception):
      def __init__(self, arg, arg2):
        pass
    self.mock.should_receive('method_foo').and_raise(FakeException, 1, arg2=2)
    self.assertRaises(FakeException, self.mock.method_foo)
    self.assertEqual(1, self.mock._get_flexmock_expectation(
        'method_foo').times_called)

  def test_flexmock_should_match_any_args_by_default(self):
    self.mock.should_receive('method_foo').and_return('bar')
    self.mock.should_receive('method_foo').with_args('baz').and_return('baz')
    self.assertEqual('bar', self.mock.method_foo())
    self.assertEqual('bar', self.mock.method_foo(1))
    self.assertEqual('bar', self.mock.method_foo('foo', 'bar'))
    self.assertEqual('baz', self.mock.method_foo('baz'))

  def test_expectation_dot_mock_should_return_mock(self):
    self.assertEqual(self.mock, self.mock.should_receive('method_foo').mock)

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
    self.assertEqual('john', user.get_name())

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
    self.assertEqual('john', user.get_name())

  def test_flexmock_should_create_partial_new_style_class_mock(self):
    class User(object):
      def __init__(self):
        pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    self.assertEqual('mike', user.get_name())

  def test_flexmock_should_create_partial_old_style_class_mock(self):
    class User:
      def __init__(self):
        pass
    flexmock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    self.assertEqual('mike', user.get_name())

  def test_flexmock_should_match_expectations_against_builtin_classes(self):
    self.mock.should_receive('method_foo').with_args(str).and_return('got a string')
    self.mock.should_receive('method_foo').with_args(int).and_return('got an int')
    self.assertEqual('got a string', self.mock.method_foo('string!'))
    self.assertEqual('got an int', self.mock.method_foo(23))
    self.assertRaises(InvalidMethodSignature, self.mock.method_foo, 2.0)

  def test_flexmock_should_match_expectations_against_user_defined_classes(self):
    class Foo:
      pass
    self.mock.should_receive('method_foo').with_args(Foo).and_return('got a Foo')
    self.assertEqual('got a Foo', self.mock.method_foo(Foo()))
    self.assertRaises(InvalidMethodSignature, self.mock.method_foo, 1)

  def test_flexmock_configures_global_mocks_dict(self):
    for expectations in self._flexmock_objects.values():
      self.assertEqual(0, len(expectations))
    self.mock.should_receive('method_foo')
    for expectations in self._flexmock_objects.values():
      self.assertEqual(1, len(expectations))

  def test_flexmock_teardown_verifies_mocks(self):
    self.mock.should_receive('verify_expectations').times(1)
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_teardown_does_not_verify_stubs(self):
    self.mock.should_receive('verify_expectations')
    unittest.TestCase.tearDown(self)

  def test_flexmock_preserves_stubbed_object_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    flexmock(user).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertEqual('mike', user.get_name())

  def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    flexmock(User).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertEqual('mike', user.get_name())

  def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
    class User: pass
    user = User()
    flexmock(user).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))

  def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
    class User: pass
    user = User()
    flexmock(User).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))

  def test_flexmock_removes_stubs_from_multiple_objects_on_teardown(self):
    class User: pass
    class Group: pass
    user = User()
    group = User()
    flexmock(user).should_receive('get_name').and_return('john').once
    flexmock(group).should_receive('get_name').and_return('john').once
    self.assertEqual('john', user.get_name())
    self.assertEqual('john', group.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))
    self.assertFalse(hasattr(group, 'get_name'))
    flexmock(user)

  def test_flexmock_removes_stubs_from_multiple_classes_on_teardown(self):
    class User: pass
    class Group: pass
    user = User()
    group = User()
    flexmock(User).should_receive('get_name').and_return('john')
    flexmock(Group).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    self.assertEqual('john', group.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))
    self.assertFalse(hasattr(group, 'get_name'))
    flexmock(User)

  def test_flexmock_respects_at_least_when_called_less_than_requested(self):
    self.mock.should_receive('method_foo').and_return('bar').at_least.twice
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_LEAST, expectation.modifier)
    self.mock.method_foo()
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_respects_at_least_when_called_requested_number(self):
    self.mock.should_receive('method_foo').and_return('value_bar').at_least.once
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_LEAST, expectation.modifier)
    self.mock.method_foo()
    unittest.TestCase.tearDown(self)

  def test_flexmock_respects_at_least_when_called_more_than_requested(self):
    self.mock.should_receive('method_foo').and_return('value_bar').at_least.once
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_LEAST, expectation.modifier)
    self.mock.method_foo()
    self.mock.method_foo()
    unittest.TestCase.tearDown(self)

  def test_flexmock_respects_at_most_when_called_less_than_requested(self):
    self.mock.should_receive('method_foo').and_return('bar').at_most.twice
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_MOST, expectation.modifier)
    self.mock.method_foo()
    unittest.TestCase.tearDown(self)

  def test_flexmock_respects_at_most_when_called_requested_number(self):
    self.mock.should_receive('method_foo').and_return('value_bar').at_most.once
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_MOST, expectation.modifier)
    self.mock.method_foo()
    unittest.TestCase.tearDown(self)

  def test_flexmock_respects_at_most_when_called_more_than_requested(self):
    self.mock.should_receive('method_foo').and_return('value_bar').at_most.once
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(Expectation.AT_MOST, expectation.modifier)
    self.mock.method_foo()
    self.mock.method_foo()
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_treats_once_as_times_one(self):
    self.mock.should_receive('method_foo').and_return('value_bar').once
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(1, expectation.expected_calls)
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_treats_twice_as_times_two(self):
    self.mock.should_receive('method_foo').twice.and_return('value_bar')
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(2, expectation.expected_calls)
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_works_with_never(self):
    self.mock.should_receive('method_foo').and_return('value_bar').never
    expectation = self.mock._get_flexmock_expectation('method_foo')
    self.assertEqual(0, expectation.expected_calls)
    unittest.TestCase.tearDown(self)

  def test_flexmock_get_flexmock_expectation_should_work_with_args(self):
    self.mock.should_receive('method_foo').with_args('value_bar')
    self.assertTrue(
        self.mock._get_flexmock_expectation('method_foo', 'value_bar'))

  def test_flexmock_function_should_return_previously_mocked_object(self):
    class User(object): pass
    user = User()
    foo = flexmock(user)
    self.assertEqual(foo._mock, flexmock(user))

  def test_flexmock_should_not_return_class_object_if_mocking_instance(self):
    class User: pass
    user = User()
    user2 = User()
    class_mock = flexmock(User).should_receive(
        'method').and_return('class').mock
    user_mock = flexmock(user).should_receive(
        'method').and_return('instance').mock
    self.assertTrue(class_mock is not user_mock)
    self.assertEquals('instance', user.method())
    self.assertEquals('class', user2.method())

  def test_flexmock_should_blow_up_on_and_execute_for_invalid_method(self):
    class User: pass
    user = User()
    mock = flexmock(user).should_receive('foo').and_execute
    self.assertRaises(AndExecuteInvalidMethod, user.foo)

  def test_flexmock_should_blow_up_on_and_execute_for_class_mock(self):
    class User:
      def foo(self):
        return 'class'
    user = User()
    try:
      flexmock(User).should_receive('foo').and_execute
      raise Exception('and_execute should have raised an exception')
    except AndExecuteNotSupportedForClassMocks:
      pass

  def test_flexmock_should_mock_new_instances(self):
    class User(object): pass
    class Group(object): pass
    user = User()
    flexmock(Group, new_instances=user)
    self.assertTrue(user is Group())

  def test_flexmock_should_mock_new_instances_with_multiple_params(self):
    class User(object): pass
    class Group(object):
      def __init__(self, arg, arg2):
        pass
    user = User()
    flexmock(Group, new_instances=user)
    self.assertTrue(user is Group(1, 2))

  def test_flexmock_should_revert_new_instances_on_teardown(self):
    class User(object): pass
    class Group(object): pass
    user = User()
    group = Group()
    flexmock(Group, new_instances=user)
    self.assertTrue(user is Group())
    unittest.TestCase.tearDown(self)
    self.assertEqual(group.__class__, Group().__class__)

  def test_flexmock_should_cleanup_added_methods_and_attributes(self):
    class Group(object): pass
    flexmock(Group)
    unittest.TestCase.tearDown(self)
    for method in FlexMock.UPDATED_ATTRS:
      self.assertFalse(method in dir(Group), '%s is still in Group' % method)

  def test_flexmock_should_cleanup_after_exception(self):
    class User: pass
    class Group: pass
    flexmock(Group)
    flexmock(User)
    Group.should_receive('method1').once
    User.should_receive('method2').once
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)
    for method in FlexMock.UPDATED_ATTRS:
      self.assertFalse(method in dir(Group), '%s is still in Group' % method)
    for method in FlexMock.UPDATED_ATTRS:
      self.assertFalse(method in dir(User), '%s is still in User' % method)

  def test_flexmock_and_execute_respects_matched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self, arg):
        return arg
    group = Group()
    flexmock(group).should_receive('method1').twice.and_execute
    self.assertEqual('a:c', group.method1('a', arg2='c'))
    self.assertEqual('a:b', group.method1('a'))
    group.should_receive('method2').once.with_args('c').and_execute
    self.assertEqual('c', group.method2('c'))
    unittest.TestCase.tearDown(self)

  def test_flexmock_and_execute_respects_unmatched_expectations(self):
    class Group(object):
      def method1(self, arg1, arg2='b'):
        return '%s:%s' % (arg1, arg2)
      def method2(self): pass
    group = Group()
    flexmock(group).should_receive('method1').at_least.once.and_execute
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)
    flexmock(group)
    group.should_receive('method2').with_args('a').once.and_execute
    group.should_receive('method2').with_args('not a')
    group.method2('not a')
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_doesnt_error_on_properly_ordered_expectations(self):
    class Foo(object): pass
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
    class Foo(object): pass
    flexmock(Foo)
    Foo.should_receive('foo')
    Foo.should_receive('method1').with_args('a').ordered
    Foo.should_receive('bar')
    Foo.should_receive('method1').with_args('b').ordered
    Foo.should_receive('baz')
    Foo.bar()
    Foo.bar()
    Foo.foo()
    self.assertRaises(MethodCalledOutOfOrder, Foo.method1, 'b')

  def test_flexmock_should_accept_multiple_return_values(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 5).and_return(2)
    self.assertEqual((1, 5), foo.method1())
    self.assertEqual(2, foo.method1())
    self.assertEqual((1, 5), foo.method1())
    self.assertEqual(2, foo.method1())

  def test_flexmock_should_accept_multiple_return_values_with_shortcut(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1, 2).one_by_one
    self.assertEqual(1, foo.method1())
    self.assertEqual(2, foo.method1())
    self.assertEqual(1, foo.method1())
    self.assertEqual(2, foo.method1())

  def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').and_return(1).and_raise(Exception)
    self.assertEqual(1, foo.method1())
    self.assertRaises(Exception, foo.method1)
    self.assertEqual(1, foo.method1())
    self.assertRaises(Exception, foo.method1)

  def test_flexmock_should_match_types_on_multiple_arguments(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(str, int).and_return('ok')
    self.assertEqual('ok', foo.method1('some string', 12))
    self.assertRaises(InvalidMethodSignature, foo.method1, 12, 32)
    self.assertRaises(InvalidMethodSignature, foo.method1, 12, 'some string')
    self.assertRaises(InvalidMethodSignature, foo.method1, 'string', 12, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_generic(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(
        object, object, object).and_return('ok')
    self.assertEqual('ok', foo.method1('some string', None, 12))
    self.assertEqual('ok', foo.method1((1,), None, 12))
    self.assertEqual('ok', foo.method1(12, 14, []))
    self.assertEqual('ok', foo.method1('some string', 'another one', False))
    self.assertRaises(InvalidMethodSignature, foo.method1, 'string', 12)
    self.assertRaises(InvalidMethodSignature, foo.method1, 'string', 12, 13, 14)

  def test_flexmock_should_match_types_on_multiple_arguments_classes(self):
    class Foo: pass
    class Bar: pass
    foo = Foo()
    bar = Bar()
    flexmock(foo).should_receive('method1').with_args(
        object, Bar).and_return('ok')
    self.assertEqual('ok', foo.method1('some string', bar))
    self.assertRaises(InvalidMethodSignature, foo.method1, bar, 'some string')
    self.assertRaises(InvalidMethodSignature, foo.method1, 12, 'some string')

  def test_flexmock_should_match_keyword_arguments(self):
    class Foo: pass
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2).twice
    foo.method1(1, arg2=2, arg3=3)
    foo.method1(1, arg3=3, arg2=2)
    unittest.TestCase.tearDown(self)
    flexmock(foo).should_receive('method1').with_args(1, arg3=3, arg2=2)
    self.assertRaises(InvalidMethodSignature, foo.method1, arg2=2, arg3=3)
    self.assertRaises(InvalidMethodSignature, foo.method1, 1, arg2=2, arg3=4)
    self.assertRaises(InvalidMethodSignature, foo.method1, 1)

  def test_flexmock_should_match_keyword_arguments_works_with_and_execute(self):
    class Foo:
      def method1(self, arg1, arg2=None, arg3=None):
        return '%s%s%s' % (arg1, arg2, arg3)
    foo = Foo()
    flexmock(foo).should_receive('method1').with_args(
        1, arg3=3, arg2=2).and_execute.once
    self.assertEqual('123', foo.method1(1, arg2=2, arg3=3))

  def test_flexmock_should_mock_private_methods(self):
    class Foo:
      def __private_method(self):
        return 'foo'
      def public_method(self):
        return self.__private_method()
    foo = Foo()
    flexmock(foo).should_receive('__private_method').and_return('bar')
    self.assertEqual('bar', foo.public_method())

  def test_flexmock_should_mock_generators(self):
    class Gen: pass
    gen = Gen()
    flexmock(gen).should_receive('foo').and_yield(*range(1, 10))
    output = [val for val in gen.foo()]
    self.assertEqual([val for val in range(1, 10)], output)

  def test_flexmock_should_verify_correct_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_return('real', 'stuff')
    self.assertEqual(('real', 'stuff'), user.get_stuff())

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
    self.assertRaises(InvalidExceptionMessage, user.get_stuff)

  def test_flexmock_should_blow_up_on_wrong_exception_type(self):
    class User:
      def get_stuff(self): raise AlreadyMocked('foo')
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_raise(MethodNotCalled)
    self.assertRaises(InvalidExceptionClass, user.get_stuff)

  def test_flexmock_should_blow_up_on_wrong_spy_return_values(self):
    class User:
      def get_stuff(self): return 'real', 'stuff'
      def get_more_stuff(self): return 'other', 'stuff'
    user = User()
    flexmock(user).should_receive(
        'get_stuff').and_execute.and_return('other', 'stuff')
    self.assertRaises(InvalidMethodSignature, user.get_stuff)
    flexmock(user).should_receive(
        'get_more_stuff').and_execute.and_return()
    self.assertRaises(InvalidMethodSignature, user.get_more_stuff)

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
    self.assertEqual(('real', 'stuff'), user.get_stuff())

  def test_flexmock_should_properly_restore_static_methods(self):
    class User:
      @staticmethod
      def get_stuff(): return 'ok!'
    self.assertEqual('ok!', User.get_stuff())
    flexmock(User).should_receive('get_stuff')
    self.assertTrue(User.get_stuff() is None)
    unittest.TestCase.tearDown(self)
    self.assertEqual('ok!', User.get_stuff())

  def test_flexmock_should_properly_restore_undecorated_static_methods(self):
    class User:
      def get_stuff(): return 'ok!'
      get_stuff = staticmethod(get_stuff)
    self.assertEqual('ok!', User.get_stuff())
    flexmock(User).should_receive('get_stuff')
    self.assertTrue(User.get_stuff() is None)
    unittest.TestCase.tearDown(self)
    self.assertEqual('ok!', User.get_stuff())

  def test_flexmock_should_properly_restore_module_level_functions(self):
    flexmock(sys.modules[self.__module__]).should_receive(
        'module_level_function')
    self.assertEqual(None, module_level_function(1, 2))
    unittest.TestCase.tearDown(self)
    self.assertEqual('1, 2', module_level_function(1, 2))

  def test_flexmock_should_properly_restore_class_methods(self):
    class User:
      @classmethod
      def get_stuff(cls):
        return cls.__name__
    self.assertEqual('User', User.get_stuff())
    flexmock(User).should_receive('get_stuff').and_return('foo')
    self.assertEqual('foo', User.get_stuff())
    unittest.TestCase.tearDown(self)
    self.assertEqual('User', User.get_stuff())

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
    self.assertEqual(('bar', 'baz'), foo.foo())
    self.assertEqual(user, foo.bar())
    self.assertEqual(None, foo.baz())
    self.assertEqual(None, foo.bax())

  def test_new_instances_should_blow_up_on_should_receive(self):
    class User(object): pass
    mock = flexmock(User, new_instances=None)
    self.assertRaises(FlexmockException, mock.should_receive, 'foo')


if __name__ == '__main__':
  unittest.main()
