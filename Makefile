.PHONY: test lint dist

all: test lint

init:
	pip3 install -r requirements.txt
	pip3 install -r tests/requirements.txt

test: init
	pip3 install -r requirements.txt
	pip3 install -r tests/requirements.txt
	pytest tests/

# flake8 failed to run in python3.7
# lint:
#	pip3 install -r tests/requirements.txt
#	flake8 . --exclude=env,virtualenv,.eggs,tests,dist

dist:
	python3 setup.py sdist

upload_pypi:
	python3 -m twine upload --repository pypi dist/atf-docker-0.0.5.tar.gz
