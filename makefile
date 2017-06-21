.PHONY: install uninstall test clean

install:
	pip install .

uninstall:
	pip uninstall twitchobserver

test:
	python -m unittest discover -s tests

clean:
	find . -name "*.pyc" -delete