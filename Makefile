PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PYTEST ?= $(PYTHON) -m pytest
KEYSUITE ?= $(if $(wildcard .venv/bin/keysuite),.venv/bin/keysuite,keysuite)
EXAMPLE ?= C C . 3 3

.PHONY: bootstrap install test conformance run docs lint security web-install web-dev web-build web-check release-check clean bandit

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

lint:
	ruff check keysuite reference tests

security:
	bandit -c .bandit -r keysuite reference

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-check:
	cd web && npm run lint && npm run typecheck && npm run build

release-check: test conformance lint security web-check
	$(KEYSUITE) "$(EXAMPLE)"
	$(PYTHON) -m compileall -q keysuite reference tests
	./scripts/release_acceptance.sh

bandit: security

run:
	$(KEYSUITE) "$(EXAMPLE)"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache build dist *.egg-info *.zip
