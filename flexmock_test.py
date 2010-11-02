from flexmock import *
import unittest

class TestFlexMock(unittest.TestCase):
  def setUp(self):
    self.mock = FlexMock('temp')

  def tearDown(self):
    self._flexmock_expectations = []
    unittest.TestCase.tearDown(self)

  def test_flexmock_should_create_mock_object_from_string(self):
    mock = FlexMock('temp')
    self.assertEqual(FlexMock, mock.__class__)
  
  def test_flexmock_should_add_expectations(self):
    self.mock.should_receive('method_foo')
    self.assertTrue('method_foo' in
        [x.method for x in self.mock._flexmock_expectations_])
  
  def test_flexmock_should_return_value(self):
    self.mock.should_receive('method_foo').and_return('value_bar')
    self.mock.should_receive('method_bar').and_return('value_baz')
    self.assertEqual('value_bar', self.mock.method_foo())
    self.assertEqual('value_baz', self.mock.method_bar())
  
  def test_flexmock_should_check_params(self):
    self.mock = FlexMock('temp')
    self.mock.should_receive('method_foo').with_args('bar').and_return('value_baz')
    self.assertEqual('value_baz', self.mock.method_foo('bar'))
  
  def test_flexmock_should_keep_track_of_method_calls(self):
    self.mock.should_receive('method_foo').and_return('value_bar')
    expectation = self.mock._get_flexmock_expectations('method_foo')
    self.assertEqual(0, expectation.times_called)
    self.mock.method_foo()
    self.assertEqual(1, expectation.times_called)
    self.mock.method_foo()
    self.assertEqual(2, expectation.times_called)
  
  def test_flexmock_expectations_returns_all(self):
    self.assertEqual([], self.mock._flexmock_expectations_)
    self.mock.should_receive('method_foo')
    self.assertEqual(1, len(self.mock._flexmock_expectations_))
  
  def test_flexmock_expectations_returns_named_expectation(self):
    self.mock.should_receive('method_foo')
    self.assertEqual(
        'method_foo',
        self.mock._get_flexmock_expectations('method_foo').method)
  
  def test_flexmock_expectations_returns_none_if_not_found(self):
    self.assertEqual(
        None, self.mock._get_flexmock_expectations('method_foo'))
  
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
    expectation = self.mock._get_flexmock_expectations('method_foo', ('foo',))
    self.assertEqual(0, expectation.times_called)
    expectation = self.mock._get_flexmock_expectations('method_foo', ('bar',))
    self.assertEqual(2, expectation.times_called)
    expectation = self.mock._get_flexmock_expectations('method_foo', ('baz',))
    self.assertEqual(1, expectation.times_called)
  
  def test_flexmock_should_set_expectation_call_numbers(self):
    self.mock.should_receive('method_foo').times(1)
    expectation = self.mock._get_flexmock_expectations('method_foo')
    self.assertRaises(MethodNotCalled, expectation.verify)
    self.mock.method_foo()
    self.assertTrue(expectation.verify())
  
  def test_flexmock_should_check_raised_exceptions(self):
    class FakeException(Exception):
      pass
    self.mock.should_receive('method_foo').and_raise(FakeException)
    self.assertRaises(FakeException, self.mock.method_foo)
    self.assertEqual(1, self.mock._get_flexmock_expectations(
        'method_foo').times_called)

  def test_expectation_should_return_mock(self):
    self.assertEqual(self.mock, self.mock.should_receive('method_foo').mock)

  def test_flexmock_should_create_partial_object_mock(self):
    class User(object):
      def __init__(self, name=None):
        self.name = name
      def get_name(self):
        return self.name
      def set_name(self, name):
        self.name = name
    user = User()
    FlexMock(user)
    user.should_receive('get_name').and_return('john')
    user.set_name('mike')
    self.assertEqual('john', user.get_name())

  def test_flexmock_should_create_partial_class_mock(self):
    class User(object):
      def __init__(self):
        pass
    FlexMock(User)
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

  def test_flexmock_configures_global_expectations(self):
    self.assertFalse(self._flexmock_expectations)
    self.mock.should_receive('method_foo')
    self.assertTrue(self._flexmock_expectations)

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
    FlexMock(user).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertEqual('mike', user.get_name())

  def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
    class User:
      def get_name(self):
        return 'mike'
    user = User()
    FlexMock(User).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertEqual('mike', user.get_name())

  def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
    class User: pass
    user = User()
    FlexMock(user).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))

  def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
    class User: pass
    user = User()
    FlexMock(User).should_receive('get_name').and_return('john')
    self.assertEqual('john', user.get_name())
    unittest.TestCase.tearDown(self)
    self.assertFalse(hasattr(user, 'get_name'))

  def test_flexmock_treats_once_as_times_one(self):
    self.mock.should_receive('method_foo').and_return('value_bar').once()
    expectation = self.mock._get_flexmock_expectations('method_foo')
    self.assertEqual(1, expectation.expected_calls)
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_treats_twice_as_times_two(self):
    self.mock.should_receive('method_foo').and_return('value_bar').twice()
    expectation = self.mock._get_flexmock_expectations('method_foo')
    self.assertEqual(2, expectation.expected_calls)
    self.assertRaises(MethodNotCalled, unittest.TestCase.tearDown, self)

  def test_flexmock_works_with_never(self):
    self.mock.should_receive('method_foo').and_return('value_bar').never()
    expectation = self.mock._get_flexmock_expectations('method_foo')
    self.assertEqual(0, expectation.expected_calls)
    unittest.TestCase.tearDown(self)

  def test_flexmock_get_flexmock_expectations_should_work_with_method(self):
    self.mock.should_receive('method_foo').with_args('value_bar')
    self.assertTrue(self.mock._get_flexmock_expectations('method_foo'))
    
  def test_flexmock_get_flexmock_expectations_should_work_with_args(self):
    self.mock.should_receive('method_foo').with_args('value_bar')
    self.assertTrue(
        self.mock._get_flexmock_expectations('method_foo', ('value_bar',)))


if __name__ == '__main__':
    unittest.main()
