Usage Documentation
===================

Definitions
-----------

In order to discuss Flexmock usage it's important to define the
following terms.

:Stub: fake object that returns a canned value

:Mock: fake object that returns a canned value and has an expectation, i.e. it includes a built-in assertion

:Spy:  watches method calls and records/verifies if the method is called with required parameters and/or returns expected values/exceptions

-----------

Compatibility
=============

Test runner integration
-----------------------

unittest
~~~~~~~~

Fully supported.

Nose
~~~~

Fully supported, with one caveat that "generator" tests do not interact well with Flexmock's expectation checking code.
Current recommendation is to only use Flexmock's stubbing and fake object facilities in generator tests.

Py.test
~~~~~~~

Fully supported, with same caveat about "generator" tests as nose.

Doctest
~~~~~~~

Not yet extensively tested but provisionally supported, including automatic expectation checking.

Other test runners
~~~~~~~~~~~~~~~~~~

As far as I can tell most test runners out there are based on unittest to some degree
so chances are they will simply just work without any special effort on Flexmock's side, as is the case with Nose.


Example Usage
=============


Import Flexmock
---------------

::

  from flexmock import flexmock

Make a fake object
------------------

::

  fake = flexmock()

Specify attribute/return value pairs

::

  fake_plane = flexmock(
      model="MIG-16",
      condition="used")

Specify methods/return value pairs

::

  fake_plane = flexmock(
      fly=lambda: "voooosh!",
      land=lambda: "landed!")
 
You can mix method and non-method attributes by making the return value a lambda for callable attributes.

Flexmock fake objects support the full range of flexmock commands but
differ from partial mocks (described below) in that should_receive()
can assign them new methods rather than being limited to acting on methods
they already possess.

::

  fake_plane = flexmock(fly=lambda: "vooosh!")
  fake_plane.should_receive("land").and_return("landed!")
 

Partially mock or stub an existing object
-----------------------------------------

Flexmock provides three syntactic ways to hook into an existing object and overwrite its methods.

Mark the object as partially mocked, allowing it to be used to create new expectations

::

    flexmock(Plane)
    Plane.should_receive('fly').and_return('vooosh!').once
    Plane.should_receive('land').and_return('landed!').once

Equivalent syntax assigns the partially mocked object to a variable

::

    plane = flexmock(Plane)
    plane.should_receive('fly').and_return('vooosh!').once
    plane.should_receive('land').and_return('landed!').once

Or you can combine everything into one line if there is only one method to overwrite

::

    flexmock(Plane).should_receive('fly').and_return('vooosh!').once

You can also return the mock object after setting the expectations

::

    plane = flexmock(Plane).should_receive('fly').and_return('vooosh!').mock

Note the "mock" modifier above -- the expectation chain returns an expectation otherwise

::

    plane.should_receive('land').with_args().and_return('foo', 'bar')


:NOTE: If you do not specify the arguments then any set of arguments, including none, will be matched.

:NOTE: If you do not provide a return value then None is returned by default.


Stub out a method for all instances of a class
----------------------------------------------

::

    >>> class User: pass
    >>> flexmock(User)
    >>> User.should_receive('get_name').and_return('Bill Clinton')
    >>> bubba = User()
    >>> bubba.get_name()
    'Bill Clinton'

Create automatically checked expectations
-----------------------------------------

Using the times(N) modifier, or its aliases -- once, twice, never --
allows you to create expectations that will be automatically checked by
the test runner.

::

    plane = flexmock(Plane)

Ensure fly('forward') gets called exactly three times

::

    plane.should_receive('fly').with_args('forward').times(3)

Ensure turn('east') gets called at least twice

::

    plane.should_receive('turn').with_args('east').at_least.twice

Ensure land('airfield') gets called at most once

::

    plane.should_receive('land').with_args('airfield').at_most.once

Ensure that crash('boom!') is never called

::

    plane.should_receive('crash').with_args('boom!').never

Raise exceptions
----------------

::

    flexmock(Plane).should_receive('fly').and_raise(BadWeatherException)

Or you can add a message to the exception being raised

::

    flexmock(Plane).should_receive('fly').and_raise(BadWeatherException, 'Oh noes, rain!')


Add a spy (or proxy) to a method
--------------------------------

In addition to stubbing out a given method and return fake values,
Flexmock also allows you to call the original method and make
expectations based on its return values/exceptions and the number of
times the method is called with the given arguments.

Matching specific arguments

::

    flexmock(Plane).should_call('repair').with_args(wing, cockpit).once

Matching any arguments

::

    flexmock(Plane).should_call('turn').twice

