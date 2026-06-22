# OpenPriors — turnkey pipeline (decomposer -> concept_graph -> matcher -> analogy -> grounding)
# Usage:  make setup  &&  make run  &&  make test
.PHONY: setup run test integration clean

VENV := decomposer/.venv
PY   := $(VENV)/bin/python
PP   := decomposer/src:concept_graph/src:matcher/src:analogy/src:grounding/src
export SOURCE_DATE_EPOCH := 1735689600   # reproducible artifacts

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -U pip
	$(PY) -m pip install -q -r decomposer/requirements.txt pytest

run:                       ## run the whole pipeline end-to-end
	PYTHONPATH=decomposer/src     $(PY) -m decomposer.cli
	PYTHONPATH=concept_graph/src  $(PY) -m concept_graph.cli
	PYTHONPATH=matcher/src:concept_graph/src $(PY) -m matcher.cli
	PYTHONPATH=analogy/src        $(PY) -m analogy.cli
	PYTHONPATH=grounding/src:analogy/src $(PY) -m grounding.cli

test:                      ## run every epic's unit tests + the integration test
	PYTHONPATH=$(PP) $(PY) -m pytest \
	  decomposer/tests concept_graph/tests matcher/tests analogy/tests grounding/tests \
	  tests/test_integration.py -q

integration:               ## just the cross-epic composition test
	PYTHONPATH=$(PP) $(PY) -m pytest tests/test_integration.py -q

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
