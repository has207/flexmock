from flexmock import flexmock
import unittest

class ModernClass(object):
  """Contains features only available in 2.6 and above."""
  def test_flexmock_should_support_with(self):
    foo = flexmock()
    with foo as mock:
      mock.should_receive('bar').and_return('baz')
    assert foo.bar() == 'baz'


class TestFlexmockUnittestModern(ModernClass, unittest.TestCase):
  def _tear_down(self):
    return unittest.TestCase.tearDown(self)
