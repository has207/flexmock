#!/bin/sh

for version in 2.4 2.5 2.6 2.7 3.1; do
	if test -f "`which python$version`"; then
		echo python$version
		python$version flexmock_test.py
	else
		echo python$version NOT FOUND
	fi
done

if test -f "$(which nosetests)"; then
	echo nosetests
	nosetests flexmock_nose_test.py
else
	echo nosetests NOT FOUND
fi

if test -f "$(which py.test)"; then
	echo py.test
	py.test flexmock_pytest_test.py
else
	echo py.test NOT FOUND
fi
