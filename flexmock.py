import new
import unittest


class InvalidMethodSignature(Exception):
  pass


class MethodNotCalled(Exception):
  pass


class Expectation(object):
  def __init__(self, name, mock, args=None, return_value=None):
    self.method = name
    self.original_method = None
    self.args = (args,)
    self.return_value = return_value
    self.times_called = 0
    self.expected_calls = None
    self.exception = None
    self.mock = mock

  def __str__(self):
    return '%s(%s) -> %s' % (self.method, self.args, self.return_value)

  def with_args(self, args):
    self.args = (args,)
    return self

  def and_return(self, value):
    self.return_value = value
    return self

  def times(self, number):
    self.expected_calls = number
    return self

  def once(self):
    return self.times(1)

  def twice(self):
    return self.times(2)

  def never(self):
    return self.times(0)

  def and_raise(self, exception):
    self.exception = exception
    return self

  def verify(self):
    if not self.expected_calls:
      return True
    if self.times_called == self.expected_calls:
      return True
    else:
      raise MethodNotCalled(
          '%s expected to be called %s times, called %s times' %
          (self.method, self.expected_calls, self.times_called))

  def reset(self):
    if self.original_method:
      setattr(self.mock, self.method, self.original_method)
    elif self.method in self.mock.__dict__:
      del(self.mock.__dict__[self.method])


class FlexMock(object):
  def __init__(self, object_class_or_name):
    if isinstance(object_class_or_name, str):
      self.name = object_class_or_name
      self._mock = self
    else:
      self.mock(object_class_or_name)
    self._flexmock_expectations_ = []
    self._update_unittest_teardown()

  def should_receive(self, method, **kwargs):
    args = kwargs.get('args', None)
    return_value = kwargs.get('return_value', None)
    expectation = self._retrieve_or_create_expectation(method, args,
                                                       return_value)
    self._flexmock_expectations_.append(expectation)
    self._add_expectation_to_object(expectation, method)
    return expectation

  def mock(self, obj):
    obj.should_receive = self.should_receive
    obj._get_flexmock_expectations = self._get_flexmock_expectations
    obj._flexmock_expectations_ = []
    self._mock = obj

  def _update_unittest_teardown(self):
    unittest.TestCase._flexmock_expectations = self._flexmock_expectations_
    saved_teardown = unittest.TestCase.tearDown
    def unittest_teardown(self):
      for expectation in self._flexmock_expectations: 
        expectation.verify()
        expectation.reset()
      self._flexmock_expectations = []
      saved_teardown(self)
    unittest.TestCase.tearDown = unittest_teardown

  def _retrieve_or_create_expectation(self, method, args, return_value):
    if method in [x.method for x in self._flexmock_expectations_]:
      expectation = [x for x in self._flexmock_expectations_
                     if x.method == method][0]
      if expectation.args is None:
        expectation.args = args
      else:
        expectation = Expectation(method, self._mock, args, return_value)
    else:
      expectation = Expectation(method, self._mock, args, return_value)
    return expectation

  def _add_expectation_to_object(self, expectation, method):
    method_instance = self.__create_mock_method(method)
    if hasattr(self._mock, method):
      expectation.original_method = getattr(self._mock, method)
    setattr(self._mock, method, new.instancemethod(
        method_instance, self._mock, self.__class__))

  def _get_flexmock_expectations(self, name=None, args=None):
    if name:
      expectation = None
      for e in self._flexmock_expectations_:
        if e.method == name:
          if args:
            if self._match_args(args, e.args):
              expectation = e
          else:
            expectation = e
      return expectation
    else:
      return self._flexmock_expectations_

  def _match_args(self, given_args, expected_args):
    if given_args == expected_args:
      return True
    try:
      if len(given_args) == 1 and isinstance(given_args[0], expected_args[0]):
        return True
    except:
      pass

  def __create_mock_method(self, method):
    def mock_method(self, *kargs, **kwargs):
      arguments = kargs
      expectation = self._get_flexmock_expectations(method, arguments)
      if expectation:
        expectation.times_called += 1
        if expectation.exception:
          raise expectation.exception
        return expectation.return_value
      else:
        raise InvalidMethodSignature(str(arguments))
    return mock_method
