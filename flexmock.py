"""Copyright 2011 Herman Sheremetyev. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import inspect
import os
import re
import sys
import types
import unittest
import warnings


AT_LEAST = 'at least'
AT_MOST = 'at most'
EXACTLY = 'exactly'
UPDATED_ATTRS = ['should_receive', 'should_call', 'new_instances']


class FlexmockError(Exception):
  pass


class MockBuiltinError(Exception):
  pass


class MethodSignatureError(FlexmockError):
  pass


class ExceptionClassError(FlexmockError):
  pass


class ExceptionMessageError(FlexmockError):
  pass


class StateError(FlexmockError):
  pass


class MethodCallError(FlexmockError):
  pass


class CallOrderError(FlexmockError):
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
        raise CallOrderError(
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

  def __init__(self, mock, name=None, return_value=None, original_method=None):
    self.method = name
    self.modifier = EXACTLY
    self.original_method = original_method
    self.args = None
    value = ReturnValue(return_value)
    self.return_values = return_values = []
    self._replace_with = None
    if return_value is not None:
      return_values.append(value)
    self.yield_values = []
    self.times_called = 0
    self.expected_calls = {
        EXACTLY: None,
        AT_LEAST: None,
        AT_MOST: None}
    self.runnable = lambda: True
    self._mock = mock
    self._pass_thru = False
    self._ordered = False
    self._one_by_one = False
    self._verified = False

  def __str__(self):
    return '%s -> (%s)' % (_format_args(self.method, self.args),
                           ', '.join(['%s' % x for x in self.return_values]))

  def __call__(self):
    return self

  def __getattribute__(self, name):
    if name == 'once':
      return _getattr(self, 'times')(1)
    elif name == 'twice':
      return _getattr(self, 'times')(2)
    elif name == 'never':
      return _getattr(self, 'times')(0)
    elif name in ('at_least', 'at_most', 'ordered', 'one_by_one'):
      return _getattr(self, name)()
    elif name == 'mock':
      return _getattr(self, 'mock')()
    else:
      return _getattr(self, name)

  def _get_runnable(self):
    """Ugly hack to get the name of when() condition from the source code."""
    name = 'condition'
    try:
      source = inspect.getsource(self.runnable)
      if 'when(' in source:
        name = source.split('when(')[1].split(')')[0]
      elif 'def ' in source:
        name = source.split('def ')[1].split('(')[0]
    except:  # couldn't get the source, oh well
      pass
    return name

  def mock(self):
    """Return the mock associated with this expectation.

    This method may be called without parentheses.
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
    return_values = _getattr(self, 'return_values')
    if not _getattr(self, '_one_by_one'):
      value = ReturnValue(value)
      return_values.append(value)
    else:
      try:
        return_values.extend([ReturnValue(v) for v in value])
      except TypeError:
        return_values.append(ReturnValue(value))
    return self

  def times(self, number):
    """Number of times this expectation's method is expected to be called.

    There are also 3 aliases for the times() method that can be called without
    parentheses:

      - once -> times(1)
      - twice -> times(2)
      - never -> times(0)

    Args:
      - number: int

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    expected_calls = _getattr(self, 'expected_calls')
    modifier = _getattr(self, 'modifier')
    expected_calls[modifier] = number
    return self

  def one_by_one(self):
    """Modifies the return value to be treated as a list of return values.

    Each value in the list is returned on successive invocations of the method.

    This method may be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    if not self._one_by_one:
      self._one_by_one = True
      return_values = _getattr(self, 'return_values')
      saved_values = return_values[:]
      self.return_values = return_values = []
      for value in saved_values:
        try:
          for val in value.value:
            return_values.append(ReturnValue(val))
        except TypeError:
          return_values.append(value)
    return self

  def at_least(self):
    """Modifies the associated times() expectation.

    When given, an exception will only be raised if the method is called less
    than times() specified. Does nothing if times() is not given.

    This method may be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    expected_calls = _getattr(self, 'expected_calls')
    modifier = _getattr(self, 'modifier')
    if expected_calls[AT_LEAST] is not None or modifier == AT_LEAST:
      raise FlexmockError('cannot use at_least modifier twice')
    if modifier == AT_MOST and expected_calls[AT_MOST] is None:
      raise FlexmockError('cannot use at_least with at_most unset')
    self.modifier = AT_LEAST
    return self

  def at_most(self):
    """Modifies the associated "times" expectation.

    When given, an exception will only be raised if the method is called more
    than times() specified. Does nothing if times() is not given.

    This method may be called without parentheses.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    expected_calls = _getattr(self, 'expected_calls')
    modifier = _getattr(self, 'modifier')
    if expected_calls[AT_MOST] is not None or modifier == AT_MOST:
      raise FlexmockError('cannot use at_most modifier twice')
    if modifier == AT_LEAST and expected_calls[AT_LEAST] is None:
      raise FlexmockError('cannot use at_most with at_least unset')
    self.modifier = AT_MOST
    return self

  def ordered(self):
    """Makes the expectation respect the order of should_receive statements.

    An exception will be raised if methods are called out of order, determined
    by order of should_receive calls in the test.

    This method may be called without parentheses.

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
    if not hasattr(func, '__call__'):
      raise FlexmockError('when() parameter must be callable')
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
    return_values = _getattr(self, 'return_values')
    return_values.append(ReturnValue(raises=exception, value=args))
    return self

  def replace_with(self, function):
    """Gives a function to run instead of the mocked out one.

    Args:
      - function: callable

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    replace_with = _getattr(self, '_replace_with')
    original_method = _getattr(self, 'original_method')
    if replace_with:
      raise FlexmockError('replace_with cannot be specified twice')
    if function == original_method:
      self._pass_thru = True
    self._replace_with = function
    return self

  def and_yield(self, *kargs):
    """Specifies the list of items to be yielded on successive method calls.

    In effect, the mocked object becomes a generator.

    Returns:
      - self, i.e. can be chained with other Expectation methods
    """
    yield_values = _getattr(self, 'yield_values')
    for value in kargs:
      yield_values.append(ReturnValue(value))
    return self

  def verify(self, final=True):
    """Verify that this expectation has been met.

    Args:
      final: boolean, True if no further calls to this method expected
             (skip checking at_least expectations when False)

    Raises:
      MethodCallError Exception
    """
    failed = False
    message = ''
    expected_calls = _getattr(self, 'expected_calls')
    times_called = _getattr(self, 'times_called')
    if expected_calls[EXACTLY] is not None:
      message = 'exactly %s' % expected_calls[EXACTLY]
      if final:
        if times_called != expected_calls[EXACTLY]:
          failed = True
      else:
        if times_called > expected_calls[EXACTLY]:
          failed = True
    else:
      if final and expected_calls[AT_LEAST] is not None:
        message = 'at least %s' % expected_calls[AT_LEAST]
        if times_called < expected_calls[AT_LEAST]:
          failed = True
      if expected_calls[AT_MOST] is not None:
        if message:
          message += ' and '
        message += 'at most %s' % expected_calls[AT_MOST]
        if times_called > expected_calls[AT_MOST]:
          failed = True
    if not failed:
      return
    else:
      if self._verified:
        return
      else:
        self._verified = True
      method = _getattr(self, 'method')
      args = _getattr(self, 'args')
      raise MethodCallError(
          '%s expected to be called %s times, called %s times' %
          (_format_args(method, args), message, times_called))

  def reset(self):
    """Returns the methods overriden by this expectation to their originals."""
    _mock = _getattr(self, '_mock')
    if not isinstance(_mock, Mock):
      original_method = _getattr(self, 'original_method')
      if original_method:
        method = _getattr(self, 'method')
        if (hasattr(_mock, '__dict__') and
            method in _mock.__dict__ and
            type(_mock.__dict__) is dict):
          del _mock.__dict__[method]
          if not hasattr(_mock, method):
            _mock.__dict__[method] = original_method
        else:
          setattr(_mock, method, original_method)
    del self


