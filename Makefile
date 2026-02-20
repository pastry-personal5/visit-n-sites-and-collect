PYCODESTYLE_MAX_LINE_LENGTH=512
SOURCE_CODE_PATH=./src/visit_n_sites_and_collect
.PHONY: all checkmake clean lint shellcheck style test unittest regression_test regression_test_cloud

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
	uv run --python 3.11 pytest tests/regression*.py tests/regression

regression_test_cloud:
	RUN_CLOUD_STORAGE_TESTS=1 uv run --python 3.11 pytest tests/regression_test_cloud_file_storage.py tests/regression

test: unittest regression_test
