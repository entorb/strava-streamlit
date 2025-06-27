#!/bin/sh
cd $(dirname $0)/..

uv run -m streamlit run src/app.py

# # my webserver uses 3.11, so I use it for local dev too.
# pyenv global 3.11
# streamlit run src/app.py
# # for production better use
# # python3.11 -O -m streamlit run src/app.py
# pyenv global 3.13