class Mock(object):
  """Fake object class returned by the flexmock() function."""

  def __init__(self, **kwargs):
    """Mock constructor.

    Args:
      - kwargs: dict of attribute/value pairs used to initialize the mock object
    """
    self._object = self
    for attr, value in kwargs.items():
      setattr(self, attr, value)

  def __enter__(self):
    return self._object

  def __exit__(self, type, value, traceback):
    return self

  def __call__(self, *kargs, **kwargs):
    """Hack to make Expectation.mock() work with parens."""
    return self

  def should_receive(self, method):
    """Adds a method Expectation to the provided class or instance.

    Args:
      - method: string name of the method to add

    Returns:
      - Expectation object
    """
    if method in UPDATED_ATTRS:
      raise FlexmockError('unable to replace flexmock methods')
    chained_methods = None
    return_value = None
    if '.' in method:
      method, chained_methods = method.split('.', 1)
    if (method.startswith('__') and not method.endswith('__') and
        not inspect.ismodule(self._object)):
      if _isclass(self._object):
        name = self._object.__name__
      else:
        name = self._object.__class__.__name__
      method = '_%s__%s' % (name, method.lstrip('_'))
    if not isinstance(self._object, Mock) and not hasattr(self._object, method):
      raise FlexmockError('%s does not have method %s' % (self._object, method))
    if chained_methods:
      return_value = Mock()
      chained_expectation = return_value.should_receive(chained_methods)
    if self not in FlexmockContainer.flexmock_objects:
      FlexmockContainer.flexmock_objects[self] = []
    expectation = self._create_expectation(method, return_value)
    if expectation not in FlexmockContainer.flexmock_objects[self]:
      FlexmockContainer.flexmock_objects[self].append(expectation)
      self._update_method(expectation, method)
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
    if _isclass(self._object):
      method_type = type(self._object.__dict__[method])
      if method_type is not classmethod and method_type is not staticmethod:
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
    if _isclass(self._object):
      return self.should_receive('__new__').and_return(kargs).one_by_one
    else:
      raise FlexmockError('new_instances can only be called on a class mock')

  def _create_expectation(self, method, return_value=None):
    if method in [x.method for x in
                  FlexmockContainer.flexmock_objects[self]]:
      expectation = [x for x in FlexmockContainer.flexmock_objects[self]
                     if x.method == method][0]
      expectation = Expectation(
          self._object, name=method, return_value=return_value,
          original_method=expectation.original_method)
    else:
      expectation = Expectation(
          self._object, name=method, return_value=return_value)
    return expectation

  def _update_method(self, expectation, method):
    method_instance = self._create_mock_method(method)
    obj = self._object
    original_method = _getattr(expectation, 'original_method')
    if hasattr(obj, method) and not original_method:
      if hasattr(obj, '__dict__') and method in obj.__dict__:
        expectation.original_method = obj.__dict__[method]
      else:
        expectation.original_method = getattr(obj, method)
      method_type = type(_getattr(expectation, 'original_method'))
      if method_type is classmethod or method_type is staticmethod:
        expectation.original_function = getattr(obj, method)
    if hasattr(obj, '__dict__') and type(obj.__dict__) is dict:
      obj.__dict__[method] = types.MethodType(method_instance, obj)
    else:
      setattr(obj, method, types.MethodType(method_instance, obj))

  def _create_mock_method(self, method):
    def generator_method(yield_values):
      for value in yield_values:
        yield value.value

    def _handle_exception_matching(expectation):
      return_values = _getattr(expectation, 'return_values')
      if return_values:
        raised, instance = sys.exc_info()[:2]
        message = '%s' % instance
        expected = return_values[0].raises
        if not expected:
          raise
        args = return_values[0].value
        expected_instance = expected(*args['kargs'], **args['kwargs'])
        expected_message = '%s' % expected_instance
        if _isclass(expected):
          if expected is not raised and expected not in raised.__bases__:
            raise (ExceptionClassError('expected %s, raised %s' %
                   (expected, raised)))
          if args['kargs'] and '_sre.SRE_Pattern' in str(args['kargs'][0]):
            if not args['kargs'][0].search(message):
              raise (ExceptionMessageError('expected /%s/, raised "%s"' %
                     (args['kargs'][0].pattern, message)))
          elif expected_message and expected_message != message:
            raise (ExceptionMessageError('expected "%s", raised "%s"' %
                   (expected_message, message)))
        elif expected is not raised:
          raise (ExceptionClassError('expected "%s", raised "%s"' %
                 (expected, raised)))
      else:
        raise

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
        original_method = _getattr(expectation, 'original_method')
        _mock = _getattr(expectation, '_mock')
        if _isclass(_mock):
          if (type(original_method) is classmethod or
              type(original_method) is staticmethod):
            original = _getattr(expectation, 'original_function')
            return_values = original(*kargs, **kwargs)
        else:
          return_values = original_method(*kargs, **kwargs)
      except:
        return _handle_exception_matching(expectation)
      expected_values = _getattr(expectation, 'return_values')
      if (expected_values and
          not match_return_values(expected_values[0].value, return_values)):
        raise (MethodSignatureError('expected to return %s, returned %s' %
               (expected_values[0].value, return_values)))
      return return_values

    def mock_method(runtime_self, *kargs, **kwargs):
      arguments = {'kargs': kargs, 'kwargs': kwargs}
      expectation = FlexmockContainer.get_flexmock_expectation(
          self, method, arguments)
      if expectation:
        if not expectation.runnable():
          raise StateError('%s expected to be called when %s is True' %
                             (method, expectation._get_runnable()))
        expectation.times_called += 1
        expectation.verify(final=False)
        _pass_thru = _getattr(expectation, '_pass_thru')
        _replace_with = _getattr(expectation, '_replace_with')
        if _pass_thru:
          return pass_thru(expectation, *kargs, **kwargs)
        elif _replace_with:
          return _replace_with(*kargs, **kwargs)
        yield_values = _getattr(expectation, 'yield_values')
        return_values = _getattr(expectation, 'return_values')
        if yield_values:
          return generator_method(yield_values)
        elif return_values:
          return_value = return_values[0]
          del return_values[0]
          return_values.append(return_value)
        else:
          return_value = ReturnValue()
        if return_value.raises:
          if _isclass(return_value.raises):
            raise return_value.raises(
                *return_value.value['kargs'], **return_value.value['kwargs'])
          else:
            raise return_value.raises
        else:
          return return_value.value
      else:
        raise MethodSignatureError(_format_args(method, arguments))

    return mock_method


