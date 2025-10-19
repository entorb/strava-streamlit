# Torben's Strava App V2 using Streamlit

This is a modern rewrite of my [old Strava Äpp](https://entorb.net/strava/). Currently, only read-only statistics features are implemented. For bulk modify of activities and Excel import, please use the old Äpp.

## Privacy

* **Code:** The [source-code](https://github.com/entorb/strava-streamlit/) is open source.
* **Data:** The app does not use a database. Your Strava data is only temporarily cached.
* **Access:** A temporary access token to your Strava profile is used and revoked at logout.
* **Cookies:** Only a single technical cookie is used for session identification and deleted at end of session. No user tracking.

## Repo Setup

### Python version

As my webserver is running Python 3.11, I need to use it locally too. See below.

### Install

see [install.sh](scripts/install.sh)

### Run

see [run.sh](scripts/run.sh)

### Check Code

```sh
pre-commit run --all-files
scripts/copy_test_data.sh
pytest --cov --cov-report=html:coverage_report
```

### Config

see [.streamlit/config.toml](.streamlit/config.toml)
see [.streamlit/secrets.toml](.streamlit/secrets-EXAMPLE.toml)

### SonarQube Code Analysis

At [sonarcloud.io](https://sonarcloud.io/summary/overall?id=entorb_template-python&branch=main)

If you want unit test coverage reports in SonarQube, you need to run the sonar check in the GitHub Action pipeline:

* disable the "Automatic Analysis" at <https://sonarcloud.io/project/analysis_method?id=entorb_strava-streamlit>
* setup SonarSource/sonarqube-scan-action@v5 in [check.yml](.github/workflows/check.yml)
* rename [.sonarcloud.properties](.sonarcloud.properties) to [sonar-project.properties](sonar-project.properties)
* generate a token at <https://sonarcloud.io/account/security>
* add this token as secret SONAR_TOKEN in GitHub

## TODOs

### Features

#### Open Feature TODOs

* some text to explain features

#### Done Feature TODOs

* activity caching: all or selected years only
* activity geo calculations
* gear download
* activity table
* activity statistics
* activity year summary
* activity active days per year
* known locations edit and list unknown frequent locations
* choose km vs. miles
* calendar export

### Technical Features

#### Open Dev TODOs

* why is supervisorctl log empty
`supervisorctl tail -f strava-streamlit`
* reconnect after token expired
* unit tests for act stats

#### Done Dev TODOs

* Strava login
* Strava logout/deauthorize
* Strava token refresh
* Strava logos and buttons
* API response caching for local dev environment
* unit tests using dummy activity data

## Deployment at Uberspace

### Python version for local dev

As my webserver is running Python 3.11, I need to use it locally too.

Variant 1: use venv

```sh
.pyenv/versions/3.11.9/bin/python -m venv .venv --prompt $(basename $(pwd))
source .venv/bin/activate
```

Variant 2: use global pyenv

```sh
pyenv global 3.11.9
eval "$(pyenv init -)"
```

`.vscode/settings.json`

```json
{
    "python.defaultInterpreterPath": ".pyenv/versions/3.11.9/bin/python"
}
```

### Setup

see <https://entorb.net/wickie/Uberspace#Streamlit>

```sh
mkdir ~/strava-streamlit

# run scripts/deploy.sh

pip3.11 install --user streamlit -r strava-streamlit/requirements.txt

# start it manually (stop by ctrl+c)
streamlit run main.py

# add web backend
uberspace web backend set /strava-streamlit --http --port 8501
```

verify it is working via browser <https://entorb.net/strava-streamlit>

stop streamlit via `ctrl+c`

create service `vim ~/etc/services.d/strava-streamlit.ini`

```ini
[program:strava-streamlit]
directory=%(ENV_HOME)s/strava-streamlit
command=python3.11 -O -m streamlit run src/main.py
loglevel=info
```

start service

```sh
supervisorctl reread
supervisorctl update
supervisorctl status
supervisorctl restart strava-streamlit
```

### Check log

```sh
 supervisorctl tail -f strava-streamlit
 tail -f ~/logs/supervisord.log
```

TODO: why is the output first command not showing the logs?

### Deploy update

see [deploy.sh](scripts/deploy.sh)
