#!/bin/sh
cd $(dirname $0)/..

streamlit run src/app.py
# for production better use
# python3.11 -O -m streamlit run src/app.py
