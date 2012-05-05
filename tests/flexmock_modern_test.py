from flexmock import flexmock
import sys
import unittest

class ModernClass(object):
  """Contains features only available in 2.6 and above."""
  def test_context_manager_on_instance(self):
    class CM(object):
      def __enter__(self): pass
      def __exit__(self, *_): pass
    cm = CM()
    flexmock(cm).should_call('__enter__').once
    flexmock(cm).should_call('__exit__').once
    with cm: pass
    self._tear_down()

  def test_context_manager_on_class(self):
    class CM(object):
      def __enter__(self): pass
      def __exit__(self, *_): pass
    cm = CM()
    flexmock(CM).should_receive('__enter__').once
    flexmock(CM).should_receive('__exit__').once
    with cm: pass
    self._tear_down()

  def test_flexmock_should_support_with(self):
    foo = flexmock()
    with foo as mock:
      mock.should_receive('bar').and_return('baz')
    assert foo.bar() == 'baz'

  def test_builtin_open(self):
    if sys.version_info < (3, 0):
      mock = flexmock(sys.modules['__builtin__'])
    else:
      mock = flexmock(sys.modules['builtins'])
    fake_fd = flexmock(read=lambda: 'some data')
    mock.should_receive('open').once.with_args('file_name').and_return(fake_fd)
    with open('file_name') as f:
      data = f.read()
    self.assertEqual('some data', data)



class TestFlexmockUnittestModern(ModernClass, unittest.TestCase):
  def _tear_down(self):
    return unittest.TestCase.tearDown(self)


if __name__ == '__main__':
  unittest.main()