Matching specific return values

::

    flexmock(Plane).should_call('land').and_return('landed!')

Matching a regular expression

::

    flexmock(Plane).should_call('land').and_return(re.compile('^la'))

Match return values by class/type

::

    flexmock(Plane).should_call('fly').and_return(str, object, None)

Ensure that an appropriate exception is raised

::

    flexmock(Plane).should_call('fly').and_raise(BadWeatherException)

Check that the exception message matches your expectations

::

    flexmock(Plane).should_call('fly').and_raise(BadWeatherException, 'Oh noes, rain!')

Check that the exception message matches a regular expression

::

    flexmock(Plane).should_call('fly').and_raise(BadWeatherException, re.compile('rain'))

If either and_return() or and_raise() is provided, flexmock will
verify that the return value matches the expected return value or
exception.

:NOTE: should_call() changes the behavior of and_return() and and_raise() to specify expectations rather than generate given values or exceptions.

Return different values on successive method invocations
--------------------------------------------------------

::

    >>> flexmock(group).should_receive('get_member').and_return('user1').and_return('user2').and_return('user3')
    >>> group.get_member()
    'user1'
    >>> group.get_member()
    'user2'
    >>> group.get_member()
    'user3'

Or use the short-hand form

::

    flexmock(group).should_receive('get_member').and_return('user1', 'user2', 'user3').one_by_one

You can also mix return values with exception raises

::

    flexmock(group).should_receive('get_member').and_return('user1').and_raise(Exception).and_return('user2')

Override "__new__" method on a class and return fake instances
------------------------------------------------------------------

Occasionally you will want a class to create fake objects when it's
being instantiated. Flexmock makes it easy and painless.

::

    >>> class Group(object): pass
    >>> fake_group = flexmock(name='fake')
    >>> flexmock(Group).new_instances(fake_group)
    >>> Group().name == 'fake'
    True

It is also possible to return different fake objects in a sequence.

::

    >>> class Group(object): pass
    >>> fake_group1 = flexmock(name='fake')
    >>> fake_group2 = flexmock(name='real')
    >>> flexmock(Group).new_instances(fake_group1, fake_group2)
    >>> Group().name == 'fake'
    True
    >>> Group().name == 'real'
    True

Overriding new instances of old-style classes is currently not supported
directly, you should make the class inherit from "object" in your code
first. Luckily, multiple inheritance should make this pretty painless.

Create a mock generator
-----------------------

::

    >>> flexmock(Plane).should_receive('flight_log').and_yield('take off', 'flight', 'landing')
    >>> for i in Plane.flight_log():
    >>>   print i
    'take off'
    'flight' 
    'landing'

Private methods
---------------

One of the small pains of writing unit tests is that it can be
difficult to get at the private methods since Python "conveniently"
renames them when you try to access them from outside the object. With
Flexmock there is nothing special you need to do to -- mocking private
methods is exactly the same as any other methods.

Enforcing call order
--------------------

::

    >>> flexmock(Plane).should_receive('fly').with_args('forward').and_return('ok').ordered
    >>> flexmock(Plane).should_receive('fly').with_args('up').and_return('ok').ordered

Now calling the methods in the same order will be fine

::

    >>> Plane.fly('forward')
    'ok'
    >>> Plane.fly('up')
    'ok'

But trying to call the second one first will result in an exception!

State Support
-------------

Flexmock supports conditional method execution based on external state. Consider a Radio class with the following methods:

::

  >>> class Radio:
  ...   is_on = False
  ...   def switch_on(self): self.is_on = True
  ...   def switch_off(self): self.is_on = False
  ...   def select_channel(self): return None
  ...   def adjust_volume(self, num): self.volume = num 
  >>> radio = Radio()

Now we can define some method call expectations dependent on the state of the radio:

::

  >>> flexmock(radio)
  >>> radio.should_receive('select_channel').once.when(lambda: radio.is_on)
  >>> radio.should_call('adjust_volume').once.with_args(5).when(lambda: radio.is_on)


Calling these while the radio is off will result in an error:

::

  >>> radio.select_channel()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "flexmock.py", line 674, in mock_method
      (method, expectation._get_runnable()))
  flexmock.StateError: select_channel expected to be called when condition is True
  >>> radio.adjust_volume(5)
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "flexmock.py", line 674, in mock_method
      (method, expectation._get_runnable()))
  flexmock.StateError: adjust_volume expected to be called when condition is True
  Traceback (most recent call last):

Turning the radio on will make things work as expected:

::

  >>> radio.is_on = True
  >>> radio.select_channel()
  >>> radio.adjust_volume(5)



