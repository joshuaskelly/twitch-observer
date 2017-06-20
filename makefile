.PHONY: install uninstall clean

install:
	pip install .

uninstall:
	pip uninstall twitchobserver

clean:
	find . -name "*.pyc" -delete