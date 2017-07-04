PYTHON_VERSION := $(shell python -c 'import sys; print(sys.version_info[0])')

.PHONY: install uninstall install-dev-dependencies test docs clean

install:
	pip install .

uninstall:
	pip uninstall twitchobserver

install-dev-dependencies:
ifeq ($(PYTHON_VERSION), 2)
	pip install mock
endif

test:
	python -m unittest discover -s tests

docs:
	$(MAKE) -C ./docs html

clean:
	find . -name "*.pyc" -delete
	rm -rf .cache
	$(MAKE) -C ./docs clean
