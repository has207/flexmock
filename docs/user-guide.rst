Usage Documentation
===================

Definitions
-----------

In order to discuss flexmock usage it's important to define the
following terms.

:Stub: fake object that returns a canned value

:Mock: fake object that returns a canned value and has an expectation, i.e. it includes a built-in assertion

:Spy:  watches method calls and records/verifies if the method is called with required parameters and/or returns expected values/exceptions

Overview
--------

flexmock declarations follow a consistent style of the following 3 forms:

::

    flexmock ( OBJECT ).COMMAND( ATTRIBUTE ).MODIFIER[.MODIFIER, ...]

    - or -

    flexmock ( OBJECT [, ATTRIBUTE=VALUE, ...] )

    - or -

    flexmock ( ATTRIBUTE=VALUE [, ATTRIBUTE=VALUE,...] )


    OBJECT:

      Either a module, a class, or an instance of a class

    COMMAND:

      One of should_receive, should_call, or new_instances. These
      create the initial expectation object.

    ATTRIBUTE:

      String name of an attribute

    MODIFIER:

      One of several Expectation modifiers, such as with_args,
      and_return, should_raise, times, etc.

    VALUE:

      Anything

-----------


Example Usage
=============


Setup
-----

::

  from flexmock import flexmock

This will include flexmock in your test and make the necessary runner modifications
so no further setup or cleanup is necessary.


Fake objects
------------

::

  fake = flexmock()  # creates an object with no attributes

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

flexmock fake objects support the full range of flexmock commands but
differ from partial mocks (described below) in that should_receive()
can assign them new methods rather than being limited to acting on methods
they already possess.

::

  fake_plane = flexmock(fly=lambda: "vooosh!")
  fake_plane.should_receive("land").and_return("landed!")
 

Partial mocks
-------------

flexmock provides three syntactic ways to hook into an existing object and override its methods.

Mark the object as partially mocked, allowing it to be used to create new expectations

::

    flexmock(plane)
    plane.should_receive('fly').and_return('vooosh!').once()
    plane.should_receive('land').and_return('landed!').once()

Equivalent syntax assigns the partially mocked object to a variable

::

    plane = flexmock(plane)
    plane.should_receive('fly').and_return('vooosh!').once()
    plane.should_receive('land').and_return('landed!').once()

Or you can combine everything into one line if there is only one method to override

::

    flexmock(plane).should_receive('fly').and_return('vooosh!').once()

You can also return the mock object after setting the expectations

::

    plane = flexmock(plane).should_receive('fly').and_return('vooosh!').mock()

Note the "mock" modifier above -- the expectation chain returns an expectation otherwise

::

    plane.should_receive('land').with_args().and_return('foo', 'bar')


:NOTE: If you do not provide a with_args() modifier then any set of arguments, including none, will be matched.  However, if you specify with_args() the expectation will only match exactly zero arguments.

:NOTE: If you do not provide a return value then None is returned by default. Thus, and_return() is equivalent to and_return(None) is equivalent to simply leaving off and_return.

Attributes and properties
-------------------------

Just as you're able to stub return values for functions and methods, flexmock also
allows to stub out non-callable attributes and even (getter) properties.
Syntax for this is exactly the same as for methods and functions.

Shorthand
---------

Instead of writing out the lengthy should_receive/and_return statements, you can
also use the handy shorthand approach of passing them in as key=value pairs
to the flexmock() function. For example, we can stub out two methods of the plane object
in the same call:

::

    flexmock(plane, fly='voooosh!', land=('foo', 'bar'))

This approach is handy and quick but only limited to stubs, i.e.
it is not possible to further modify these kind of calls with any of
the usual modifiers described below.

Class level mocks
-----------------

If the object your partially mock is a class, flexmock effectively replaces the
method for all instances of that class.

::

    >>> class User: pass
    >>> flexmock(User)
    >>> User.should_receive('get_name').and_return('Bill Clinton')
    >>> bubba = User()
    >>> bubba.get_name()
    'Bill Clinton'

Automatically checked expectations
----------------------------------

Using the times(N) modifier, or its aliases -- once, twice, never --
allows you to create expectations that will be automatically checked by
the test runner.

Ensure fly('forward') gets called exactly three times

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args('forward')
        .times(3))

Ensure turn('east') gets called at least twice

::

    (flexmock(plane)
        .should_receive('turn')
        .with_args('east')
        .at_least().twice())

Ensure land('airfield') gets called at most once

::

    (flexmock(plane)
        .should_receive('land')
        .with_args('airfield')
        .at_most().once())

Ensure that crash('boom!') is never called

::

    (flexmock(plane)
        .should_receive('crash')
        .with_args('boom!')
        .never())

Exceptions
----------

You can make the mocked method raise an exception instead of returning a value.

::

    (flexmock(plane)
        .should_receive('fly')
        .and_raise(BadWeatherException))

Or you can add a message to the exception being raised

::

    (flexmock(plane)
        .should_receive('fly')
        .and_raise(BadWeatherException, 'Oh noes, rain!'))


