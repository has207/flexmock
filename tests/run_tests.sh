#!/bin/bash

PYTHON_VERSIONS=${PYTHON_VERSIONS:-"2.4 2.5 2.6 2.7 3.1 3.2 3.3"}
PYTHON_IMPLEMENTATIONS=${PYTHON_IMPLEMENTATIONS:-"cpython pypy jython"}
RUNNERS=${RUNNERS:-"unittest nose pytest twisted"}
SCRIPT=$(cd ${0%/*} && echo $PWD/${0##*/})
TEST_PATH=$(dirname $SCRIPT)
FLEXMOCK_PATH=$(echo $TEST_PATH | sed -e s/tests$//)
export PYTHONPATH=$TEST_PATH:$FLEXMOCK_PATH:$PYTHONPATH

if echo $PYTHON_IMPLEMENTATIONS |grep -qw cpython; then
  for version in $PYTHON_VERSIONS; do
    if [[ "$RUNNERS" =~ unittest ]]; then
      if test -f "`which python$version`"; then
        echo python$version
        python$version $TEST_PATH/flexmock_unittest_test.py
      else
        echo python$version NOT FOUND
      fi
    fi

    if [[ "$RUNNERS" =~ nose ]]; then
      if test -f "$(which nosetests-$version)"; then
        echo nosetests with python$version
        if python$version -c 'import nose' 2>/dev/null; then
          $(which nosetests-$version) $TEST_PATH/flexmock_nose_test.py
        else
          echo nose not installed for python$version
        fi
      else
        echo nosetests-$version NOT FOUND
      fi
    fi

    if [[ "$RUNNERS" =~ pytest ]]; then
      if test -f "$(which py.test)"; then
        echo py.test with python$version
        if python$version -c 'import py.test' 2>/dev/null; then
          python$version $(which py.test) $TEST_PATH/flexmock_pytest_test.py
        else
          echo py.test not installed for python$version
        fi
      else
        echo py.test NOT FOUND
      fi
    fi

    if [[ "$RUNNERS" =~ twisted ]]; then
      if test -f "$(which trial-$version)"; then
        TRIAL=$(which trial-$version)
      elif test -f "$(which trial$version)"; then
        TRIAL=$(which trial$version)
      else
        TRIAL=''
        echo trial-$version or trial$version NOT FOUND
      fi
      if test -n "$TRIAL"; then
        echo "twisted (trial) with python$version"
        $TRIAL --reporter text $TEST_PATH/flexmock_pytest_test.py
        rm -rf _trial_temp/
      fi
    fi
  done
fi

for impl in $PYTHON_IMPLEMENTATIONS; do
  if test -f "$(which $impl)" && test "$impl" != "cpython"; then
    echo testing with $impl
    $impl $TEST_PATH/flexmock_test.py
  else
    echo $impl NOT FOUND
  fi
done
