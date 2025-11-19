PYTHON=python3

install:
	pip install -r requirements.txt

run:
	$(PYTHON) benchmark.py

clean:
	rm -rf results/raw_responses/*
	rm -rf results/evaluations/*

reset:
	make clean
	rm -rf results
	mkdir -p results/raw_responses
	mkdir -p results/evaluations