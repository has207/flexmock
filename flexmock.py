"""Copyright 2010 Herman Sheremetyev. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import inspect
import sys
import types
import unittest


class FlexmockException(Exception):
  pass


class AttemptingToMockBuiltin(Exception):
  def __str__(self):
    out = 'Python does not allow you to mock builtin modules. '
    out += 'Consider wrapping it in a class you can mock instead'
    return out


class InvalidMethodSignature(FlexmockException):
  pass


class InvalidExceptionClass(FlexmockException):
  pass


class InvalidExceptionMessage(FlexmockException):
  pass


class MethodNotCalled(FlexmockException):
  pass


class MethodCalledOutOfOrder(FlexmockException):
  pass


class MethodDoesNotExist(FlexmockException):
  pass


class AlreadyMocked(FlexmockException):
  pass


class AndExecuteNotSupportedForClassMocks(FlexmockException):
  pass


class ReturnValue(object):
  def __init__(self, value=None, raises=None):
    self.value = value
    self.raises = raises

  def __str__(self):
    if self.raises:
      return '%s(%s)' % (self.raises, self.value)
    else:
      return str(self.value)


class FlexmockContainer(object):
  """Holds global hash of object/expectation mappings."""
  flexmock_objects = {}


class Expectation(object):
  """Holds expectations about methods.

  The information contained in the Expectation object includes method name,
  its argument list, return values, and any exceptions that the method might
  raise.
  """

  AT_LEAST = 'at least '
  AT_MOST = 'at most '

  def __init__(self, name, mock, kargs=None, kwargs=None, return_value=None):
    self.method = name
    self.modifier = ''
    self.original_method = None
    self.static = False
    if kargs is None and kwargs is None:
      self.args = None
    else:
      self.args = {'kargs': (), 'kwargs': {}}
      if kargs is not None:
        if isinstance(kargs, tuple):
          self.args['kargs'] = kargs
        else:
          self.args['kargs'] = (kargs,)
      if kwargs is not None:
        self.args['kwargs'] = kwargs
    value = ReturnValue(return_value)
    self.return_values = []
    if return_value is not None:
      self.return_values.append(value)
    self.yield_values = []
    self.times_called = 0
    self.expected_calls = None
    self._mock = mock
    self._pass_thru = False
    self._ordered = False
    self._one_by_one = False

  def __str__(self):
    return '%s -> (%s)' % (FlexMock._format_args(self.method, self.args),
                         ', '.join([str(x) for x in self.return_values]))

  @property
  def mock(self):
    """Return the mock associated with this expectation.

    Since this method is a property it must be called without parentheses.
    """
    return self._mock

  def with_args(self, *kargs, **kwargs):
    """Override the arguments used to match this expectation's method."""
    self.args = {'kargs': kargs, 'kwargs': kwargs}
    return self

  def and_return(self, *value):
    """Override the return value of this expectation's method.

    When and_return is given multiple times, each value provided is returned
    on successive invocations of the method. It is also possible to mix
    and_return with and_raise in the same manner to alternate between returning
    a value and raising and exception on different method invocations.

    When combined with the one_by_one property, value is treated as a list of
    values to be returned in the order specified by successive calls to this
    method rather than a single list to be returned each time.
    """
    if len(value) == 1:
      value = value[0]
    if not self._one_by_one:
      value = ReturnValue(value)
      self.return_values.append(value)
    else:
      try:
        self.return_values.extend([ReturnValue(v) for v in value])
      except TypeError:
        self.return_values.append(ReturnValue(value))
    return self

  def times(self, number):
    """Number of times this expectation's method is expected to be called."""
    self.expected_calls = number
    return self

  @property
  def one_by_one(self):
    """Modifies the return value to be treated as a list of return values.

    Each value in the list is returned on successive invocations of the method.
    """
    if not self._one_by_one:
      self._one_by_one = True
      saved_values = self.return_values[:]
      self.return_values = []
      for value in saved_values:
        try:
          for val in value.value:
            self.return_values.append(ReturnValue(val))
        except TypeError:
          self.return_values.append(value)
    return self

  @property
  def once(self):
    """Alias for times(1)."""
    return self.times(1)

  @property
  def twice(self):
    """Alias for times(2)."""
    return self.times(2)

  @property
  def never(self):
    """Alias for times(0)."""
    return self.times(0)

  @property
  def at_least(self):
    """Modifies the associated "times" expectation."""
    self.modifier = self.AT_LEAST
    return self

  @property
  def at_most(self):
    """Modifies the associated "times" expectation."""
    self.modifier = self.AT_MOST
    return self

  @property
  def and_execute(self):
    """Creates a spy.

    This means that the original method will be called rather than the fake
    version. However, we can still keep track of how many times it's called and
    with what arguments, and apply expectations accordingly.
    """
    if inspect.isclass(self._mock):
      raise AndExecuteNotSupportedForClassMocks
    self._pass_thru = True
    return self

  @property
  def ordered(self):
    """Makes the expectation respect the order of should_receive statements."""
    self._ordered = True
    return self

  def and_raise(self, exception, *kargs, **kwargs):
    """Specifies the exception to be raised when this expectation is met.

    Args:
      exception: class or instance of the exception
      kargs: tuple of kargs to pass to the exception
      kwargs: dict of kwargs to pass to the exception
    """
    args = {'kargs': kargs, 'kwargs': kwargs}
    self.return_values.append(ReturnValue(raises=exception, value=args))
    return self

  def and_yield(self, *kargs):
    """Specifies the list of items to be yielded on successive method calls."""
    for value in kargs:
      self.yield_values.append(ReturnValue(value))
    return self

  def verify(self):
    """Verify that this expectation has been met.

    Raises:
      MethodNotCalled Exception
    """
    if not self.expected_calls:
      return
    failed = False
    if not self.modifier:
      if self.times_called != self.expected_calls:
        failed = True
    elif self.modifier == self.AT_LEAST:
      if self.times_called < self.expected_calls:
        failed = True
    elif self.modifier == self.AT_MOST:
      if self.times_called > self.expected_calls:
        failed = True
    if not failed:
      return
    else:
      raise MethodNotCalled(
          '%s expected to be called %s%s times, called %s times' %
          (FlexMock._format_args(self.method, self.args), self.modifier,
           self.expected_calls, self.times_called))

  def reset(self):
    """Returns the methods overriden by this expectation to their originals."""
    if isinstance(self._mock, FlexMock):
      del self
      return  # no need to worry about mock objects
    if self.original_method:
      if self.static:
        setattr(self._mock, self.method, staticmethod(self.original_method))
      else:
        setattr(self._mock, self.method, self.original_method)
    elif self.method in dir(self._mock):
      delattr(self._mock, self.method)
    for attr in FlexMock.UPDATED_ATTRS:
      if hasattr(self._mock, attr):
        try:
          delattr(self._mock, attr)
        except AttributeError:
          pass
    del self