Chained methods
---------------

Let's say you have some code that looks something like the following:

::

    http = HTTP()
    results = http.get_url('http://www.google.com').parse_html().retrieve_results()

You could use Flexmock to mock each of these method calls individually:

::

    mock = flexmock(get_url=lambda: flexmock(parse_html=lambda: flexmock(retrieve_results=[])))
    flexmock(HTTP).new_instances(mock)

But that looks really error prone and quite difficult to parse when
reading. Here's a better way:

::

    mock = flexmock()
    flexmock(HTTP).new_instances(mock)
    mock.should_receive('get_url.parse_html.retrieve_results').and_return([])

When using this short-hand, Flexmock will create intermediate objects
and expectations, returning the final one in the chain. As a result, any
further modifications, such as with_args() or times() modifiers, will
only be applied to the final method in the chain. If you need finer
grained control, such as specifying specific arguments to an
intermediate method, you can always fall back to the above long version.

Replacing methods with custom functions
---------------------------------------

There are times when it is useful to replace a method with a custom lambda or function in order to return custom values based on provided arguments or a global value that changes between method calls.

::

   flexmock(Plane).should_receive('set_speed').replace_with(lambda x: x == 5)

Mocking builtin functions
-------------------------

Mocking or stubbing out builtin functions, such as open(), can be slightly tricky.
The "builtins" module is accessed differenty in interactive Python sessions versus
running applications and named differently in Python 3.0 and above.
It is also not always obvious when the builtin function you are trying to mock might be
internally called by the test runner and cause unexpected behavior in the test.
As a result, the recommended way to mock out builtin functions is to always specify
a fall-through with should_call() first and use with_args() to limit the scope of
your mock or stub to just the specific invocation you are trying to replace:

::

   # python 2.4+
   mock = flexmock(sys.modules['__builtin__'])
   mock.should_call('open')  # set the fall-through
   mock.should_receive('open').with_args('/your/file').and_return(
       flexmock(read=lambda: 'file contents'))

   # python 3.0+
   mock = flexmock(sys.modules['builtins'])
   mock.should_call('open')  # set the fall-through
   mock.should_receive('open').with_args('/your/file').and_return(
       flexmock(read=lambda: 'file contents'))


Expectation Matching
====================

Creating an expectation with no arguments will by default match all
arguments, including no arguments.

::

    >>> flexmock(Plane).should_receive('fly').and_return('ok')

Will be matched by any of the following:

::

    >>> Plane.fly()
    'ok'
    >>> Plane.fly('up')
    'ok'
    >>> Plane.fly('up', 'down')
    'ok'

Match exactly no arguments 

::

    flexmock(Plane).should_receive('fly').with_args()

Match any single argument

::

    flexmock(Plane).should_receive('fly').with_args(object)

:NOTE: In addition to exact values, you can match against the type or class of the argument.

Match any single string argument

::

    flexmock(Plane).should_receive('fly').with_args(str)

Match the empty string using a compiled regular expression

::

    flexmock(Plane).should_receive('fly').with_args(re.compile('^(up|down)$'))

Match any set of three arguments where the first one is an integer,
second one is anything, and third is string 'foo'
(matching against user defined classes is also supported in the same fashion)

::

    flexmock(Plane).should_receive('repair').with_args(int, object, 'notes')

You can also override the default match with another expectation for the
same method.

::

    >>> flexmock(Plane).should_receive('fly').and_return('ok')
    >>> flexmock(Plane).should_receive('fly').with_args('up').and_return('bad')
    >>> Plane.fly()
    'ok'
    >>> Plane.fly('forward', 'down')
    'ok'

But!

::

    >>> Plane.fly('up')
    'bad'

The order of the expectations being defined is significant, with later
expectations having higher precedence than previous ones. Which means
that if you reversed the order of the example expectations above the
more specific expectation would never be matched.


Style
=====

While the order of modifiers is unimportant to Flexmock, there is a preferred convention
that will make your tests more readable.

If using with_arg(), place it before should_return():

::

    >>> flexmock(Plane).should_receive('fly').with_args('up', 'down').and_return('ok')

If using the times() modifier (or its aliases: once, twice, never), place them at
the end of the flexmock statement:

::

    >>> flexmock(Plane).should_receive('fly').and_return('ok').once

It is acceptable to have the times() modifier show up in the middle of the modifier chain if
the chain splits multiple lines and you want to ensure it shows up on the first line:

::

    >>> flexmock(Plane).should_receive('fly').times(2).and_return(
    >>>     'some really long status message',
    >>>     'some other really long status message').one_by_one
