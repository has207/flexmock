Start Here
==========


So what does flexmock actually help you do?


Creating fake objects
---------------------


Making a new object in Python requires defining a new class with all the
fake methods and attributes you're interested in emulating and then instantiating it.
For example, to create a FakePlane object to use in a test in place of a real Plane object we would need to do something like:

::

  class FakePlane(object):
      operational = True
      model = "MIG-21"
      def fly(self): pass

  plane = FakePlane()  # this is tedious!

In other words, we must first create a class, make sure it contains all required attributes and methods, and finally instantiate it to create the object.

flexmock provides an easier way to generate a fake object on the fly using the flexmock()
function:

::

  plane = flexmock(
                   operational=True,
                   model="MIG-21")


It is also possible to add methods to this object using the same notation and Python's handy lambda keyword to turn an attribute into a method:

::

  plane = flexmock(
                   operational=True,
                   model="MIG-21",
                   fly=lambda: None)


Replacing parts of existing objects and classes (stubs)
-------------------------------------------------------


While creating fake objects from scratch is often sufficient, many times it is easier
to take an existing object and simply stub out certain methods or replace them with
fake ones. flexmock makes this easy as well:

::

  flexmock(
           Train,  # this can be an instance, a class, or a module
           get_destination="Tokyo",
           get_speed=200)


By passing a real object (or class or module) into the flexmock() function as the first argument
it is possible to modify that object in place and provide default return values for
any of its existing methods.

In addition to simply stubbing out return values, it can be useful to be able to call
an entirely different method and substitute return values based on test-specific conditions:

::

  (flexmock(Train)
      .should_receive("get_route")
      .replace_with(lambda x: custom_get_route()))
      

Creating and checking expectations
----------------------------------
 
flexmock features smooth integration with pretty much every popular test runner, so no special setup is necessary. Simply
importing flexmock into your test module is sufficient to get started with any of the 
following examples.


Mocks
~~~~~


Expectations take many flavors, and flexmock has many different facilities and modes to generate them.
The first and simplest is ensuring that a certain method is called:

::

  flexmock(Train).should_receive("get_destination").once()


The .once() modifier ensures that Train.get_destination() is called at some point during the test and
will raise an exception if this does not happen.

Of course, it is also possible to provide a default return value:

::

  flexmock(Train).should_receive("get_destination").once().and_return("Tokyo")


Or check that a method is called with specific arguments:

::

  flexmock(Train).should_receive("set_destination").with_args("Tokyo").at_least().times(1)


In this example we used .times(1) instead of .once() and added the .at_least() modifier
to demonstate that it is easy to match any number of calls, including 0 calls or a variable amount of
calls. As you've probably guessed there is also an at_most() modifier.


Spies
~~~~~


While replacing method calls with canned return values or checking that they are called with
specific arguments is quite useful, there are also times when you want to execute the actual method
and simply find out how many times it was called. flexmock uses should_call() to generate this
sort of expectations instead of should_receive():

::

  flexmock(Train).should_call("get_destination").once()


In the above case the real get_destination() method will be executed, but flexmock will raise
an exception unless it is executed exactly once. All the modifiers allowed with should_receive()
can also be used with should_call() so it is possible to tweak the allowed arguments, return
values and call times.

::

  (flexmock(Train)
      .should_call("set_destination")
      .once()
      .with_args(object, str, int)
      .and_raise(Exception, re.compile("^No such dest.*")))


The above example introduces a handful of new capabilities -- raising exceptions, matching argument types (object naturally matches any argument type) and regex matching on string return values and arguments.


Summary
-------


flexmock has many other features and capabilities, but hopefully the above overview has
given you enough of the flavor for the kind of things that it makes possible. For more
details see the `User Guide`_.

.. _User Guide: user-guide.html
