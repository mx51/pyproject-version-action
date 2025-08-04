#!/usr/bin/env make

include Makehelp.mk

###Core

## Create/activate python virtualenv
venv:
	python3 -m venv .venv && . .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt -r requirements-dev.txt
.PHONY: venv


## Perform fmt, lint and type checks
check: check-fmt check-lint check-type
.PHONY: check


## Format python code using black
fmt:
	. .venv/bin/activate && ruff format . && ruff check --fix .
.PHONY: fmt


## Perform code format using black
check-fmt:
	. .venv/bin/activate && ruff format --check .
.PHONY: check-fmt


## Perform pylint check
check-lint:
	. .venv/bin/activate && ruff check .
.PHONY: check-lint


## Perform mypy check
check-type:
	. .venv/bin/activate && mypy app tests
.PHONY: check-type



## Perform unit tests
test:
	. .venv/bin/activate && \
	coverage run -m pytest -v && \
	coverage xml -o reports/coverage.xml
.PHONY: test


## Clean python artefacts
clean:
	@rm -rf .pytest_cache .ruff_cache reports
	@echo "Cleanup complete."
.PHONY: clean

