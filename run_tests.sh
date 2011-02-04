#!/bin/sh

for version in 2.4 2.5 2.6 2.7 3.1 3.2; do
	if test -f "`which python$version`"; then
		echo python$version
		python$version flexmock_test.py
	else
		echo python$version NOT FOUND
	fi

	if test -f "$(which nosetests)"; then
		echo nosetests with python$version
		if python$version -c 'import nose' 2>/dev/null; then
			python$version $(which nosetests) flexmock_nose_test.py
		else
			echo nose not installed for python$version
		fi
	else
		echo nosetests NOT FOUND
	fi

	if test -f "$(which py.test)"; then
		echo py.test with python$version
		if python$version -c 'import py.test' 2>/dev/null; then
			python$version $(which py.test) flexmock_pytest_test.py
		else
			echo py.test not installed for python$version
		fi
	else
		echo py.test NOT FOUND
	fi
done
