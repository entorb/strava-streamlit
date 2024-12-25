#!/bin/sh

# modify config
cp .streamlit/config.toml .streamlit/config-prod.toml
sed -i "" "s/watchdog/none/g" .streamlit/config-prod.toml
sed -i "" "s/address = /# address = /g" .streamlit/config-prod.toml
sed -i "" "s/# baseUrlPath/baseUrlPath/g" .streamlit/config-prod.toml
# transfer data
scp .streamlit/config-prod.toml entorb@entorb.net:strava-streamlit/.streamlit/config.toml
scp .streamlit/secrets.toml entorb@entorb.net:strava-streamlit/.streamlit/secrets.toml
scp src/*.py entorb@entorb.net:strava-streamlit/src/

ssh entorb@entorb.net "supervisorctl restart strava-streamlit"