class FlexMock(object):
  """Creates mock objects or puts existing objects or classes under mock."""

  UPDATED_ATTRS = ['should_receive', 'should_call',
                   '_get_flexmock_expectation', '_flexmock_expectations']

  def __init__(self, **kwargs):
    """FlexMock constructor.

    Args:
      kwargs: dict of attribute/value pairs used to initialize the mock object
    """
    self._flexmock_expectations = []
    self._mock = self
    for attr, value in kwargs.items():
      setattr(self, attr, value)

  def should_receive(self, method):
    """Adds a method Expectation to the provided class or instance.

    Args:
      method: string name of the method to add

    Returns:
      expectation: Expectation object
    """
    self._ensure_not_new_instances()
    if (method.startswith('__') and
        (not inspect.isclass(self._mock) and not inspect.ismodule(self._mock))):
      method = '_%s__%s' % (self._mock.__class__.__name__, method.lstrip('_'))
    if (not isinstance(self._mock, FlexMock) and
        not hasattr(self._mock, method) and
        (not method.startswith('__') and not method.endswith('__'))):
      raise MethodDoesNotExist('%s does not have method %s' % (self, method))
    expectation = self._retrieve_or_create_expectation(method)
    if expectation not in self._flexmock_expectations:
      self._flexmock_expectations.append(expectation)
      self._update_method(expectation, method)
      self.update_teardown()
    return expectation

  def should_call(self, method):
    """Shortcut for creating a spy.

    Alias for should_receive().and_execute.
    """
    return self.should_receive(method).and_execute

  def _ensure_not_new_instances(self):
    for exp in self._flexmock_expectations:
      if exp.original_method and exp.original_method.__name__ == '__new__':
        raise FlexmockException('cannot use should_receive with new_instances')

  def _new_instances(self, return_value):
    """Overrides creation of new instances of the mocked class.

    Args:
      return_value: the object that should be created instead of the default
    """
    method = '__new__'
    expectation = self._retrieve_or_create_expectation(
        method, return_value=return_value)
    self._flexmock_expectations.append(expectation)
    if not expectation.original_method:
      expectation.original_method = getattr(self._mock, method)
    setattr(self._mock, method, self.__create_new_method(return_value))
    self.update_teardown()

  def _setup_mock(self, obj_or_class, **kwargs):
    """Puts the provided object or class under mock."""
    self._ensure_not_already_mocked(obj_or_class)
    for attr in self.UPDATED_ATTRS:
      setattr(obj_or_class, attr, getattr(self, attr))
    self._mock = obj_or_class
    if 'new_instances' in kwargs and inspect.isclass(obj_or_class):
      self._new_instances(kwargs['new_instances'])
    else:
      for method, return_value in kwargs.items():
        obj_or_class.should_receive(method).and_return(return_value)
    expectation = self._retrieve_or_create_expectation()
    self._flexmock_expectations.append(expectation)
    self.update_teardown()

  def _ensure_not_already_mocked(self, obj):
    for attr in self.UPDATED_ATTRS:
      if (hasattr(obj, attr) and
          (hasattr(obj, '__class__') and not hasattr(obj.__class__, attr))):
        raise AlreadyMocked('%s already defines %s' % (obj, attr))

  def update_teardown(self, test_runner=unittest.TestCase,
                      teardown_method='tearDown'):
    """Should be implemented by classes inheriting from FlexMock."""
    if not FlexmockContainer.flexmock_objects:
      FlexmockContainer.flexmock_objects = {self: self._flexmock_expectations}
      if hasattr(test_runner, teardown_method):
        saved_teardown = getattr(test_runner, teardown_method)
      else:
        saved_teardown = None
      setattr(test_runner, teardown_method,
          self._flexmock_teardown(saved_teardown))
    else:
      FlexmockContainer.flexmock_objects[self] = self._flexmock_expectations

  def _flexmock_teardown(self, saved_teardown):
    def teardown(*kargs, **kwargs):
      if saved_teardown:
        saved_teardown(*kargs, **kwargs)
      saved = {}
      for mock_object, expectations in \
          FlexmockContainer.flexmock_objects.items():
        saved[mock_object] = expectations[:]
        for expectation in expectations:
          expectation.reset()
      for mock_object, expectations in saved.items():
        del FlexmockContainer.flexmock_objects[mock_object]
      for mock_object, expectations in saved.items():
        for expectation in expectations:
          expectation.verify()
    return teardown

  def _retrieve_or_create_expectation(self, method=None,
                                      args=None, return_value=None):
    if method in [x.method for x in self._flexmock_expectations]:
      expectation = [x for x in self._flexmock_expectations
                     if x.method == method][0]
      if expectation.args is None and not expectation.return_values:
        expectation.args = args
      else:
        expectation = self._create_expectation(method, args, return_value)
    else:
      expectation = self._create_expectation(method, args, return_value)
    return expectation

  def _create_expectation(self, method, args, return_value):
    if args is None:
      expectation = Expectation(method, self._mock, args, return_value)
    else:
      expectation = Expectation(
          method, self._mock, args['kargs'], args['kwargs'], return_value)
    return expectation

  def _update_method(self, expectation, method):
    method_instance = self.__create_mock_method(method)
    if hasattr(self._mock, method) and not expectation.original_method:
      expectation.original_method = getattr(self._mock, method)
      expectation.static = self._is_static(method)
    setattr(self._mock, method, types.MethodType(
        method_instance, self._mock))

  def _is_static(self, method):
    """Infer whether the method is static based on its properties.

    This way we can re-insert it properly when it's time to clean up.
    This monkeying around is only necessary in Python < 3.0
    """
    if sys.version_info < (3, 0):
      method = getattr(self._mock, method)
      if (not inspect.ismodule(self._mock) and
          inspect.isfunction(method) and not inspect.ismethod(method)):
        return True
    return False

  def _get_flexmock_expectation(self, name=None, args=None):
    """Gets attached to the object under mock and is called in that context."""
    if args == None:
      args = {'kargs': (), 'kwargs': {}}
    if not isinstance(args, dict):
      args = {'kargs': args, 'kwargs': {}}
    if not isinstance(args['kargs'], tuple):
      args['kargs'] = (args['kargs'],)
    if name:
      for e in reversed(self._flexmock_expectations):
        if e.method == name and self._match_args(args, e.args):
          if e._ordered:
            self._verify_call_order(e, args, name)
          return e

  def _verify_call_order(self, e, args, name):
    for exp in self._flexmock_expectations:
      if (exp.method == name and
          not self._match_args(args, exp.args) and
          not exp.times_called):
        raise MethodCalledOutOfOrder(
            '%s called before %s' %
            (FlexMock._format_args(e.method, e.args),
             FlexMock._format_args(exp.method, exp.args)))
      if exp.method == name and self._match_args(args, exp.args):
        break

  def _match_args(self, given_args, expected_args):
    if (given_args == expected_args or expected_args is None or
        expected_args == {'kargs': (), 'kwargs': {}}):
      return True
    if (len(given_args['kargs']) != len(expected_args['kargs']) or
        len(given_args['kwargs']) != len(expected_args['kwargs'])):
      return False
    try:
      for i, arg in enumerate(given_args['kargs']):
        if (arg != expected_args['kargs'][i] and
            not isinstance(arg, expected_args['kargs'][i])):
          return False
      for k, v in given_args['kwargs']:
        if (v != expected_args['kwargs'][k] and
            not isinstance(v, expected_args['kwargs'][k])):
          return False
      return True
    except:
      pass

  def __create_mock_method(self, method):
    def generator_method(yield_values):
      for value in yield_values:
        yield value.value

    def _handle_exception_matching(expectation):
      if expectation.return_values:
        raised, instance = sys.exc_info()[:2]
        message = str(instance)
        expected = expectation.return_values[0].raises
        if not expected:
          raise
        args = expectation.return_values[0].value
        expected_instance = expected(*args['kargs'], **args['kwargs'])
        expected_message = str(expected_instance)
        if inspect.isclass(expected):
          if expected is not raised and not isinstance(raised, expected):
            raise (InvalidExceptionClass('expected %s, raised %s' %
                   (expected, raised)))
          elif expected_message != message:
            raise (InvalidExceptionMessage('expected %s, raised %s' %
                   (expected_message, message)))
        elif expected is not raised:
          raise (InvalidExceptionClass('expected %s, raised %s' %
                 (expected, raised)))

    def match_return_values(expected, received):
      if not received:
        return True
      if not isinstance(expected, tuple):
        expected = (expected,)
      if not isinstance(received, tuple):
        received = (received,)
      if len(received) != len(expected):
        return False
      for i, val in enumerate(received):
        if (val != expected[i] and
            not (inspect.isclass(expected[i]) and
                 isinstance(val, expected[i]))):
          return False
      return True

    def pass_thru(expectation, *kargs, **kwargs):
      return_values = None
      try:
        return_values = expectation.original_method(*kargs, **kwargs)
      except:
        return _handle_exception_matching(expectation)
      if (expectation.return_values and
          not match_return_values(expectation.return_values[0].value,
                                  return_values)):
        raise (InvalidMethodSignature('expected to return %s, returned %s' %
               (expectation.return_values[0].value, return_values)))
      return expectation.original_method(*kargs, **kwargs)

    def mock_method(self, *kargs, **kwargs):
      arguments = {'kargs': kargs, 'kwargs': kwargs}
      expectation = self._get_flexmock_expectation(method, arguments)
      if expectation:
        expectation.times_called += 1
        if expectation._pass_thru:
          return pass_thru(expectation, *kargs, **kwargs)
        if expectation.yield_values:
          return generator_method(expectation.yield_values)
        elif expectation.return_values:
          return_value = expectation.return_values[0]
          expectation.return_values = expectation.return_values[1:]
          expectation.return_values.append(return_value)
        else:
          return_value = ReturnValue()
        if return_value.raises:
          if inspect.isclass(return_value.raises):
            raise return_value.raises(
                *return_value.value['kargs'], **return_value.value['kwargs'])
          else:
            raise return_value.raises
        else:
          return return_value.value
      else:
        raise InvalidMethodSignature(FlexMock._format_args(method, arguments))
    return mock_method

  @staticmethod
  def _format_args(method, arguments):
    def to_str(arg):
      if sys.version_info < (3, 0):
        # prior to 3.0 unicode strings are type unicode that inherits
        # from basestring along with str, in 3.0 both unicode and basestring
        # go away and str handles everything properly
        if isinstance(arg, basestring):
          return '"%s"' % arg
        else:
          return str(arg)
      else:
        if isinstance(arg, str):
          return '"%s"' % arg
        else:
          return str(arg)

    if arguments is None:
      arguments = {'kargs': (), 'kwargs': {}}
    kargs = ', '.join(to_str(arg) for arg in arguments['kargs'])
    kwargs = ', '.join('%s=%s' % (k, to_str(v)) for k, v in
                                  arguments['kwargs'].items())
    if kargs and kwargs:
      args = '%s, %s' % (kargs, kwargs)
    else:
      args = '%s%s' % (kargs, kwargs)
    return '%s(%s)' % (method, args)

  def __create_new_method(self, return_value):
    @staticmethod
    def new(cls, *kargs, **kwargs):
      return return_value
    return new


