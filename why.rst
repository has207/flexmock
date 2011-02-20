Why Flexmock?
=============

Food For Thought
----------------

While it's easy to write tests for brand new code that you specifically
craft to fit in with the testing metaphors permitted by a given mocking
library, it is much more difficult to take untested legacy code and add
unit tests. Due to various restrictions in the tools or the language
itself, it is often (always?) necessary to refactor legacy code to bring
it under test. This creates a chicken-egg problem of not being able to
refactor safely without tests and being unable to write tests without
refactoring. Dealing with this problem is non-trivial in practice and
having the right tools makes a huge difference both in speed and
ultimate success rate.

What We Have Now
----------------

Existing Python mocking libraries fall into two categories. The first
group (mox, mocker, pymock) follows the record/replay approach that
generally goes something along the lines of:

::

- setting up a mock
- specifying the methods you'll be replacing, along with return values, exceptions raised, etc
- replaying the replacement version
- exercising your code
- finally doing verification/unsetting the mocked methods

As you can imagine this approach requires a lot of manual effort to
write every single test, and for every single method you mock. In
addition, it is difficult to factor out common actions between tests as
you have to perform the replay step manually before the code is
exercised and then verify the mocks at the end, often also manually.

The second group of mocking libraries (pmock, mock, fudge) take a
somewhat more sensible approach:

::

- setting up a mock
- specifying the methods to replace, along with return values, exceptions raised, etc
- exercising the code
- doing the verification/cleanup

While these libraries allow you to skip the "replay" step, they still
have the same issues of verification at the end. Some of them provide
additional syntax, in the form of decorators or "teardown" methods you
can explicitly declare to help with some of the setup/verification
tedium. However, all they basically accomplish is shift the logic to a
different place, not free you from worrying about it altogether.

The Alternative
---------------

Flexmock provides a third alternative -- integration with the test
runner that takes care of the verification and cleanup steps, leaving
you with:

::

- creating the mock
- specifying expectations
- exercising the code

*(The first two steps can usually be combined into a single line of
code, reducing it to essentially one step.)*

It goes without saying that this is a lot less code, which makes writing
tests easier, faster, and less error-prone. But the fact that the entire
setup/verification logic of the mock can be generated before the code
under test is exercised offers another, less obvious, advantage. Namely,
you can factor out the mock code into helper functions and share them
across tests. Since Flexmock allows you to specify both the behavior of
the fake object along with any expectations, it makes it extremely
simple to generate helper functions that ensure that certain behavior is
verified across a number of different tests.

Let's Look At Some Code
-----------------------

As a quick example to bring this concept home, let's take a look at a
very simple servlet:

::

    class UserServlet:

      @classmethod
      def authenticate(cls):
        pass  # expensive authentication lookup

      @classmethod
      def create(cls, attrs):
        if cls.authenticate():
          User.create(attr)
        else:
          redirect_login()

      @classmethod
      def delete(cls, id):
        if cls.authenticate():
          User.delete(id)
        else:
          redirect_login()

*(I'm using class methods to avoid having to instantiate the UserServlet
in the following tests. In reality Flexmock handles both classes and
instances in the same manner, so this is only to simplify the example
while keeping it somewhat realistic.)*

And here is a test that ensures that the servlet properly authenticates
the request before performing the creation and deletion steps:

::

    from flexmock import flexmock
    from user_servlet import UserServlet
    from user_logic import User
    import unittest

    class TestUserServlet(unittest.TestCase):
      def _ensure_authenticated(self):
        flexmock(UserServlet).should_receive('authenticate').once.ordered

      def test_create(self):
        self._ensure_authenticated()
        flexmock(User).should_receive('create').once.with_args(name='eve').ordered
        UserServlet.create(name='eve')

      def test_delete(self):
        self._ensure_authenticated()
        flexmock(User).should_receive('delete').once.with_args(1231).ordered
        UserServlet.delete(1231)

    if __name__ == '__main__':
      unittest.main()

I intentionally added the imports and "main" call into the example test
to demonstrate that this is the **entire** test. Unlike other mocking
libraries, Flexmock does not require any extra magic in order to create
expectations or verify them, there is no hidden "teardown" method you
need to add to the test class, or decorators you need to hang on the
test methods.

This is the entire test, and it ensures that when UserServlet receives a
*create* or *delete* request, it first authenticates the user, then
performs the creation/deletion logic. Both the authentication function
and the database logic are mocked out and verified to have been called
in the correct order, with the correct arguments. This seems like an
extremely simple concept, but all other available mocking libraries seem
to make it rather awkward to implement.

To Sum Up
---------

The above example is extremely simple, and only showcases a fraction of
what Flexmock can do. In addition to the rather straightforward ability
to mock out methods and generate expectations, Flexmock features
powerful argument matching, based not just on values but on both
built-in and user-defined types or classes. It allows you to "spy" on
methods rather than stubbing them, calling the original method and
checking its return value or raised exceptions, as well as verify the
amount of times the method has been called. It can mock generators and
requires no special syntax for dealing with private and static methods,
module level functions, class level and instance methods. It also makes
it easy to override new instances of classes with custom objects.
