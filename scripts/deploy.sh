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
uv run --no-build --no-project --with tomli-w scripts/config_convert.py
rsync -uz .streamlit/config-prod.toml entorb8@mab.uberspace.de:be/strava-streamlit/.streamlit/config.toml
rsync -uz .streamlit/secrets.toml entorb8@mab.uberspace.de:be/strava-streamlit/.streamlit/secrets.toml
rsync -uz requirements.txt entorb8@mab.uberspace.de:be/strava-streamlit/
rsync -uz activity_columns.txt entorb8@mab.uberspace.de:be/strava-streamlit/
rsync -ruzv --no-links --delete --delete-excluded --exclude __pycache__ --exclude r99_Playground.py src/ entorb8@mab.uberspace.de:be/strava-streamlit/src/

# static files are under strava/
rsync -uz src/strava-resources/*.svg entorb8@mab.uberspace.de:html/strava/strava-resources/

echo installing packages
ssh entorb8@mab.uberspace.de "python3.14 -m pip install -r be/strava-streamlit/requirements.txt > /dev/null"

echo restarting strava-streamlit
ssh entorb8@mab.uberspace.de "systemctl --user restart streamlit-strava"

echo DONE
