PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PYTEST ?= $(PYTHON) -m pytest
KEYSUITE ?= $(PYTHON) -m reference.keysuite.src.main
EXAMPLE ?= C C . 3 3

.PHONY: bootstrap install test conformance run docs release-check clean

bootstrap:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt && pip install -e .

install:
	pip install -r requirements.txt
	pip install -e .

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTEST) -q -p no:cacheprovider

conformance:
	$(KEYSUITE) conformance conformance/vectors

docs:
	sh make_docs.sh

release-check: test conformance
	$(KEYSUITE) "$(EXAMPLE)"
	$(PYTHON) -m compileall -q reference tests
	./scripts/release_acceptance.sh
run:
	$(KEYSUITE) "$(EXAMPLE)"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache build dist *.egg-info *.zip
