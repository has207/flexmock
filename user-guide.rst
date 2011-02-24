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

Test runner integration
=======================


unittest / unittest2
--------------------

FlexMock, by default, assumes your tests are in a class that inherits
from unittest.TestCase, so if that's the case then all you need to do
is:

::

    from flexmock import flexmock

Nose
----

For normal nose tests, including those at module level, inside
unittest.TestCase classes or in other classes that nose recognizes:

::

    from flexmock import flexmock_nose as flexmock

Generator tests must be decorated by @with_setup(setup_func, flexmock_teardown()). The teardown for these tests is non-trivial to hook into -- if you can figure out a better way, please let me know.

Py.test
-------

::

  from flexmock import flexmock_pytest as flexmock

*(Should also work fine when running nose style tests or straight
unittest.TestCase tests)*

Other test runners
------------------

As far as I can tell most test runners out there support
unittest.TestCase so as long as your tests are in a class that inherits
from unittest.TestCase flexmock will just work, otherwise have a look at
other test runner integration and send me a patch.


Example Usage
=============


Make a mock object
------------------

::

  # using the param shortcuts -- limited to specifying attribute/return value pairs
  mock = flexmock(some_attribute="value", some_method=lambda: "another value")

  # using the more verbose approach -- gives more flexibility when you need it
  mock = flexmock()
  mock.should_receive("method2").with_args("foo", "bar").and_return("baz")
  mock.should_receive("method3").and_raise(Exception)

FlexMock mock objects support the full range of flexmock commands but
differ from partial mocks (described below) in that should_receive()
assigns them new methods rather than acting on methods they already
possess.

Partially mock or stub an existing object
-----------------------------------------

There are a few, basically equivalent, ways to hook into an existing
object and overwrite its methods:

::

    # mark the object as partially mocked, allowing it to be used to create new expectations
    flexmock(some_object)
    some_object.should_receive('method1').and_return('some return value').once
    some_object.should_receive('method2').and_return('some other return value').once

    # equivalent syntax assigns the object to a variable, possibly for brevity
    mock = flexmock(some_object)
    mock.should_receive('method1').and_return('some return value').once
    mock.should_receive('method2').and_return('some other return value').once

    # or you can combine everything into one line if there is only one method to overwrite
    flexmock(some_object).should_receive('method').and_return('some return value').once

    # you can also return the mock object after setting the expectations
    mock = flexmock(some_object).should_receive('method').and_return('some_value').mock

    # note the "mock" modifier above -- the expectation chain returns an expectation otherwise
    mock.should_receive('some_other_method').with_args().and_return('foo', 'bar')

You can leave off with_args() to match any arguments, and leave off and_return() to return None.

Stub out a method for all instances of a class
----------------------------------------------

::

    >>> class User: pass
    >>> flexmock(User)
    >>> User.should_receive('method_foo').and_return('value_bar')
    >>> user = User()
    >>> user.method_foo()
    'value_bar'``

Create automatically checked expectations
-----------------------------------------

Using the times(N) modifier, or its aliases -- once, twice, never --
allows you to create expectations that will be automatically checked by
the test runner.

::

    mock = flexmock(some_object)

    # ensure method_bar('a') gets called exactly three times
    mock.should_receive('method_bar').with_args('a').times(3)

    # ensure method_bar('b') gets called at least twice
    mock.should_receive('method_bar').with_args('b').at_least.twice

    # ensure method_bar('c') gets called at most once
    mock.should_receive('method_bar').with_args('c').at_most.once

    # ensure that method_bar('d') is never called
    mock.should_receive('method_bar').with_args('d').never

Raise exceptions
----------------

::

    flexmock(some_object).should_receive('some_method').and_raise(YourException)

    # or you can add a message to the exception being raised
    flexmock(some_object).should_receive('some_method').and_raise(YourException('exception message'))

Add a spy (or proxy) to a method
--------------------------------

In addition to stubbing out a given method and return fake values,
FlexMock also allows you to call the original method and make
expectations based on its return values/exceptions and the number of
times the method is called with the given arguments.

::

    # matching specific arguments
    flexmock(some_object).should_receive('method_bar').with_args(arg1, arg2).at_least.once.and_execute

    # matching any arguments
    flexmock(some_object).should_receive('method_bar').twice.and_execute

    # or using the short-hand
    flexmock(some_object).should_call('method_bar').once

    # matching specific return values
    flexmock(some_object).should_call('method_bar').and_return('foo')

    # or match return values by class/type
    flexmock(some_object).should_call('method_bar').and_return(str, object, None)

    # or ensuring that an appropriate exception is raised --
    flexmock(some_object).should_call('method_bar').and_raise(Exception)

    # or even checking that the exception message matches your expectations --
    flexmock(some_object).should_call('method_bar').and_raise(Exception("some error"))