Spies (proxies)
---------------

In addition to stubbing out a given method and returning fake values,
flexmock also allows you to call the original method and make
expectations based on its return values/exceptions and the number of
times the method is called with the given arguments.

Matching specific arguments

::

    (flexmock(plane)
        .should_call('repair')
        .with_args(wing, cockpit)
        .once())

Matching any arguments

::

    (flexmock(plane)
        .should_call('turn')
        .twice())

Matching specific return values

::

    (flexmock(plane)
        .should_call('land')
        .and_return('landed!'))

Matching a regular expression

::

    (flexmock(plane)
        .should_call('land')
        .and_return(re.compile('^la')))

Match return values by class/type

::

    (flexmock(plane)
        .should_call('fly')
        .and_return(str, object, None))

Ensure that an appropriate exception is raised

::

    (flexmock(plane)
        .should_call('fly')
        .and_raise(BadWeatherException))

Check that the exception message matches your expectations

::

    (flexmock(plane)
        .should_call('fly')
        .and_raise(BadWeatherException, 'Oh noes, rain!'))

Check that the exception message matches a regular expression

::

    (flexmock(plane)
        .should_call('fly')
        .and_raise(BadWeatherException, re.compile('rain')))

If either and_return() or and_raise() is provided, flexmock will
verify that the return value matches the expected return value or
exception.

:NOTE: should_call() changes the behavior of and_return() and and_raise() to specify expectations rather than generate given values or exceptions.

Multiple return values
----------------------

It's possible for the mocked method to return different values on successive calls.

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

    (flexmock(group)
        .should_receive('get_member')
        .and_return('user1', 'user2', 'user3')
        .one_by_one())

You can also mix return values with exception raises

::

    (flexmock(group)
        .should_receive('get_member')
        .and_return('user1')
        .and_raise(Exception)
        .and_return('user2'))

Fake new instances
------------------

Occasionally you will want a class to create fake objects when it's
being instantiated. flexmock makes it easy and painless.

Your first option is to simply replace the class with a function.


::
    (flexmock(some_module)
        .should_receive('NameOfClass')
        .and_return(fake_instance))
    # fake_instance can be created with flexmock as well

The upside of this approach is that it works for both new-style and old-style
classes. The downside is that you may run into subtle issues since the
class has now been replaced by a function.

If you're dealing with new-style classes, flexmock offers another alternative using the .new_instances() command.

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

Another approach, if you're familiar with how instance instatiation is done in Python, is to stub the __new__ method directly.

::

    >>> flexmock(Group).should_receive('__new__').and_return(fake_group)
    >>> # or, if you want to be even slicker
    >>> flexmock(Group, __new__=fake_group)

In fact, the new_instances command is simply shorthand for should_receive('__new__').and_return() under the hood.

Generators
----------

In addition to returning values and raising exceptions, flexmock can also turn 
the mocked method into a generator that yields successive values.

::

    >>> flexmock(plane).should_receive('flight_log').and_yield('take off', 'flight', 'landing')
    >>> for i in plane.flight_log():
    >>>   print i
    'take off'
    'flight' 
    'landing'

You can also use Python's builtin iter() function to generate an iterable return value.

::

  flexmock(plane, flight_log=iter(['take off', 'flight', 'landing']))

In fact, the and_yield() modifier is just shorthand for should_receive().and_return(iter)
under the hood.


Private methods
---------------

One of the small pains of writing unit tests is that it can be
difficult to get at the private methods since Python "conveniently"
renames them when you try to access them from outside the object. With
flexmock there is nothing special you need to do to -- mocking private
methods is exactly the same as any other methods.

Call order
----------

flexmock does not enforce call order by default, but it's easy to do if you need to.

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args('forward')
        .and_return('ok')
        .ordered())
    (flexmock(plane)
        .should_receive('fly')
        .with_args('up')
        .and_return('ok')
        .ordered())

The order of the flexmock calls is the order in which these methods will need to be
called by the code under test.

If method fly() above is called with the right arguments in the declared order things
will be fine and both will return 'ok'.
But trying to call fly('up') before fly('forward') will result in an exception.

State Support
-------------

flexmock supports conditional method execution based on external state.
Consider the rather contrived Radio class with the following methods:

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
  >>> radio.should_receive('select_channel').once().when(lambda: radio.is_on)
  >>> radio.should_call('adjust_volume').once().with_args(5).when(lambda: radio.is_on)


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
    results = (http.get_url('http://www.google.com')
                  .parse_html()
                  .display_results())

You could use flexmock to mock each of these method calls individually:

::

    mock = flexmock(get_url=lambda: flexmock(parse_html=lambda: flexmock(display_results='ok')))
    flexmock(HTTP).new_instances(mock)

But that looks really error prone and quite difficult to parse when
reading. Here's a better way:

::

    mock = flexmock()
    flexmock(HTTP).new_instances(mock)
    mock.should_receive('get_url.parse_html.display_results').and_return('ok')