def _arg_to_str(arg):
  arg = '%s' % arg  # ensure unicode conversion
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
             if x._object is obj_or_class]
  if matches:
    mock = matches[0]
  else:
    mock = Mock()
    mock._object = obj_or_class
  for method, return_value in kwargs.items():
    mock.should_receive(method).and_return(return_value)
  if not matches:
    FlexmockContainer.add_expectation(mock, Expectation(obj_or_class))
  if (_attach_flexmock_methods(mock, Mock, obj_or_class) and
    not _isclass(mock._object)):
    mock = mock._object
  return mock


def _attach_flexmock_methods(mock, flexmock_class, obj):
  try:
    for attr in UPDATED_ATTRS:
      if hasattr(obj, attr):
        if (_get_code(getattr(obj, attr)) is not
            _get_code(getattr(flexmock_class, attr))):
          return False
    for attr in UPDATED_ATTRS:
      if hasattr(obj, '__dict__') and type(obj.__dict__) is dict:
        obj.__dict__[attr] = getattr(mock, attr)
      else:
        setattr(obj, attr, getattr(mock, attr))
  except TypeError:
    raise MockBuiltinError(
        'Python does not allow you to mock builtin objects or modules. '
        'Consider wrapping it in a class you can mock instead')
  except AttributeError:
    raise MockBuiltinError(
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
  elif _isclass(expected_arg) and isinstance(arg, expected_arg):
    return True
  elif ('_sre.SRE_Pattern' in str(type(expected_arg)) and
        expected_arg.search(arg)):
    return True
  else:
    return False


def _getattr(obj, name):
  """Convenience wrapper."""
  return object.__getattribute__(obj, name)


def _isclass(obj):
  """Fixes stupid bug in inspect.isclass from < 2.7."""
  if sys.version_info < (2, 7):
    return isinstance(obj, (type, types.ClassType))
  else:
    return inspect.isclass(obj)

def flexmock_teardown():
  """Performs lexmock-specific teardown tasks."""

  saved = {}
  instances = []
  classes = []
  for mock_object, expectations in FlexmockContainer.flexmock_objects.items():
    saved[mock_object] = expectations[:]
    for expectation in expectations:
      _getattr(expectation, 'reset')()
  for mock in saved.keys():
    obj = mock._object
    if not isinstance(obj, Mock) and not _isclass(obj):
      instances += [obj]
    if _isclass(obj):
      classes += [obj]
  for obj in instances + classes:
    for attr in UPDATED_ATTRS:
      try:
        obj_dict = obj.__dict__
        if _get_code(obj_dict[attr]) is _get_code(Mock.__dict__[attr]):
          del obj_dict[attr]
      except:
        try:
          if _get_code(getattr(obj, attr)) is _get_code(Mock.__dict__[attr]):
            delattr(obj, attr)
        except AttributeError:
          pass
  for mock_object in saved:
    del FlexmockContainer.flexmock_objects[mock_object]

  # make sure this is done last to keep exceptions here from breaking
  # any of the previous steps that cleanup all the changes
  for mock_object, expectations in saved.items():
    for expectation in expectations:
      _getattr(expectation, 'verify')()


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
