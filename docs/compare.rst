Mock Library Comparison
=======================

(flexmock for Mox or Mock users.)
---------------------------------------------------------------

This document shows a side-by-side comparison of how to accomplish some
basic tasks with flexmock as well as other popular Python mocking libraries.

Simple fake object (attributes only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    mock = flexmock(some_attribute="value", some_other_attribute="value2")
    assertEquals("value", mock.some_attribute)
    assertEquals("value2", mock.some_other_attribute)

    # Mox
    mock = mox.MockAnything()
    mock.some_attribute = "value"
    mock.some_other_attribute = "value2"
    assertEquals("value", mock.some_attribute)
    assertEquals("value2", mock.some_other_attribute)

    # Mock
    my_mock = mock.Mock()
    my_mock.some_attribute = "value"
    my_mock.some_other_attribute = "value2"
    assertEquals("value", my_mock.some_attribute)
    assertEquals("value2", my_mock.some_other_attribute)


Simple fake object (with methods)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    mock = flexmock(some_method=lambda: "calculated value")
    assertEquals("calculated value", mock.some_method())

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndReturn("calculated value")
    mox.Replay(mock)
    assertEquals("calculated value", mock.some_method())

    # Mock
    my_mock = mock.Mock()
    my_mock.some_method.return_value = "calculated value"
    assertEquals("calculated value", my_mock.some_method())


Simple mock
~~~~~~~~~~~

::

    # flexmock
    mock = flexmock()
    mock.should_receive("some_method").and_return("value").once()
    assertEquals("value", mock.some_method())

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndReturn("value")
    mox.Replay(mock)
    assertEquals("value", mock.some_method())
    mox.Verify(mock)

    # Mock
    my_mock = mock.Mock()
    my_mock.some_method.return_value = "value"
    assertEquals("value", mock.some_method())
    my_mock.some_method.assert_called_once_with()


Creating partial mocks
~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    flexmock(SomeObject).should_receive("some_method").and_return('value')
    assertEquals("value", mock.some_method())

    # Mox
    mock = mox.MockObject(SomeObject)
    mock.some_method().AndReturn("value")
    mox.Replay(mock)
    assertEquals("value", mock.some_method())
    mox.Verify(mock)

    # Mock
    with mock.patch("SomeObject") as my_mock:
      my_mock.some_method.return_value = "value"
      assertEquals("value", mock.some_method())


Ensure calls are made in specific order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    mock = flexmock(SomeObject)
    mock.should_receive('method1').once().ordered().and_return('first thing')
    mock.should_receive('method2').once().ordered().and_return('second thing')
    # exercise the code

    # Mox
    mock = mox.MockObject(SomeObject)
    mock.method1().AndReturn('first thing')
    mock.method2().AndReturn('second thing')
    mox.Replay(mock)
    # exercise the code
    mox.Verify(mock)

    # Mock
    mock = mock.Mock(spec=SomeObject)
    mock.method1.return_value = 'first thing'
    mock.method2.return_value = 'second thing'
    # exercise the code
    assert mock.method_calls == [('method1',) ('method2',)]


Raising exceptions
~~~~~~~~~~~~~~~~~~

::

    # flexmock
    mock = flexmock()
    mock.should_receive("some_method").and_raise(SomeException("message"))
    assertRaises(SomeException, mock.some_method)

    # Mox
    mock = mox.MockAnything()
    mock.some_method().AndRaise(SomeException("message"))
    mox.Replay(mock)
    assertRaises(SomeException, mock.some_method)
    mox.Verify(mock)

    # Mock
    my_mock = mock.Mock()
    my_mock.some_method.side_effect = SomeException("message")
    assertRaises(SomeException, my_mock.some_method)


Override new instances of a class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    flexmock(some_module.SomeClass).new_instances(some_other_object)
    assertEqual(some_other_object, some_module.SomeClass())

    # Mox
    # (you will probably have mox.Mox() available as self.mox in a real test)
    mox.Mox().StubOutWithMock(some_module, 'SomeClass', use_mock_anything=True)
    some_module.SomeClass().AndReturn(some_other_object)
    mox.ReplayAll()
    assertEqual(some_other_object, some_module.SomeClass())

    # Mock
    with mock.patch('somemodule.Someclass') as MockClass:
      MockClass.return_value = some_other_object
      assert some_other_object == some_module.SomeClass()


Verify a method was called multiple times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # flexmock (verifies that the method gets called at least twice)
    flexmock(some_object).should_receive('some_method').at_least().twice()
    # exercise the code
    
    # Mox
    # (does not support variable number of calls, so you need to create a new entry for each explicit call)
    mock = mox.MockObject(some_object)
    mock.some_method(mox.IgnoreArg(), mox.IgnoreArg())
    mock.some_method(mox.IgnoreArg(), mox.IgnoreArg())
    mox.Replay(mock)
    # exercise the code
    mox.Verify(mock)
    
    # Mock
    my_mock = mock.Mock(spec=SomeObject)
    # exercise the code
    assert my_mock.some_method.call_count >= 2


Mock chained methods
~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    # (intermediate method calls are automatically assigned to temporary fake objects
    # and can be called with any arguments)
    (flexmock(some_object)
        .should_receive('method1.method2.method3')
        .with_args(arg1, arg2)
        .and_return('some value'))
    assertEqual('some_value', some_object.method1().method2().method3(arg1, arg2))

    # Mox
    mock = mox.MockObject(some_object)
    mock2 = mox.MockAnything()
    mock3 = mox.MockAnything()
    mock.method1().AndReturn(mock1)
    mock2.method2().AndReturn(mock2)
    mock3.method3(arg1, arg2).AndReturn('some_value')
    self.mox.ReplayAll()
    assertEqual("some_value", some_object.method1().method2().method3(arg1, arg2))
    self.mox.VerifyAll()

    # Mock
    my_mock = mock.Mock()
    my_mock.method1.return_value.method2.return_value.method3.return_value = 'some value'
    method3 = my_mock.method1.return_value.method2.return_value.method3
    method3.assert_called_once_with(arg1, arg2)
    assertEqual('some_value', my_mock.method1().method2().method3(arg1, arg2))


Mock context manager
~~~~~~~~~~~~~~~~~~~~

::

    # flexmock
    my_mock = flexmock()
    with my_mock:
        pass

    # Mock
    my_mock = mock.MagicMock()
    with my_mock:
        pass

    # Mox
    my_mock = mox.MockAnything()
    with my_mock:
        pass


Mocking the builtin open used as a context manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following examples work in an interactive Python session but may not work
quite the same way in a script, or with Python 3.0+. See examples in the
:ref:`builtin_functions` section for more specific flexmock instructions
on mocking builtins.

::

    # flexmock
    (flexmock(__builtins__)
        .should_receive('open')
        .once()
        .with_args('file_name')
        .and_return(flexmock(read=lambda: 'some data')))
    with open('file_name') as f:
        assertEqual('some data', f.read())                    

    # Mox
    self_mox = mox.Mox()
    mock_file = mox.MockAnything()
    mock_file.read().AndReturn('some data')
    self_mox.StubOutWithMock(__builtins__, 'open')           
    __builtins__.open('file_name').AndReturn(mock_file)            
    self_mox.ReplayAll()
    with mock_file:
        assertEqual('some data', mock_file.read())
    self_mox.VerifyAll()

    # Mock
    with mock.patch('__builtin__.open') as my_mock:
        my_mock.return_value.__enter__ = lambda s: s
        my_mock.return_value.__exit__ = mock.Mock()
        my_mock.return_value.read.return_value = 'some data'
        with open('file_name') as h:
            assertEqual('some data', h.read())
    my_mock.assert_called_once_with('foo')


A possibly more up-to-date version of this document, featuring more mocking
libraries, is availale at:

http://garybernhardt.github.com/python-mock-comparison/

