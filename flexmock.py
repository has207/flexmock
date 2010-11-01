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
    self.args = args
    self.return_value = return_value
    self.times_called = 0
    self.expected_calls = None
    self.exception = None
    self.mock = mock

  def __str__(self):
    return '%s(%s) -> %s' % (self.method, self.args, self.return_value)

  def with_args(self, args):
    self.args = args
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
      raise MethodNotCalled(self.method)

  def reset(self):
    if self.original_method:
      setattr(self.mock, self.method, self.original_method)
    else:
      del(self.mock.__dict__[self.method])


class FlexMock(object):
  def __init__(self, object_class_or_name):
    if isinstance(object_class_or_name, str):
      self.name = object_class_or_name
      self.mock = self
    else:
      object_class_or_name.should_receive = self.should_receive
      object_class_or_name.expectations = self.expectations
      object_class_or_name._expectations = []
      self.mock = object_class_or_name
    self._expectations = []
    unittest.TestCase._flexmock_expectations = self._expectations
    saved_teardown = unittest.TestCase.tearDown
    def unittest_teardown(self):
      for expectation in self._flexmock_expectations: 
        expectation.verify()
        expectation.reset()
      self._flexmock_expectations = []
      saved_teardown(self)
    unittest.TestCase.tearDown = unittest_teardown

  def should_receive(self, method, args=None, return_value=None):
    def mock_method(self, *kargs, **kwargs):
      arguments = kargs
      expectation = self.expectations(method, arguments)
      if expectation:
        expectation.times_called += 1
        if expectation.exception:
          raise expectation.exception
        return expectation.return_value
      else:
        raise InvalidMethodSignature(str(arguments))

    if method in [x.method for x in self._expectations]:
      expectation = [x for x in self._expectations if x.method == method][0]
      if expectation.args is None:
        expectation.args = args
      else:
        expectation = Expectation(method, self.mock, args, return_value)
    else:
      expectation = Expectation(method, self.mock, args, return_value)
    self._expectations.append(expectation)
    method_instance = mock_method
    if hasattr(self.mock, method):
      expectation.original_method = getattr(self.mock, method)
    setattr(self.mock, method, new.instancemethod(
        method_instance, self.mock, self.__class__))
    return expectation

  def expectations(self, name=None, args=None):
    if name:
      expectation = None
      for e in self._expectations:
        if e.method == name:
          if args:
            if self._match_args(args, (e.args,)):
              expectation = e
          else:
            expectation = e
      return expectation
    else:
      return self._expectations

  def _match_args(self, given_args, expected_args):
    if given_args == expected_args:
      return True
    try:
      if len(given_args) == 1 and isinstance(given_args[0], expected_args[0]):
        return True
    except:
      pass

  def times_called(self, method, args=None):
    expectation = self.expectations(method, (args,))
    if expectation:
      return expectation.times_called
    else:
      return None
