help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  test        to make unit tests run"

test:
	PYTHONPATH=${PWD}:${PYTHONPATH} python tests/manage.py test example

release:
	python setup.py sdist upload
