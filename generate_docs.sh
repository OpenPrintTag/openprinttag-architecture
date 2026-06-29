#!/bin/bash

python3 docs_src/generate.py
PYTHONPATH=. python3 docs_src/generate_llms.py
