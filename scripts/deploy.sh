#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

# exit upon error
set -e

# cleanup
rm -f .DS_Store
rm -f */.DS_Store

# ruff
uv run ruff check
uv run ruff format

sh scripts/pytest.sh

echo copying
# config.toml -> config-prod.toml
python3 scripts/config_convert.py
rsync -uz .streamlit/config-prod.toml entorb@entorb.net:strava-streamlit/.streamlit/config.toml
rsync -uz .streamlit/secrets.toml entorb@entorb.net:strava-streamlit/.streamlit/secrets.toml
rsync -uz requirements.txt entorb@entorb.net:strava-streamlit/
rsync -uz activity_columns.txt entorb@entorb.net:strava-streamlit/
rsync -ruzv --no-links --delete --delete-excluded --exclude __pycache__ --exclude r99_Playground.py src/ entorb@entorb.net:strava-streamlit/src/

echo installing packages
ssh entorb@entorb.net "pip3.11 install --user -r strava-streamlit/requirements.txt > /dev/null"

echo restarting strava-streamlit
ssh entorb@entorb.net "supervisorctl restart strava-streamlit"

echo DONE
