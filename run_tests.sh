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
	nosetests flexmock_test.py
echo
	echo nosetests NOT FOUND
fi
