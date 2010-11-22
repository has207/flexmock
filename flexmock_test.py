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
    self.assertEqual('temp', mock.name)
  
  def test_flexmock_should_create_mock_object_from_dict(self):
    mock = FlexMock('temp', foo='foo', bar='bar')
    self.assertEqual(FlexMock, mock.__class__)
    self.assertEqual('temp', mock.name)
    self.assertEqual('foo', mock.foo)
    self.assertEqual('bar', mock.bar)
  
  def test_flexmock_should_add_expectations(self):
    self.mock.should_receive('method_foo')
    self.assertTrue('method_foo' in
        [x.method for x in self.mock._flexmock_expectations_])
  
  def test_flexmock_should_return_value(self):
    self.mock.should_receive('method_foo').and_return('value_bar')
    self.mock.should_receive('method_bar').and_return('value_baz')
    self.assertEqual('value_bar', self.mock.method_foo())
    self.assertEqual('value_baz', self.mock.method_bar())

  def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
    class Foo: pass
    foo = Foo()
    FlexMock(foo, method1='returning 1', method2='returning 2')
    self.assertEqual('returning 1', foo.method1())
    self.assertEqual('returning 2', foo.method2())
  
  def test_flexmock_expectations_returns_all(self):
    self.assertEqual([], self.mock._flexmock_expectations_)
    self.mock.should_receive('method_foo')
    self.mock.should_receive('method_bar')
    self.assertEqual(2, len(self.mock._flexmock_expectations_))
  
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

  def test_flexmock_should_match_any_args_by_default(self):
    self.mock.should_receive('method_foo').and_return('bar')
    self.mock.should_receive('method_foo', args=('baz',), return_value='baz')
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
    FlexMock(user)
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
    FlexMock(user)
    user.should_receive('get_name').and_return('john')
    user.set_name('mike')
    self.assertEqual('john', user.get_name())

  def test_flexmock_should_create_partial_new_style_class_mock(self):
    class User(object):
      def __init__(self):
        pass
    FlexMock(User)
    User.should_receive('get_name').and_return('mike')
    user = User()
    self.assertEqual('mike', user.get_name())

  def test_flexmock_should_create_partial_old_style_class_mock(self):
    class User:
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

  def test_flexmock_configures_global_expectations_list(self):
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

  def test_flexmock_get_flexmock_expectations_should_work_with_args(self):
    self.mock.should_receive('method_foo').with_args('value_bar')
    self.assertTrue(
        self.mock._get_flexmock_expectations('method_foo', 'value_bar'))

  def test_flexmock_should_convert_old_style_class_to_new_style(self):
    class User: pass
    User = FlexMock._convert_to_new_style(User)
    self.assertTrue('__new__' in dir(User))

  def test_flexmock_should_not_convert_new_style_class(self):
    class User(object): pass
    saved_user = User
    User = FlexMock._convert_to_new_style(User)
    self.assertTrue(User is saved_user)

  def test_flexmock_should_revert_class_to_original(self):
    class User: pass
    saved_user = User
    User = FlexMock._convert_to_new_style(User)
    if '__new__' not in dir(User):
      self.assertFalse(User is saved_user)
    User = FlexMock._restore_class(User)
    self.assertTrue(User is saved_user)

  def test_flexmock_should_not_revert_new_style_class(self):
    class User(object): pass
    saved_user = User
    User = FlexMock._restore_class(User)
    self.assertTrue(User is saved_user)

  def test_flexmock_should_not_mock_the_same_object_twice(self):
    class User(object): pass
    user = User()
    FlexMock(user)
    self.assertRaises(AlreadyMocked, FlexMock, user)

  def test_flexmock_should_force_mock_the_same_object(self):
    class User(object): pass
    user = User()
    FlexMock(user)
    FlexMock(user, force=True)

  #def test_flexmock_should_mock_new_instances_of_old_style_classes(self):
    #class User(): pass
    #class Group(): pass
    #user = User()
    #FlexMock(Group, new_instances=user)
    #self.assertTrue(user is Group())

  def test_flexmock_should_mock_new_instances(self):
    class User(object): pass
    class Group(object): pass
    user = User()
    FlexMock(Group, new_instances=user)
    self.assertTrue(user is Group())

  def test_flexmock_should_revert_new_instances_on_teardown(self):
    class User(object): pass
    class Group(object): pass
    user = User()
    group = Group()
    FlexMock(Group, new_instances=user)
    self.assertTrue(user is Group())
    unittest.TestCase.tearDown(self)
    self.assertEqual(group.__class__, Group().__class__)
    
  def test_flexmock_should_cleanup_added_methods_and_attributes(self):
    class Group(object): pass
    FlexMock(Group)
    unittest.TestCase.tearDown(self)
    for method in FlexMock.UPDATED_ATTRS:
      self.assertFalse(method in dir(Group), '%s is still in Group' % method)


if __name__ == '__main__':
    unittest.main()
