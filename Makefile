quick:
	PYTHON_VERSIONS=2.6 RUNNERS=unittest ./tests/run_tests.sh

test:
	./tests/run_tests.sh

coverage:
	PYTHONPATH=. coverage run tests/flexmock_test.py 
	coverage html --omit tests\/flexmock_test\.py --include flexmock\.py
