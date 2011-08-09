Start Here
==========


So what does Flexmock actually help you do?


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

Flexmock provides an easier way to generate a fake object on the fly using the flexmock()
function:

::

  plane = flexmock(operational=True, model="MIG-21")


It is also possible to add methods to this object using the same notation and Python's handy
lambda keyword to turn an attribute into a method:

::

  plane = flexmock(operational=True,
                   model="MIG-21",
                   fly=lambda: None)


Objects created with the flexmock() function have an additional property
of supporting any and all methods and attributes without having to define them explicitly.
In other words, you can create a fake object and only have to worry about defining those attributes whose values you want to control explicitly.

::

  plane = flexmock()
  plane.model
  plane.fly()


In the example above, the "model" attribute as well as the "fly()" method both return the "plane" object itself.
Which means that chained method calls will succeed as well without any extra effort on your part.

::

  plane = flexmock()
  plane.fly().land().refuel()


You can also ask the object about which attributes and method were accessed, in what order, and what they returned:

::

  plane = flexmock()
  plane.fly().land().refuel()
  plane.__calls__
  ... [{'kargs': (), 'kwargs': {}, 'name': 'fly', 'returned': <flexmock.Mock object at 0x775a70>},
  ...  {'kargs': (), 'kwargs': {}, 'name': 'land', 'returned': <flexmock.Mock object at 0x775a70>},
  ...  {'kargs': (), 'kwargs': {}, 'name': 'refuel', 'returned': <flexmock.Mock object at 0x775a70>}]
  

Replacing parts of existing objects and classes (stubs)
-------------------------------------------------------


While creating fake objects from scratch is often sufficient, many times it is easier
to take an existing object and simply stub out certain methods or replace them with
fake ones. Flexmock makes this easy as well:

::

  flexmock(Train,
           get_destination="Tokyo",
           get_speed=200)


By passing a real object or class into the flexmock() function as the first argument
it is possible to modify that object in place and provide default return values for
any of its existing methods.

In addition to simply stubbing out return values, it can be useful to be able to call
an entirely different method and substitute return values based on test-specific conditions:

::

  flexmock(Train).should_receive("get_route").replace_with(
      lambda x: custom_get_route())
      

Creating and checking expectations (mocks)
------------------------------------------


Basic
~~~~~


Expectations take many flavors, and Flexmock has many different facilities and modes to generate them.
The first and simplest is ensuring that a certain method is called:

::

  flexmock(Train).should_receive("get_destination").once


The .once modifier ensures that Train.get_destination() is called at some point during the test and
will raise an exception if this does not happen.

Of course, it is also possible to provide a default return value:

::

  flexmock(Train).should_receive("get_destination").once.and_return("Tokyo")


Or check that a method is called with specific arguments:

::

  flexmock(Train).should_receive("set_destination").with_args("Tokyo").at_least.times(1)


In this example we used .times(1) instead of .once and added the .at_least modifier
to demonstate that it is easy to match any number of calls, including 0 calls or a variable amount of
calls.


Spies
~~~~~


While replacing method calls with canned return values or checking that they are called with
specific arguments is quite useful, there are also times when you want to execute the actual method
and simply find out how many times it was called. Flexmock uses should_call() to generate this
sort of expectations instead of should_receive():

::

  flexmock(Train).should_call("get_destination").once


In the above case the real get_destination() method will be executed, but Flexmock will raise
an exception unless it is executed exactly once. All the modifiers allowed with should_receive()
can also be used with should_call() so it is possible to tweak the allowed arguments, return
values and call times.

::

  flexmock(Train).should_call("set_destination").once.with_args(
      re.compile("^Tok")).and_raise(Exception, re.compile("^No such dest.*"))


The above example introduces a couple of new capabilities -- raising exceptions and regex
matching on string return values and arguments.

Flexmock has a number of other features and capabilities, but hopefully the above overview has
given you enough of the flavor for the kind of things that it makes possible. It is also important
to note that Flexmock features smooth integration with the test runner,
be it unittest, nose, py.test or doctest, so no special setup is necessary. Simply
importing flexmock into your test module is sufficient to get started with any of the above
examples.