When using this short-hand, flexmock will create intermediate objects
and expectations, returning the final one in the chain. As a result, any
further modifications, such as with_args() or times() modifiers, will
only be applied to the final method in the chain. If you need finer
grained control, such as specifying specific arguments to an
intermediate method, you can always fall back to the above long version.

Word of caution: because flexmock generates temporary intermediate mock objects
for each step along the chain, trying to mock two method call chains with the
same prefix will not work. That is, doing the following will fail to set up
the stub for display_results() because the one for save_results() overrides it:

::

    flexmock(HTTP).should_receive('get_url.parse_html.display_results').and_return('ok')
    flexmock(HTTP).should_receive('get_url.parse_html.save_results').and_return('ok')

In this situation, you should identify the point where the chain starts to
diverge and return a flexmock() object that handles all the "tail"
methods using the same object:

::

    (flexmock(HTTP)
        .should_receive('get_url.parse_html')
        .and_return(flexmock, display_results='ok', save_results='ok'))


Replacing methods
-----------------

There are times when it is useful to replace a method with a custom lambda or
function, rather than simply stubbing it out, in order to return custom values
based on provided arguments or a global value that changes between method calls.

::

    (flexmock(plane)
        .should_receive('set_speed')
        .replace_with(lambda x: x == 5))

There is also shorthand for this, similar to the shorthand for should_receive/and_return:

::

    flexmock(plane, set_speed=lambda x: x == 5)

:NOTE: Whenever the return value provided to the key=value shorthand is a callable (such as lambda), flexmock expands it to should_receive().replace_with() rather than should_receive().and_return().

.. _builtin_functions:

Builtin functions
-----------------

Mocking or stubbing out builtin functions, such as open(), can be slightly tricky.
The "builtins" module is accessed differently in interactive Python sessions versus
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
   (mock.should_receive('open')
       .with_args('/your/file')
       .and_return( flexmock(read=lambda: 'file contents') ))

   # python 3.0+
   mock = flexmock(sys.modules['builtins'])
   mock.should_call('open')  # set the fall-through
   (mock.should_receive('open')
       .with_args('/your/file')
       .and_return( flexmock(read=lambda: 'file contents') ))


Expectation Matching
====================

Creating an expectation with no arguments will by default match all
arguments, including no arguments.

::

    >>> flexmock(plane).should_receive('fly').and_return('ok')

Will be matched by any of the following:

::

    >>> plane.fly()
    'ok'
    >>> plane.fly('up')
    'ok'
    >>> plane.fly('up', 'down')
    'ok'

You can also match exactly no arguments 

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args())

Or match any single argument

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args(object))

:NOTE: In addition to exact values, you can match against the type or class of the argument.

Match any single string argument

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args(str))

Match the empty string using a compiled regular expression

::

    regex = re.compile('^(up|down)$')
    (flexmock(plane)
        .should_receive('fly')
        .with_args(regex))

Match any set of three arguments where the first one is an integer,
second one is anything, and third is string 'foo'
(matching against user defined classes is also supported in the same fashion)

::

    (flexmock(plane)
        .should_receive('repair')
        .with_args(int, object, 'notes'))

And if the default argument matching based on types is not flexible enough,
flexmock will respect matcher objects that provide a custom __eq__ method.

For example, when trying to match against contents of numpy arrays,
equality is undefined by the library so comparing two of them directly
is meaningless unless you use all() or any() on the return value of the comparison.

What you can do in this case is create a custom matcher object and flexmock will
use its __eq__ method when comparing the arguments at runtime.

::

    class NumpyArrayMatcher(object):
        def __init__(self, array): self.array = array
        def __eq__(self, other): return all(other == self.array)

    (flexmock(obj)
        .should_receive('function')
        .with_args(NumpyArrayMatcher(array1)))

The above approach will work for any objects that choose not to return proper
boolean comparison values, or if you simply find the default equality and 
type-based matching not sufficiently specific.

It is, of course, also possible to create multiple expectations for the same
method differentiated by arguments.

::

    >>> flexmock(plane).should_receive('fly').and_return('ok')
    >>> flexmock(plane).should_receive('fly').with_args('up').and_return('bad')

Try to excecute plane.fly() with any, or no, arguments as defined by the first
flexmock call will return the first value.

::

    >>> plane.fly()
    'ok'
    >>> plane.fly('forward', 'down')
    'ok'

But! If argument values match the more specific flexmock call the function
will return the other return value.

::

    >>> plane.fly('up')
    'bad'

The order of the expectations being defined is significant, with later
expectations having higher precedence than previous ones. Which means
that if you reversed the order of the example expectations above the
more specific expectation would never be matched.

Style
=====

While the order of modifiers is unimportant to flexmock, there is a preferred convention
that will make your tests more readable.

If using with_args(), place it before should_return(), and_raise() and and_yield() modifiers:

::

    (flexmock(plane)
        .should_receive('fly')
        .with_args('up', 'down')
        .and_return('ok'))

If using the times() modifier (or its aliases: once, twice, never), place them at
the end of the flexmock statement:

::

    (flexmock(plane)
        .should_receive('fly')
        .and_return('ok')
        .once())
