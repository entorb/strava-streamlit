#!/bin/sh
cd $(dirname $0)/..

# pyenv global 3.11.9
# eval "$(pyenv init -)"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip freeze >requirements-all.txt
# pyenv global 3.12.2