If either and_return() or and_raise() is provided, flexmock will
verify that the return value matches the expected return value or
exception.

NOTE: should_call/and_execute changes the behavior of and_return()
and and_raise() to specify expectations rather than generate given
values or exceptions.

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

    # or use the short-hand form
    >>> flexmock(group).should_receive('get_member').and_return('user1', 'user2', 'user3').one_by_one

    # you can also mix return values with exception raises
    >>> flexmock(group).should_receive('get_member').and_return('user1').and_raise(Exception).and_return('user2')

Override "__new__" method on a class and return fake instances
------------------------------------------------------------------

Occasionally you will want a class to create fake objects when it's
being instantiated. FlexMock makes it easy and painless.

::

    >>> class Group(object): pass
    >>> flexmock(Group, new_instances='foo')
    >>> 'foo' == Group()
    True

Overriding new instances of old-style classes is currently not supported
directly, you should make the class inherit from "object" in your code
first. Luckily, multiple inheritance should make this pretty painless.

Create a mock generator
-----------------------

::

    >>> flexmock(foo).should_receive('gen').and_yield(1, 2, 3)
    >>> for i in foo.gen():
    >>>   print i
    1
    2
    3

Private methods
---------------

One of the small pains of writing unit tests is that it's a bit
difficult to get at the private methods since Python "conveniently"
renames them when you try to access them from outside the object. With
FlexMock there is nothing special you need to do to -- mocking private
methods is exactly the same as any other methods.

Enforcing call order
--------------------

::

    >>> flexmock(foo).should_receive('method_bar').with_args('bar').and_return('bar').ordered
    >>> flexmock(foo).should_receive('method_bar').with_args('foo').and_return('foo').ordered

    # now calling the methods in the same order will be fine
    >>> foo.method_bar('bar')
    'bar'
    >>> foo.method_bar('foo')
    'foo'

But trying to call the second one first will result in an exception!

Chained methods
---------------

Let's say you have some code that looks something like the following:

::

    http = HTTP()
    results = http.get_url('http://www.google.com').parse_html().retrieve_results()

You could use Flexmock to mock each of these method calls individually:

::

    mock = flexmock()
    flexmock(HTTP, new_instances=mock)
    mock.should_receive('get_url').and_return(
        flexmock().should_receive('parse_html').and_return(
            flexmock().should_receive('retrieve_results').and_return([]).mock
        ).mock
    )

But that looks really error prone and quite difficult to parse when
reading. Here's a better way:

::

    mock = flexmock()
    flexmock(HTTP, new_instances=mock)
    mock.should_receive('get_url.parse_html.retrieve_results').and_return([])

When using this short-hand, Flexmock will create intermediate objects
and expectations, returning the final one in the chain. As a result, any
further modifications, such as with_args() or times() modifiers, will
only be applied to the final method in the chain. If you need finer
grained control, such as specifying specific arguments to an
intermediate method, you can always fall back to the above long version.


Expectation Matching
====================

Creating an expectation with no arguments will by default match all
arguments, including no arguments.

::

    >>> flexmock(foo).should_receive('method_bar').and_return('bar')

    # will be matched by any of the following:
    >>> foo.method_bar()
    'bar'
    >>> foo.method_bar('foo')
    'bar'
    >>> foo.method_bar('foo', 'bar')
    'bar'

In addition to exact values, you can also match against the type or
class of the argument.

::

    # match any single argument
    flexmock(foo).should_receive('method_bar').with_args(object)

    # match any single string argument
    flexmock(foo).should_receive('method_bar').with_args(str)

    # match any set of three arguments where the first one is an integer,
    # second one is anything, and third is string 'foo'
    # (matching against user defined classes is also supported in the same fashion)
    flexmock(foo).should_receive('method_bar').with_args(int, object, 'foo')

You can also override the default match with another expectation for the
same method.

::

    >>> flexmock(foo).should_receive('method_bar').and_return('bar')
    >>> flexmock(foo).should_receive('method_bar').with_args('foo').and_return('foo')
    >>> foo.method_bar()
    'bar'
    >>> foo.method_bar('foo', 'bar')
    'bar'

    # but!
    >>> foo.method_bar('foo')
    'foo'``

The order of the expectations being defined is significant, with later
expectations having higher precedence than previous ones. Which means
that if you reversed the order of the example expectations above the
more specific expectation would never be matched.
