.PHONY: all checkmake clean lint shellcheck style test unittest

all: checkmake shellcheck style lint test

checkmake:
	checkmake ./Makefile

clean:

lint:
	pylint --rcfile=./.pylintrc *.py || true

shellcheck:
	shellcheck *.sh || true

style:
	pycodestyle *.py || true

unittest:
#	python -m unittest tests/*.py

test: unittest
