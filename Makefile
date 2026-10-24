# Simple developer commands. Use the pinned Python 3.11 environment.
PYTHON ?= python

.PHONY: test-quick test-model test-full run-example

test-quick:
	$(PYTHON) scripts/test.py quick

test-model:
	$(PYTHON) scripts/test.py model

test-full:
	$(PYTHON) scripts/test.py full

run-example:
	$(PYTHON) -m cteas_ufotri.cli --case configs/test_case.yaml
