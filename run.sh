#!/bin/bash
find ./ -type f -name "*.pyc"|xargs rm -f
find ./ -type d -name "__pycache__"|xargs rm -rf

PYTHONPATH=./src python -m casserver --debug --path "/cas" --assets "./assets"

