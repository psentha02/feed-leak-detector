PY := venv/bin/python
SEED ?= 1

setup:
	python3 -m venv venv
	$(PY) -m pip install -q -r requirements.txt

data:
	$(PY) -m generator.scenarios --seed $(SEED)

eval:
	$(PY) -m evals.run_eval

app:
	$(PY) -m streamlit run app/streamlit_app.py

test:
	$(PY) -m pytest -q

.PHONY: setup data eval app test
