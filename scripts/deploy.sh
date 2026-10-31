#!/bin/sh
set -e
cd "$(dirname "$0")/.."

# cleanup
rm -f .DS_Store
rm -f -- ./*/.DS_Store

# spelling
sh scripts/run_spelling.sh

# ruff
uv run ruff format
uv run ruff check

sh scripts/run_pytest.sh

echo copying
# config.toml -> config-prod.toml
uv run --no-build scripts/config_convert.py
rsync -uz .streamlit/config-prod.toml entorb@mab.uberspace.de:be/strava-streamlit/.streamlit/config.toml
rsync -uz .streamlit/secrets.toml entorb@mab.uberspace.de:be/strava-streamlit/.streamlit/secrets.toml
rsync -uz requirements.txt entorb@mab.uberspace.de:be/strava-streamlit/
rsync -uz activity_columns.txt entorb@mab.uberspace.de:be/strava-streamlit/
rsync -ruzv --no-links --delete --delete-excluded --exclude __pycache__ --exclude r99_Playground.py src/ entorb@mab.uberspace.de:be/strava-streamlit/src/

# static files are under strava/
rsync -uz src/strava-resources/*.svg entorb@mab.uberspace.de:html/strava/strava-resources/

echo installing packages
ssh entorb@mab.uberspace.de "pip3.14 install --user -r be/strava-streamlit/requirements.txt > /dev/null"

echo restarting strava-streamlit
ssh entorb@mab.uberspace.de "supervisorctl restart streamlit-strava"

echo DONE
