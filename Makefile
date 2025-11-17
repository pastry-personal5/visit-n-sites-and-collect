PYCODESTYLE_MAX_LINE_LENGTH=512
SOURCE_CODE_PATH=./src/visit_n_sites_and_collect
.PHONY: all checkmake clean lint shellcheck style test unittest

all: checkmake shellcheck style lint test

checkmake:
	checkmake ./Makefile

clean_data: clean_visited_urls

clean_visited_urls:
	python -m src.visit_n_sites_and_collect.clean_visited_urls

lint:
	pylint --rcfile=./.pylintrc ${SOURCE_CODE_PATH}/*.py || true

shellcheck:
	shellcheck 1 || true

style:
	pycodestyle --max-line-length=${PYCODESTYLE_MAX_LINE_LENGTH} ${SOURCE_CODE_PATH}/*.py || true

unittest:
	uv run --python 3.11 python -m unittest tests/*.py

regression_test:
	uv run --python 3.11 python tests/regression_*.py

test: unittest regression_test
