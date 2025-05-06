PYCODESTYLE_MAX_LINE_LENGTH=512
SOURCE_CODE_PATH=./src/visit_n_sites_and_collect
.PHONY: all checkmake clean lint shellcheck style test unittest

all: checkmake shellcheck style lint test

checkmake:
	checkmake ./Makefile

clean: clean_visited_urls

clean_visited_urls:
	python ./src/visit_n_sites_and_collect/clean_visited_urls.py

lint:
	pylint --rcfile=./.pylintrc ${SOURCE_CODE_PATH}/*.py || true

shellcheck:
	shellcheck 1 || true

style:
	pycodestyle --max-line-length=${PYCODESTYLE_MAX_LINE_LENGTH} *.py || true

unittest:
#	python -m unittest tests/*.py

test: unittest