def _generate_mock(flexmock_class, object_or_class=None, **kwargs):
  """Factory function for creating FlexMock objects.

  Args:
    flexmock_class: class inheriting from FlexMock, used to differentiate
                    different test runners
    object_or_class: object or class to mock
    kwargs: dict of attribute/value pairs used to initialize the mock object
  """
  if object_or_class is None:
    mock = flexmock_class(**kwargs)
  else:
    mock = flexmock_class()
    try:
      mock._setup_mock(object_or_class, **kwargs)
    except TypeError:
      raise AttemptingToMockBuiltin
    except AlreadyMocked:
      mock = object_or_class
  return mock


def flexmock_unittest(object_or_class=None, **kwargs):
  class UnittestFlexMock(FlexMock):
    def update_teardown(self, test_runner=unittest.TestCase,
        teardown_method='tearDown'):
      FlexMock.update_teardown(self, test_runner, teardown_method)
  return _generate_mock(UnittestFlexMock, object_or_class, **kwargs)


def get_current_function():
  try:
    from nose import config
  except ImportError:
    return None
  conf = config.Config()
  func_name = None
  this_func = None
  for i in range(0, 10):
    func_name = sys._getframe(i).f_code.co_name
    if conf.testMatch.match(func_name):
      break
  if func_name in sys._getframe(i).f_globals:
    this_func = sys._getframe(i).f_globals[func_name]
  else:
    for i in range(0, 10):
      if 'self' in sys._getframe(i).f_locals:
        if (func_name in dir(sys._getframe(i).f_locals['self'].__class__) and
           'teardown' in dir(getattr(sys._getframe(i).f_locals['self'].__class__, func_name))):
          this_func = getattr(sys._getframe(i).f_locals['self'].__class__,
              func_name)
          break
  return this_func


def flexmock_nose(object_or_class=None, **kwargs):
  class NoseFlexMock(FlexMock):
    def update_teardown(self, test_runner=None, teardown_method=None):
      this_func = get_current_function()
      if this_func:
        FlexMock.update_teardown(self, this_func, 'teardown')
      else:
        FlexMock.update_teardown(self, unittest.TestCase, 'tearDown')
  return _generate_mock(NoseFlexMock, object_or_class, **kwargs)


flexmock = flexmock_unittest
