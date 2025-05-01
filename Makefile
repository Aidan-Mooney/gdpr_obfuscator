SHELL := /bin/bash

define execute_in_env
	export PYTHONPATH=. && source venv/bin/activate && $1
endef

create-environment:
	@echo ">>> Setting up Venv"
	python3 -m venv venv

install-requirements: create-environment
	@echo ">>> Installing external requirements."
	$(call execute_in_env, pip install -r ./requirements/requirements-external.txt)
	@echo ">>> Installing lambda requirements."
	$(call execute_in_env, pip install -r ./requirements/requirements-lambda.txt)

install-dev-tools: create-environment
	@echo ">>> Installing dev tools requirements"
	$(call execute_in_env, pip install -r ./requirements/requirements-dev-tools.txt)

run-checks: install-requirements install-dev-tools
	@echo ">>> Running pytest"
	$(call execute_in_env, pytest --testdox -vvvrP --cov=src --cov-fail-under=90 test/*)
	@echo ">>> Running security checks"
	$(call execute_in_env, bandit -lll */*.py *c/*.py)
	@echo ">>> Running ruff"
	$(call execute_in_env, ruff check src)
	$(call execute_in_env, ruff check test)
	