#!/bin/sh
cd $(dirname $0)/..

pyenv global 3.11
python -m pip install --upgrade pip
pip install --upgrade -r streamlit XlsxWriter
pip freeze >requirements-all.txt
grep -E "streamlit|XlsxWriter" requirements-all.txt >requirements.txt
