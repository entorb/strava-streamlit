#!/bin/sh

echo copying
# modify config.toml -> config-prod.toml
python3 scripts/config_convert.py
# transfer data
rsync -uz .streamlit/config-prod.toml entorb@entorb.net:strava-streamlit/.streamlit/config.toml
rsync -uz .streamlit/secrets.toml entorb@entorb.net:strava-streamlit/.streamlit/secrets.toml
# scp src/*.py entorb@entorb.net:strava-streamlit/src/
rsync -ruzv --no-links --delete --delete-excluded --exclude __pycache__ src/ entorb@entorb.net:strava-streamlit/src/

echo restarting strava-streamlit
ssh entorb@entorb.net "supervisorctl restart strava-streamlit"
