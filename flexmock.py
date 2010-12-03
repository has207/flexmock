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
import types
import unittest


class FlexmockException(Exception):
  pass


class InvalidMethodSignature(FlexmockException):
  pass


class MethodNotCalled(FlexmockException):
  pass


class MethodCalledOutOfOrder(FlexmockException):
  pass


class AlreadyMocked(FlexmockException):
  pass


class ReturnValue(object):
  def __init__(self, value=None, raises=None):
    self.value = value
    self.raises = raises


class Expectation(object):
  """Holds expectations about methods.

  The information contained in the Expectation object includes method name,
  its argument list, return values, and any exceptions that the method might
  raise.
  """

  AT_LEAST = 'at least '
  AT_MOST = 'at most '

  def __init__(self, name, mock, args=None, return_value=None, kwargs=None):
    self.method = name
    self.modifier = ''
    self.original_method = None
    self.args = {}
    if not isinstance(args, tuple):
      self.args['kargs'] = (args,)
    else:
      self.args['kargs'] = args
    if kwargs is None:
      kwargs = {}
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
    return '%s%s -> %s' % (self.method, self.args, self.return_values)

  @property
  def mock(self):
    """Return the mock associated with this expectation.

    Since this method is a property it must be called without parentheses.
    """
    return self._mock

  def with_args(self, *kargs, **kwargs):
    """Override the arguments used to match this expectation's method."""
    self.args = {}
    self.args['kargs'] = kargs
    self.args['kwargs'] = kwargs
    return self

  def and_return(self, *value):
    """Override the return value of this expectation's method.

    When and_return is given multiple times, each value provided is returned
    on successive invokations of the method. It is also possible to mix
    and_return with and_raise in the same manner to alternate between returning
    a value and raising and exception on different method invokations.

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

    Each value in the list is returned on successive invokations of the method.
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
    self._pass_thru = True
    return self

  @property
  def ordered(self):
    """Makes the expectation respect the order of should_receive statements."""
    self._ordered = True
    return self

  def and_raise(self, exception):
    """Specifies the exception to be raised when this expectation is met."""
    self.return_values.append(ReturnValue(raises=exception))
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
      setattr(self._mock, self.method, self.original_method)
    elif self.method in dir(self._mock):
      delattr(self._mock, self.method)
    for attr in FlexMock.UPDATED_ATTRS:
      if hasattr(self._mock, attr):
        delattr(self._mock, attr)
    del self


class FlexMock(object):
  """Creates mock objects or puts existing objects or classes under mock.

  To create a new mock object with some attributes:
    FlexMock('some_name', attr1=value1, attr2=value2, ...)

  To put existing object under mock:
    FlexMock(some_object)

  Now you can add some expectations:

    some_object.should_receive('some_method').and_return('some_value')

    --or--

    some_object.should_receive('some_method').and_raise(some_exception)

  To generate some assertions add a times(x) expectation:

    some_object.should_receive('some_method').times(1)

    -- which is equivalent to --

    some_object.should_receive('some_method').once

  You can also do the same thing for all instances of a class by giving the
  FlexMock constructor a class instead of an instance. It's even possible to
  override new instances created by the class constructor.

  Various shortcuts are supported, so:

    FlexMock(some_object, method1='foo', method2='bar')

    -- is the same as --

    FlexMock(some_object)
    some_object.should_receive('method1').and_return('foo')
    some_object.should_receive('method2').and_return('bar')
  """

  UPDATED_ATTRS = ['should_receive', '_get_flexmock_expectation',
                   '_flexmock_expectations']

  def __init__(self, object_or_class=None, force=False, **kwargs):
    """FlexMock constructor.

    Args:
      object_or_class: object or class to mock
      force: Boolean, see _setup_mock() method for explanation
      kwargs: dict of attribute/value pairs used to initialize the mock object
    """
    self._flexmock_expectations = []
    if object_or_class is None:
      self._mock = self
      for attr, value in kwargs.items():
        setattr(self, attr, value)
    else:
      self._setup_mock(object_or_class, force=force, **kwargs)
    self.update_teardown()

  def should_receive(self, method, args=None, return_value=None):
    """Adds a method Expectation to the provided class or instance.

    Args:
      method: string name of the method to add
      args: tuple of multipe args or *single* arg of any type
      return_value: whatever you want the method to return

    Returns:
      expectation: Expectation object
    """
    if method.startswith('__'):
      method = '_%s__%s' % (self._mock.__class__.__name__, method.lstrip('_'))
    expectation = self._retrieve_or_create_expectation(method, args,
                                                       return_value)
    self._flexmock_expectations.append(expectation)
    self._add_expectation_to_object(expectation, method)
    return expectation

  def _new_instances(self, return_value):
    """Overrides creation of new instances of the mocked class.

    Args:
      return_value: the object that should be created instead of the default
    """
    method = '__new__'
    expectation = self._retrieve_or_create_expectation(
        method, None, return_value)
    self._flexmock_expectations.append(expectation)
    if not hasattr(expectation, 'original_method'):
      expectation.original_method = getattr(self._mock, method)
    self._mock.__new__ = self.__create_new_method(return_value)

  def _setup_mock(self, obj, force=False, **kwargs):
    """Puts the provided object or class under mock."""
    self._ensure_not_already_mocked(obj, force)
    obj.should_receive = self.should_receive
    obj._get_flexmock_expectation = self._get_flexmock_expectation
    obj._flexmock_expectations = []
    self._mock = obj
    if 'new_instances' in kwargs and inspect.isclass(obj):
      self._new_instances(kwargs['new_instances'])
    else:
      for method, return_value in kwargs.items():
        obj.should_receive(method, return_value=return_value)
    expectation = self._retrieve_or_create_expectation(None, (), None)
    self._flexmock_expectations.append(expectation)

  def _ensure_not_already_mocked(self, obj, force):
    for attr in self.UPDATED_ATTRS:
      if (hasattr(obj, attr)) and not force:
        raise AlreadyMocked('%s already defines %s' % (obj, attr))

  def update_teardown(self, test_runner=unittest.TestCase,
                      teardown_method='tearDown'):
    """Should be implemented by classes inheriting from FlexMock."""
    if not hasattr(test_runner, '_flexmock_objects'):
      setattr(test_runner,
          '_flexmock_objects', {self: self._flexmock_expectations})
      saved_teardown = getattr(test_runner, teardown_method)
      setattr(test_runner, teardown_method,
          self._flexmock_teardown(saved_teardown))
    else:
      getattr(test_runner,
              '_flexmock_objects')[self] = self._flexmock_expectations

  def _flexmock_teardown(self, saved_teardown):
    def teardown(self):
      saved_teardown(self)
      if hasattr(self, '_flexmock_objects'):
        saved = {}
        for mock_object, expectations in self._flexmock_objects.items():
          saved[mock_object] = expectations[:]
          for expectation in expectations:
            expectation.reset()
        for mock_object, expectations in saved.items():
          del self._flexmock_objects[mock_object]
        for mock_object, expectations in saved.items():
          for expectation in expectations:
            expectation.verify()
    return teardown

  def _retrieve_or_create_expectation(self, method, args, return_value):
    if method in [x.method for x in self._flexmock_expectations]:
      expectation = [x for x in self._flexmock_expectations
                     if x.method == method][0]
      if expectation.args is None:
        if isinstance(args, tuple):
          expectation.args = args
        else:
          expectation.args = (args,)
      else:
        expectation = Expectation(method, self._mock, args, return_value)
    else:
      expectation = Expectation(method, self._mock, args, return_value)
    return expectation

  def _add_expectation_to_object(self, expectation, method):
    method_instance = self.__create_mock_method(method)
    if hasattr(self._mock, method):
      expectation.original_method = getattr(self._mock, method)
    setattr(self._mock, method, types.MethodType(
        method_instance, self._mock))

  def _get_flexmock_expectation(self, name=None, args=None):
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
    if (given_args == expected_args or
        expected_args == {'kargs': (None,), 'kwargs': {}}):
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

    def mock_method(self, *kargs, **kwargs):
      arguments = {}
      arguments['kargs'] = kargs
      arguments['kwargs'] = kwargs
      expectation = self._get_flexmock_expectation(method, arguments)
      if expectation:
        expectation.times_called += 1
        if expectation._pass_thru and expectation.original_method:
          return expectation.original_method(*kargs, **kwargs)
        if expectation.yield_values:
          return generator_method(expectation.yield_values)
        elif expectation.return_values:
          return_value = expectation.return_values[0]
          expectation.return_values = expectation.return_values[1:]
          expectation.return_values.append(return_value)
        else:
          return_value = ReturnValue()
        if return_value.raises:
          raise return_value.raises
        else:
          return return_value.value
      else:
        raise InvalidMethodSignature(FlexMock._format_args(method, arguments))
    return mock_method

  @staticmethod
  def _format_args(method, arguments):
    def to_str(arg):
      if isinstance(arg, str):
        return '"%s"' % arg
      else:
        return str(arg)

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
    def new(cls):
      return return_value
    return new


def flexmock_unittest(*kargs, **kwargs):
  class UnittestFlexMock(FlexMock):
    def update_teardown(self, test_runner=unittest.TestCase,
        teardown_method='tearDown'):
      FlexMock.update_teardown(self, test_runner, teardown_method)
  return UnittestFlexMock(*kargs, **kwargs)


flexmock = flexmock_unittest
