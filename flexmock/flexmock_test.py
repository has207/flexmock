from flexmock import FlexMock
import unittest

class TestFlexMock(unittest.TestCase):
  def setUp(self):
    self.mock = FlexMock('temp')

  def test_flexmock_should_create_mock_object_from_string(self):
    mock = FlexMock('temp')
    self.assertEqual(FlexMock, mock.__class__)
  
  def test_flexmock_should_add_expectations(self):
    self.mock.should_receive('method_foo')
    self.assertTrue('method_foo' in [x.method for x in self.mock.expectations()])
  
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
    self.assertEqual(None, self.mock.times_called('nonexistent_method'))
    self.assertEqual(0, self.mock.times_called('method_foo'))
    self.mock.method_foo()
    self.assertEqual(1, self.mock.times_called('method_foo'))
    self.mock.method_foo()
    self.assertEqual(2, self.mock.times_called('method_foo'))
  
  def test_flexmock_expectations_returns_all(self):
    self.assertEqual([], self.mock.expectations())
    self.mock.should_receive('method_foo')
    self.assertEqual(1, len(self.mock.expectations()))
  
  def test_flexmock_expectations_returns_named_expectation(self):
    self.mock.should_receive('method_foo')
    self.assertEqual('method_foo', self.mock.expectations('method_foo').method)
  
  def test_flexmock_expectations_returns_none_if_not_found(self):
    self.assertEqual(None, self.mock.expectations('method_foo'))
  
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
    self.assertEqual(0, self.mock.times_called('method_foo', 'foo'))
    self.assertEqual(2, self.mock.times_called('method_foo', 'bar'))
    self.assertEqual(1, self.mock.times_called('method_foo', 'baz'))
  
  def test_flexmock_should_set_expectation_call_numbers(self):
    self.mock.should_receive('method_foo').times(1)
    self.assertFalse(self.mock.verify_expectations())
    self.mock.method_foo()
    self.assertTrue(self.mock.verify_expectations())
  
  def test_flexmock_should_check_raised_exceptions(self):
    class FakeException(Exception):
      pass
    self.mock.should_receive('method_foo').and_raise(FakeException)
    self.assertRaises(FakeException, self.mock.method_foo)
    self.assertEqual(1, self.mock.expectations('method_foo').times_called)

  def test_expectation_should_return_mock(self):
    self.assertEqual(self.mock, self.mock.should_receive('method_foo').mock)

if __name__ == '__main__':
    unittest.main()
