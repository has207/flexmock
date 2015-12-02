#!/bin/bash

PYTHON_IMPLEMENTATIONS=${PYTHON_IMPLEMENTATIONS:-"python pypy jython"}
python_VERSIONS=${PYTHON_VERSIONS:-"2.6 2.7 3.3 3.4 3.5"}
pypy_VERSIONS=${PYPY_VERSIONS:-"nover 3"}
jython_VERSIONS=${JYTHON_VERSIONS:-"nover"}

if [ -z "$PYEXECS" ]; then
  for impl in $PYTHON_IMPLEMENTATIONS; do
    IMPL_VERSIONS_VAR=${impl}_VERSIONS
    for ver in ${!IMPL_VERSIONS_VAR}; do
      if [ "$ver" == "nover" ]; then
        PYEXECS="$PYEXECS $impl"
      else
        PYEXECS="$PYEXECS $impl$ver"
      fi
    done
  done
fi

RUNNERS=${RUNNERS:-"unittest nose pytest twisted"}
SCRIPT=$(cd ${0%/*} && echo $PWD/${0##*/})
TEST_PATH=$(dirname $SCRIPT)
FLEXMOCK_PATH=$(echo $TEST_PATH | sed -e s/tests$//)
export PYTHONPATH=$FLEXMOCK_PATH:$TEST_PATH:$PYTHONPATH

for pyexec in $PYEXECS; do
  if [[ "$RUNNERS" =~ unittest ]]; then
    echo unittest for $pyexec
    if test -f "`which $pyexec 2>/dev/null`"; then
      $pyexec $TEST_PATH/flexmock_unittest_test.py
    else
      echo $pyexec NOT FOUND
    fi
  fi

  if [[ "$RUNNERS" =~ nose ]]; then
    if $pyexec -c 'import nose' 2>/dev/null; then
      echo nose for $pyexec
      $pyexec -m nose $TEST_PATH/flexmock_nose_test.py
    else
      echo nose for $pyexec NOT FOUND
    fi
  fi

  if [[ "$RUNNERS" =~ pytest ]]; then
    if $pyexec -c 'import py.test' 2>/dev/null; then
      echo py.test for $pyexec
      $pyexec -m py.test $TEST_PATH/flexmock_pytest_test.py
    else
      echo py.test for $pyexec NOT FOUND
    fi
  fi

  if [[ "$RUNNERS" =~ twisted ]]; then
    if $pyexec -c "from twisted.scripts.trial import run" 2>/dev/null; then
      echo twisted for $pyexec
      $pyexec -c "from twisted.scripts.trial import run; run();" $TEST_PATH/flexmock_pytest_test.py
      rm -rf _trial_temp/
    else
      echo twisted for $pyexec NOT FOUND
    fi
  fi
done
