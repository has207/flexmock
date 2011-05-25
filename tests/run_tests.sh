#!/bin/bash

PYTHON_VERSIONS=${PYTHON_VERSIONS:-"2.4 2.5 2.6 2.7 3.1 3.2"}
RUNNERS=${RUNNERS:-"unittest nose pytest"}
SCRIPT=$(cd ${0%/*} && echo $PWD/${0##*/})
TEST_PATH=$(dirname $SCRIPT)
FLEXMOCK_PATH=$(echo $TEST_PATH | sed -e s/tests$//)
export PYTHONPATH=$TEST_PATH:$FLEXMOCK_PATH:$PYTHONPATH

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
		if test -f "$(which nosetests)"; then
			echo nosetests with python$version
			if python$version -c 'import nose' 2>/dev/null; then
				python$version $(which nosetests) $TEST_PATH/flexmock_nose_test.py
			else
				echo nose not installed for python$version
			fi
		else
			echo nosetests NOT FOUND
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
done
