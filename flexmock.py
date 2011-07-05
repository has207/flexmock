"""Copyright 2011 Herman Sheremetyev. All rights reserved.

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
import os
import re
import sys
import types
import unittest
import warnings


class FlexmockError(Exception):
  pass


class AttemptingToMockBuiltin(Exception):
  pass


class InvalidMethodSignature(FlexmockError):
  pass


class InvalidExceptionClass(FlexmockError):
  pass


class InvalidExceptionMessage(FlexmockError):
  pass


class InvalidState(FlexmockError):
  pass


class MethodNotCalled(FlexmockError):
  pass


class MethodCalledOutOfOrder(FlexmockError):
  pass


class MethodDoesNotExist(FlexmockError):
  pass


class AlreadyMocked(FlexmockError):
  pass


class ReturnValue(object):
  def __init__(self, value=None, raises=None):
    self.value = value
    self.raises = raises

  def __str__(self):
    if self.raises:
      return '%s(%s)' % (self.raises, _arg_to_str(self.value))
    else:
      if len(self.value) == 1:
        return '%s' % _arg_to_str(self.value[0])
      else:
        return '(%s)' % ', '.join([_arg_to_str(x) for x in self.value])


class FlexmockContainer(object):
  """Holds global hash of object/expectation mappings."""
  flexmock_objects = {}
  teardown_updated = []

  @classmethod
  def get_flexmock_expectation(cls, obj, name=None, args=None):
    """Gets attached to the object under mock and is called in that context."""
    if args == None:
      args = {'kargs': (), 'kwargs': {}}
    if not isinstance(args, dict):
      args = {'kargs': args, 'kwargs': {}}
    if not isinstance(args['kargs'], tuple):
      args['kargs'] = (args['kargs'],)
    if name and obj in cls.flexmock_objects:
      for e in reversed(cls.flexmock_objects[obj]):
        if e.method == name and _match_args(args, e.args):
          if e._ordered:
            cls._verify_call_order(e, obj, args, name)
          return e

  @classmethod
  def _verify_call_order(cls, e, obj, args, name):
    for exp in cls.flexmock_objects[obj]:
      if (exp.method == name and
          not _match_args(args, exp.args) and
          not exp.times_called):
        raise MethodCalledOutOfOrder(
            '%s called before %s' %
            (_format_args(e.method, e.args),
             _format_args(exp.method, exp.args)))
      if (exp.method == name and
          args and exp.args and  # ignore default stub case
          _match_args(args, exp.args)):
        break

  @classmethod
  def add_expectation(cls, obj, expectation):
    if obj in cls.flexmock_objects:
      cls.flexmock_objects[obj].append(expectation)
    else:
      cls.flexmock_objects[obj] = [expectation]


class Expectation(object):
  """Holds expectations about methods.

  The information contained in the Expectation object includes method name,
  its argument list, return values, and any exceptions that the method might
  raise.
  """

  AT_LEAST = 'at least'
  AT_MOST = 'at most'
  EXACTLY = 'exactly'

  def __init__(self, mock, name=None, return_value=None, original_method=None):
    self.method = name
    self.modifier = self.EXACTLY
    self.original_method = original_method
    self.args = None
    value = ReturnValue(return_value)
    self.return_values = []
    self._replace_with = None
    if return_value is not None:
      self.return_values.append(value)
    self.yield_values = []
    self.times_called = 0
    self.expected_calls = {
        self.EXACTLY: None,
        self.AT_LEAST: None,
        self.AT_MOST: None}
    self.runnable = lambda: True
    self._mock = mock
    self._pass_thru = False
    self._ordered = False
    self._one_by_one = False

  def __str__(self):
    return '%s -> (%s)' % (_format_args(self.method, self.args),
                           ', '.join(['%s' % x for x in self.return_values]))

  def __call__(self):
    return self

  @property
  def mock(self):
    """Return the mock associated with this expectation.

    Since this method is a property it must be called without parentheses.
    """
    return self._mock

  def with_args(self, *kargs, **kwargs):
    """Override the arguments used to match this expectation's method.

    Args:
      - kargs: optional keyword arguments
      - kwargs: optional named arguments

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    self.args = {'kargs': kargs, 'kwargs': kwargs}
    return self

  def and_return(self, *values):
    """Override the return value of this expectation's method.

    When and_return is given multiple times, each value provided is returned
    on successive invocations of the method. It is also possible to mix
    and_return with and_raise in the same manner to alternate between returning
    a value and raising and exception on different method invocations.

    When combined with the one_by_one property, value is treated as a list of
    values to be returned in the order specified by successive calls to this
    method rather than a single list to be returned each time.

    Args:
      - values: optional list of return values, defaults to None if not given

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    if len(values) == 1:
      value = values[0]
    else:
      value = values
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
    """Number of times this expectation's method is expected to be called.

    Args:
      - number: int

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    self.expected_calls[self.modifier] = number
    return self

  @property
  def one_by_one(self):
    """Modifies the return value to be treated as a list of return values.

    Each value in the list is returned on successive invocations of the method.

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
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
    """Alias for times(1).

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    return self.times(1)

  @property
  def twice(self):
    """Alias for times(2).

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    return self.times(2)

  @property
  def never(self):
    """Alias for times(0).

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    return self.times(0)

  @property
  def at_least(self):
    """Modifies the associated times() expectation.

    When given, an exception will only be raised if the method is called less
    than times() specified. Does nothing if times() is not given.

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    if (self.expected_calls[self.AT_LEAST] is not None or
        self.modifier == self.AT_LEAST):
      raise FlexmockError('cannot use at_least modifier twice')
    if (self.modifier == self.AT_MOST and
        self.expected_calls[self.AT_MOST] is None):
      raise FlexmockError('cannot use at_least with at_most unset')
    self.modifier = self.AT_LEAST
    return self

  @property
  def at_most(self):
    """Modifies the associated "times" expectation.

    When given, an exception will only be raised if the method is called more
    than times() specified. Does nothing if times() is not given.

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    if (self.expected_calls[self.AT_MOST] is not None or
        self.modifier == self.AT_MOST):
      raise FlexmockError('cannot use at_most modifier twice')
    if (self.modifier == self.AT_LEAST and
        self.expected_calls[self.AT_LEAST] is None):
      raise FlexmockError('cannot use at_most with at_least unset')
    self.modifier = self.AT_MOST
    return self

  @property
  def ordered(self):
    """Makes the expectation respect the order of should_receive statements.

    An exception will be raised if methods are called out of order, determined
    by order of should_receive calls in the test.

    This is a property method so must be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    self._ordered = True
    return self

  def when(self, func):
    """Sets an outside resource to be checked before executing the method.

    Args:
      - func: function to call to check if the method should be executed

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    self.runnable = func
    return self

  def and_raise(self, exception, *kargs, **kwargs):
    """Specifies the exception to be raised when this expectation is met.

    Args:
      - exception: class or instance of the exception
      - kargs: optional keyword arguments to pass to the exception
      - kwargs: optional named arguments to pass to the exception

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    args = {'kargs': kargs, 'kwargs': kwargs}
    self.return_values.append(ReturnValue(raises=exception, value=args))
    return self

  def replace_with(self, function):
    """Gives a function to run instead of the mocked out one.

    Args:
      - function: callable

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    if self._replace_with:
      raise FlexmockError('replace_with cannot be specified twice')
    if function == self.original_method:
      self._pass_thru = True
    self._replace_with = function
    return self

  def and_yield(self, *kargs):
    """Specifies the list of items to be yielded on successive method calls.

    In effect, the mocked object becomes a generator.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    for value in kargs:
      self.yield_values.append(ReturnValue(value))
    return self

  def verify(self):
    """Verify that this expectation has been met.

    Raises:
      MethodNotCalled Exception
    """
    failed = False
    message = ''
    if self.expected_calls[self.EXACTLY] is not None:
      message = 'exactly %s' % self.expected_calls[self.EXACTLY]
      if self.times_called != self.expected_calls[self.EXACTLY]:
        failed = True
    else:
      if self.expected_calls[self.AT_LEAST] is not None:
        message = 'at least %s' % self.expected_calls[self.AT_LEAST]
        if self.times_called < self.expected_calls[self.AT_LEAST]:
          failed = True
      if self.expected_calls[self.AT_MOST] is not None:
        if message:
          message += ' and '
        message += 'at most %s' % self.expected_calls[self.AT_MOST]
        if self.times_called > self.expected_calls[self.AT_MOST]:
          failed = True
    if not failed:
      return
    else:
      raise MethodNotCalled(
          '%s expected to be called %s times, called %s times' %
          (_format_args(self.method, self.args), message, self.times_called))

  def reset(self):
    """Returns the methods overriden by this expectation to their originals."""
    if not isinstance(self._mock, Mock):
      if self.original_method:
        if (hasattr(self._mock, '__dict__') and
            self.method in self._mock.__dict__ and
            type(self._mock.__dict__) is dict):
          del self._mock.__dict__[self.method]
          if not hasattr(self._mock, self.method):
            self._mock.__dict__[self.method] = self.original_method
        else:
          setattr(self._mock, self.method, self.original_method)
    del self


class Mock(object):
  """Fake object class returned by the flexmock() function."""

  UPDATED_ATTRS = ['should_receive', 'should_call', 'new_instances']

  def __init__(self, **kwargs):
    """Mock constructor.

    Args:
      - kwargs: dict of attribute/value pairs used to initialize the mock object
    """
    self.__calls__ = []
    self.__object__ = self
    for attr, value in kwargs.items():
      if hasattr(value, '__call__') and not isinstance(value, Mock):
        setattr(self, attr, self._recordable(value))
      else:
        setattr(self, attr, value)

  def __enter__(self):
    return self.__object__

  def __exit__(self, type, value, traceback):
    return self

  def __call__(self, *kargs, **kwargs):
    if self.__calls__:
      call = self.__calls__[-1]
      call['kargs'] = kargs
      call['kwargs'] = kwargs
      call['returned'] = self
    return self

  def __getattribute__(self, name):
    if name not in ORIGINAL_MOCK_ATTRS:
      attr = object.__getattribute__(self, name)
      calls = object.__getattribute__(self, '__calls__')
      calls.append({'name': name, 'returned': attr})
      return attr
    else:
      return object.__getattribute__(self, name)

  def __getattr__(self, name):
    self.__calls__.append({'name': name, 'returned': self})
    return self

  def _recordable(self, func):
    def inner(*kargs, **kwargs):
      if not self.__calls__:
        return func(*kargs, **kwargs)
      else:
        call = self.__calls__[-1]
        call['kargs'] = kargs
        call['kwargs'] = kwargs
        try:
          ret = func(*kargs, **kwargs)
          call['returned'] = ret
          return ret
        except:
          call['raised'] = sys.exc_info()
          del call['returned']
          raise
    return inner

  def should_receive(self, method):
    """Adds a method Expectation to the provided class or instance.

    Args:
      - method: string name of the method to add

    Returns:
      - Expectation object
    """
    calls = self.__calls__
    obj = self.__object__
    saved_length = len(calls)
    if method in Mock.UPDATED_ATTRS:
      raise FlexmockError('unable to replace flexmock methods')
    chained_methods = None
    return_value = None
    if '.' in method:
      method, chained_methods = method.split('.', 1)
    if (method.startswith('__') and not method.endswith('__') and
        not inspect.ismodule(obj)):
      if inspect.isclass(obj):
        name = obj.__name__
      else:
        name = obj.__class__.__name__
      method = '_%s__%s' % (name, method.lstrip('_'))
    if not isinstance(obj, Mock) and not hasattr(obj, method):
      raise MethodDoesNotExist('%s does not have method %s' % (obj, method))
    if chained_methods:
      return_value = Mock()
      chained_expectation = return_value.should_receive(chained_methods)
    if self not in FlexmockContainer.flexmock_objects:
      FlexmockContainer.flexmock_objects[self] = []
    expectation = self._retrieve_or_create_expectation(method, return_value)
    if expectation not in FlexmockContainer.flexmock_objects[self]:
      FlexmockContainer.flexmock_objects[self].append(expectation)
      self._update_method(expectation, method)
    calls = calls[:saved_length]
    if chained_methods:
      return chained_expectation
    else:
      return expectation

  def should_call(self, method):
    """Creates a spy.

    This means that the original method will be called rather than the fake
    version. However, we can still keep track of how many times it's called and
    with what arguments, and apply expectations accordingly.

    should_call is meaningless/not allowed for partial class mocks.

    Returns:
      - Expectation object
    """
    obj = self.__object__
    if inspect.isclass(obj) and not isinstance(obj, Mock):
      raise FlexmockError('should_call cannot be called on a class mock')
    expectation = self.should_receive(method)
    return expectation.replace_with(expectation.original_method)

  def new_instances(self, *kargs):
    """Overrides __new__ method on the class to return custom objects.

    Alias for should_receive('__new__').and_return(kargs).one_by_one

    Args:
      - kargs: objects to return on each successive call to __new__

    Returns:
      - Expectation object
    """
    if inspect.isclass(self.__object__):
      return self.should_receive('__new__').and_return(kargs).one_by_one
    else:
      raise FlexmockError('new_instances can only be called on a class mock')

  def _retrieve_or_create_expectation(self, method, return_value=None):
    if method in [x.method for x in FlexmockContainer.flexmock_objects[self]]:
      expectation = [x for x in FlexmockContainer.flexmock_objects[self]
                     if x.method == method][0]
      expectation = Expectation(
          self.__object__, name=method, return_value=return_value,
          original_method=expectation.original_method)
    else:
      expectation = Expectation(
          self.__object__, name=method, return_value=return_value)
    return expectation

  def _update_method(self, expectation, method):
    method_instance = self.__create_mock_method(method)
    obj = self.__object__
    if hasattr(obj, method) and not expectation.original_method:
      if hasattr(obj, '__dict__') and method in obj.__dict__:
        expectation.original_method = obj.__dict__[method]
      else:
        expectation.original_method = getattr(obj, method)
    if hasattr(obj, '__dict__') and type(obj.__dict__) is dict:
      obj.__dict__[method] = types.MethodType(method_instance, obj)
    else:
      setattr(obj, method, types.MethodType(method_instance, obj))

  def __create_mock_method(self, method):
    def generator_method(yield_values):
      for value in yield_values:
        yield value.value

    def _handle_exception_matching(expectation):
      if expectation.return_values:
        raised, instance = sys.exc_info()[:2]
        message = '%s' % instance
        expected = expectation.return_values[0].raises
        if not expected:
          raise
        args = expectation.return_values[0].value
        expected_instance = expected(*args['kargs'], **args['kwargs'])
        expected_message = '%s' % expected_instance
        if inspect.isclass(expected):
          if expected is not raised and expected not in raised.__bases__:
            raise (InvalidExceptionClass('expected %s, raised %s' %
                   (expected, raised)))
          if args['kargs'] and '_sre.SRE_Pattern' in str(args['kargs'][0]):
            if not args['kargs'][0].search(message):
              raise (InvalidExceptionMessage('expected /%s/, raised "%s"' %
                     (args['kargs'][0].pattern, message)))
          elif expected_message and expected_message != message:
            raise (InvalidExceptionMessage('expected "%s", raised "%s"' %
                   (expected_message, message)))
        elif expected is not raised:
          raise (InvalidExceptionClass('expected "%s", raised "%s"' %
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
        if not _arguments_match(val, expected[i]):
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
      return return_values

    def mock_method(runtime_self, *kargs, **kwargs):
      arguments = {'kargs': kargs, 'kwargs': kwargs}
      expectation = FlexmockContainer.get_flexmock_expectation(
          self, method, arguments)
      if expectation:
        if not expectation.runnable():
          raise InvalidState('%s expected to be called when %s is True' %
                             (method, expectation.runnable))
        expectation.times_called += 1
        if expectation._pass_thru:
          return pass_thru(expectation, *kargs, **kwargs)
        elif expectation._replace_with:
          return expectation._replace_with(*kargs, **kwargs)
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
        raise InvalidMethodSignature(_format_args(method, arguments))

    def mock_method_recordable_wrapper(runtime_self, *kargs, **kwargs):
      mock_list = [o for o in FlexmockContainer.flexmock_objects
                   if o.__object__ == runtime_self]
      if mock_list:
        mock_object = mock_list[0]
        if not mock_object.__calls__:
          return mock_method(runtime_self, *kargs, **kwargs)
        else:
          call = mock_object.__calls__[-1]
          try:
            ret = mock_method(runtime_self, *kargs, **kwargs)
            call['kargs'] = kargs
            call['kwargs'] = kwargs
            call['returned'] = ret
            return ret
          except:
            mock_object.__calls__[-1]['raised'] = sys.exc_info()
            del mock_object.__calls__[-1]['returned']
            raise

    return mock_method_recordable_wrapper


ORIGINAL_MOCK_ATTRS = dir(Mock) + ['__calls__', '__object__']


def __should_call_connected(self, method):
  if inspect.isclass(self.__object__):
    return Expectation(self)

  expectation = self.should_receive(method)
  return expectation.replace_with(expectation.original_method)


def __should_receive_connected(self, method):
  return __should_call_connected(self, method)


if os.environ.get('FLEXMOCK_MODE', '').lower() == 'connected':
  Mock.should_call = __should_call_connected
  Mock.should_receive = __should_receive_connected


def _arg_to_str(arg):
  if '_sre.SRE_Pattern' in str(type(arg)):
    return '/%s/' % arg.pattern
  if sys.version_info < (3, 0):
    # prior to 3.0 unicode strings are type unicode that inherits
    # from basestring along with str, in 3.0 both unicode and basestring
    # go away and str handles everything properly
    if isinstance(arg, basestring):
      return '"%s"' % arg
    else:
      return '%s' % arg
  else:
    if isinstance(arg, str):
      return '"%s"' % arg
    else:
      return '%s' % arg


def _format_args(method, arguments):
  if arguments is None:
    arguments = {'kargs': (), 'kwargs': {}}
  kargs = ', '.join(_arg_to_str(arg) for arg in arguments['kargs'])
  kwargs = ', '.join('%s=%s' % (k, _arg_to_str(v)) for k, v in
                                arguments['kwargs'].items())
  if kargs and kwargs:
    args = '%s, %s' % (kargs, kwargs)
  else:
    args = '%s%s' % (kargs, kwargs)
  return '%s(%s)' % (method, args)


def _create_partial_mock(obj_or_class, **kwargs):
  matches = [x for x in FlexmockContainer.flexmock_objects
             if x.__object__ is obj_or_class]
  if matches:
    mock = matches[0]
  else:
    mock = Mock()
    mock.__object__ = obj_or_class
  for method, return_value in kwargs.items():
    mock.should_receive(method).and_return(return_value)
  if not matches:
    FlexmockContainer.add_expectation(mock, Expectation(obj_or_class))
  if (_attach_flexmock_methods(mock, Mock, obj_or_class) and
    not inspect.isclass(mock.__object__)):
    mock = mock.__object__
  return mock


def _attach_flexmock_methods(mock, flexmock_class, obj):
  try:
    for attr in Mock.UPDATED_ATTRS:
      if hasattr(obj, attr):
        if (_get_code(getattr(obj, attr)) is not
            _get_code(getattr(flexmock_class, attr))):
          return False
    for attr in Mock.UPDATED_ATTRS:
      if hasattr(obj, '__dict__') and type(obj.__dict__) is dict:
        obj.__dict__[attr] = getattr(mock, attr)
      else:
        setattr(obj, attr, getattr(mock, attr))
  except TypeError:
    raise AttemptingToMockBuiltin(
        'Python does not allow you to mock builtin objects or modules. '
        'Consider wrapping it in a class you can mock instead')
  except AttributeError:
    raise AttemptingToMockBuiltin(
        'Python does not allow you to mock instances of builtin objects. '
        'Consider wrapping it in a class you can mock instead')
  return True


def _get_code(func):
  if hasattr(func, 'func_code'):
    code = 'func_code'
  elif hasattr(func, 'im_func'):
    func = func.im_func
    code = 'func_code'
  else:
    code = '__code__'
  return getattr(func, code)


def _match_args(given_args, expected_args):
  if (given_args == expected_args or expected_args is None):
    return True
  if (len(given_args['kargs']) != len(expected_args['kargs']) or
      len(given_args['kwargs']) != len(expected_args['kwargs']) or
      given_args['kwargs'].keys() != expected_args['kwargs'].keys()):
    return False
  for i, arg in enumerate(given_args['kargs']):
    if not _arguments_match(arg, expected_args['kargs'][i]):
      return False
  for k, v in given_args['kwargs'].items():
    if not _arguments_match(v, expected_args['kwargs'][k]):
      return False
  return True


def _arguments_match(arg, expected_arg):
  if arg == expected_arg:
    return True
  elif inspect.isclass(expected_arg) and isinstance(arg, expected_arg):
    return True
  elif ('_sre.SRE_Pattern' in str(type(expected_arg)) and
        expected_arg.search(arg)):
    return True
  else:
    return False


def flexmock_teardown():
  """Performs lexmock-specific teardown tasks."""

  saved = {}
  for mock_object, expectations in FlexmockContainer.flexmock_objects.items():
    saved[mock_object] = expectations[:]
    for expectation in expectations:
      expectation.reset()
  instances = [x.__object__ for x in saved.keys()
               if not isinstance(x.__object__, Mock) and
               not inspect.isclass(x.__object__)]
  classes = [x.__object__ for x in saved.keys()
             if inspect.isclass(x.__object__)]
  for obj in set(instances + classes):
    for attr in Mock.UPDATED_ATTRS:
      if (hasattr(obj, '__dict__') and
          type(obj.__dict__) is dict and attr in obj.__dict__):
        if (_get_code(getattr(obj, attr)) is _get_code(getattr(Mock, attr))):
          del obj.__dict__[attr]
      elif hasattr(obj, attr):
        try:
          if (_get_code(getattr(obj, attr)) is _get_code(getattr(Mock, attr))):
            delattr(obj, attr)
        except AttributeError:
          pass
  for mock_object, expectations in saved.items():
    del FlexmockContainer.flexmock_objects[mock_object]

  for mock_object, expectations in saved.items():
    for expectation in expectations:
      expectation.verify()


def flexmock(spec=None, **kwargs):
  """Main entry point into the flexmock API.

  This function is used to either generate a new fake object or take
  an existing object (or class or module) and use it as a basis for
  a partial mock. In case of a partial mock, the passed in object
  is modified to support basic Mock class functionality making
  it unnecessary to make successive flexmock() calls on the same
  objects to generate new expectations.

  Examples:
    >>> flexmock(SomeClass)
    >>> SomeClass.should_receive('some_method')

  NOTE: it's safe to call flexmock() on the same object, it will detect
  when an object has already been partially mocked and return it each time.

  Args:
    - spec: object (or class or module) to mock
    - kwargs: method/return_value pairs to attach to the object

  Returns:
    Mock object if no spec is provided. Otherwise return the spec object.
  """
  if spec:
    return _create_partial_mock(spec, **kwargs)
  else:
    return Mock(**kwargs)


# RUNNER INTEGRATION


def _hook_into_pytest():
  try:
    from _pytest import runner
    saved = runner.call_runtest_hook
    def call_runtest_hook(item, when):
      ret = saved(item, when)
      teardown = runner.CallInfo(flexmock_teardown, when=when)
      if when == 'call' and not ret.excinfo:
        teardown.result = None
        return teardown
      else:
        return ret
    runner.call_runtest_hook = call_runtest_hook

  except ImportError:
    pass
_hook_into_pytest()


def _hook_into_doctest():
  try:
    from doctest import DocTestRunner
    saved = DocTestRunner.run
    def run(self, test, compileflags=None, out=None, clear_globs=True):
      try:
        return saved(self, test, compileflags, out, clear_globs)
      finally:
        flexmock_teardown()
    DocTestRunner.run = run
  except ImportError:
    pass
_hook_into_doctest()


def _update_unittest(klass):
  saved_stopTest = klass.stopTest
  saved_addSuccess = klass.addSuccess
  def stopTest(self, test):
    try:
      flexmock_teardown()
      saved_addSuccess(self, test)
    except:
      if hasattr(self, '_pre_flexmock_success'):
        self.addError(test, sys.exc_info())
    return saved_stopTest(self, test)
  klass.stopTest = stopTest

  def addSuccess(self, test):
    self._pre_flexmock_success = True
  klass.addSuccess = addSuccess


def _hook_into_unittest():
  try:
    import unittest
    try:
      from unittest import TextTestResult as TestResult
    except ImportError:
      from unittest import _TextTestResult as TestResult
    _update_unittest(TestResult)
  except ImportError:
    pass
_hook_into_unittest()
