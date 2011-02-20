Mock Library Comparison
=======================

This document shows a side-by-side comparison of how to accomplish some
basic tasks with Flexmock as well as other Python mocking libraries.
While it demonstrates that Flexmock is much less verbose, while
remaining just as capable, it is less interesting in my opinion as it
focuses on things that are already possible with existing libraries
instead of Flexmock's real strengths in allowing you to do things in
your tests that are either very difficult or completely impossible with
other existing tools.

This comparison is by no means complete, and there are a number of
libraries out there that are not covered here. In addition it probably
contains some amount of inaccuracies, so feel free to submit amendments
or examples for additional libraries.

Simple fake object
~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    mock = flexmock(some_method="calculated value", some_attribute="value")
    assertEquals("calculated value", mock.some_method())
    assertEquals("value", mock.some_attribute)

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndReturn("calculated value")
    mock.some_attribute = "value"
    mox.Replay(mock)
    assertEquals("value", mock.some_method())
    assertEquals("value", mock.some_attribute)

    # Python Mock module
    mymock = mock.Mock( {"some_method": "calculated value", "some_attribute": "value"})
    assertEquals("calculated value", mymock.some_method())
    assertEquals("value", mock.some_attribute)

    # pMock
    mock = pmock.Mock()
    mock.some_attribute = "value"
    mock.expects().some_method().will(pmock.return_value("calculated value"))
    assertEquals("value", mock.some_method())
    assertEquals("value", mock.some_attribute)

    # Mocker
    mock = mocker.mock()
    mock.some_method()
    mocker.result("calculated value")
    mocker.replay()
    mock.some_attribute = "value"
    assertEquals("calculated value", mock.some_method())
    assertEquals("value", mock.some_attribute)

Simple mock
~~~~~~~~~~~

::

    # Flexmock
    mock = flexmock()
    mock.should_receive(some_method).and_return("value").once
    assertEquals("value", mock.some_method())

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndReturn("value")
    mox.Replay(mock)
    assertEquals("value", mock.some_method())
    mox.Verify(mock)

    # Python Mock module
    mymock = mock.Mock( {"some_method" : "value"})
    assertEquals("value", mymock.some_method())
    mock.mockCheckCall(self, 0, "some_method")

    # pMock
    mock = pmock.Mock()
    mock.expects(pmock.once()).some_method().will(pmock.return_value("value"))
    assertEquals("value", mock.some_method())
    mock.verify()

    # Mocker
    mock = mocker.mock()
    mock.some_method()
    mocker.result("value")
    mocker.replay()
    assertEquals("value", mock.some_method())
    mocker.verify()

Creating partial mocks
~~~~~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    flexmock(SomeObject).should_receive(some_method).and_return('value')
    assertEquals("value", mock.some_method())

    # Mox
    mock = mox.MockObject(SomeObject)
    mock.some_method().AndReturn("value")
    mox.Replay(mock)
    assertEquals("hello", mock.some_method())
    mox.Verify(mock)

    # Python Mock module
    mock = mock.Mock({"some_method", "value"}, SomeObject)
    assertEquals("value", mock.some_method())
    mock.mockCheckCall(self, 0, "some_method")

    # pMock
    # Doesn't seem to have support for partial mocks

    # Mocker
    mock = mocker.mock(SomeObject)
    mock.Get()
    mocker.result("value")
    mocker.replay()
    assertEquals("value", mock.some_method())
    mocker.verify()

Ensure calls are made in specific order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    mock = flexmock(SomeObject)
    mock.should_receive('method1').once.ordered.and_return('first thing')
    mock.should_receive('method2').once.ordered.and_return('second thing')

    # Mox
    mock = mox.MockObject(SomeObject)
    mock.method1().AndReturn('first thing')
    mock.method2().AndReturn('second thing')
    mox.Replay(mock)
    mox.Verify(mock)

    # Python Mock module
    # Doesn't seem to support call ordering

    # pMock
    mock = pmock.Mock()
    mock.expects(pmock.once()).some_method().will(pmock.return_value("value"))
    mock_db.expects(pmock.once()).method1().id("method1")
    mock_db.expects(pmock.once()).method2().id("method2").after("method1")
    mock.verify()

    # Mocker
    mock = mocker.mock()
    with mocker.order():
      mock.method1()
      mocker.result('first thing')
      mock.method2()
      mocker.result('second thing')
      mocker.replay()
      mocker.verify()

Raising exceptions
~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    mock = flexmock()
    mock.should_receive('some_method').and_raise(SomeException('message'))
    assertRaises(SomeException, mock.some_method)

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndRaise(SomeException("message"))
    mox.Replay(mock)
    assertRaises(SomeException, mock.some_method)
    mox.Verify(mock)

    # Python Mock module
    mock = mock.Mock()
    mock.mockSetExpectation('some_method', expectException(SomeException))
    assertRaises(SomeException, mock.some_method)
    mock.mockCheckCall(self, 0, "some_method")

    # pMock
    mock = pmock.Mock()
    mock.expects(pmock.once()).some_method().will(pmock.raise_exception(SomeException("message")))
    assertRaises(SomeException, mock.some_method)
    mock.verify()

    # Mocker
    mock = mocker.mock()
    mock.some_method()
    mocker.throw(SomeException("message"))
    mocker.replay()
    assertRaises(SomeException, mock.some_method)
    mocker.verify()

Override new instances of a class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    flexmock(some_module.SomeClass, new_instances=some_other_object)
    assertEqual(some_other_object, some_module.SomeClass())

    # Mox
    # (you will probably have mox.Mox() available as self.mox in a real test)
    mox.Mox().StubOutWithMock(some_module, 'SomeClass', use_mock_anything=True)
    some_module.SomeClass().AndReturn(some_other_object)
    mox.ReplayAll()
    assertEqual(some_other_object, some_module.SomeClass())
    
    # Python Mock module
    # (TODO)
    
    # pMock
    # (TODO)
    
    # Mocker
    # (TODO)

Call the same method multiple times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Flexmock # (verifies that the method gets called at least twice)
    flexmock(some_object).should_receive('some_method').at_least.twice
    
    # Mox
    # (does not support variable number of calls, so you need to create a new entry for each explicit call)
    mock = mox.MockObject(some_object)
    mock.some_method(mox.IgnoreArg(), mox.IgnoreArg())
    mock.some_method(mox.IgnoreArg(), mox.IgnoreArg())
    mox.Replay(mock)
    mox.Verify(mock)
    
    # Python Mock module
    # (TODO)
    
    # pMock
    # (TODO)
    
    # Mocker
    # (TODO)

Mock chained methods
~~~~~~~~~~~~~~~~~~~~

::

    # Flexmock
    # (intermediate method calls are automatically assigned to temporary fake objects
    # and can be called with any arguments)
    flexmock(some_object).should_receive(
        'method1.method2.method3'
    ).with_args(arg1, arg2).and_return('some value')
    assertEqual('some_value', some_object.method1().method2().method3(arg1, arg2))

    # Mox
    mock = mox.MockObject(some_object)
    mock2 = mox.MockAnything()
    mock3 = mox.MockAnything()
    mock.method1().AndReturn(mock1)
    mock2.method2().AndReturn(mock2)
    mock3.method3(arg1, arg2).AndReturn('some_value')
    self.mox.ReplayAll()
    assertEquals("some_value", some_object.method1().method2().method3(arg1, arg2))
    self.mox.VerifyAll()

    # Python Mock module
    # (TODO)

    # pMock
    # (TODO)

    # Mocker
    # (TODO)
