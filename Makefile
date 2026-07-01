# OpenPriors — turnkey pipeline
#   make run       front-end on raw docs: decompose -> concept graph -> match -> ground
#   make pipeline  graph layer over the already-grounded corpora (grounding/dgroups/,
#                  retrieval/library/): unify -> lineage -> analogy -> conjecture -> evaluate
#   make query     interrogate the unified graph    make test  every epic's tests
#   make demo      rebuild the interactive dashboard docs/index.html from live output
# Usage:  make setup  &&  make pipeline  &&  make test
.PHONY: setup run pipeline query demo report experiment test integration clean

VENV := decomposer/.venv
PY   := $(VENV)/bin/python
PP   := decomposer/src:concept_graph/src:matcher/src:analogy/src:grounding/src:retrieval/src:graph/src
GPP  := graph/src:retrieval/src:analogy/src:grounding/src
export SOURCE_DATE_EPOCH := 1735689600   # reproducible artifacts

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -U pip
	$(PY) -m pip install -q -r decomposer/requirements.txt pytest

run:                       ## run the front-end pipeline (decompose -> ground)
	PYTHONPATH=decomposer/src     $(PY) -m decomposer.cli
	PYTHONPATH=concept_graph/src  $(PY) -m concept_graph.cli
	PYTHONPATH=matcher/src:concept_graph/src $(PY) -m matcher.cli
	PYTHONPATH=analogy/src        $(PY) -m analogy.cli
	PYTHONPATH=grounding/src:analogy/src $(PY) -m grounding.cli

pipeline:                  ## the capstone: full graph pipeline over three literatures, one summary
	PYTHONPATH=$(GPP) $(PY) -m graphstore.pipeline

query:                     ## interrogate the unified graph (path / ancestor / analogy / conjecture)
	PYTHONPATH=$(GPP) $(PY) -m graphstore.dsl_cli

experiment:                ## run the proposed research-direction experiments (C2 finite-MDP, C4 EM)
	PYTHONPATH=graph/src $(PY) -m graphstore.experiment_c2
	PYTHONPATH=graph/src $(PY) -m graphstore.experiment_c4

demo:                      ## rebuild the interactive dashboard docs/index.html from live output
	$(PY) demo/build_demo.py

report:                    ## regenerate REPORT.md — the consolidated audit report, live from the pipeline
	PYTHONPATH=demo:$(GPP) $(PY) report/build_report.py

test:                      ## run every epic's unit tests + the integration test
	PYTHONPATH=$(PP) $(PY) -m pytest \
	  decomposer/tests concept_graph/tests matcher/tests analogy/tests grounding/tests \
	  retrieval/tests graph/tests tests/test_integration.py -q

integration:               ## just the cross-epic composition test
	PYTHONPATH=$(PP) $(PY) -m pytest tests/test_integration.py -q

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
