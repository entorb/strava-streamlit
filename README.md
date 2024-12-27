# Torben's Strava App V2 using Streamlit

This is a modern rewrite of my old [Strava Äpp](https://github.com/entorb/strava/), that was written in Perl.
Will be hosted later at <https://entorb.net/strava/>

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

## TODOs

### Dev

#### Open Dev TODOs

* why is supervisorctl log empty
`supervisorctl tail -f strava-streamlit`

#### Done Dev TODOs

* Strava login
* Strava logout/deauthorize
* Strava token refresh
* local API response caching
* unit tests using dummy activity data

### Features

#### Open Feature TODOs

* reconnect after token expired
* some text to explain features
* download stop after 2000 activities and button to continue
* download process

#### Done Feature TODOs

* activity download all data and convert to DataFrame
* activity geo calculations
* gear download gear data
* activity table
* activity status
* edit known locations
* list unknown frequent locations
* activity column order
* choose km vs. miles
* calendar export
* Strava logos and buttons

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
streamlit run app.py

# add web backend
uberspace web backend set /strava-streamlit --http --port 8501
```

verify it is working via browser <https://entorb.net/strava-streamlit>

stop streamlit via `ctrl+c`

create service `vim ~/etc/services.d/strava-streamlit.ini`

```ini
[program:strava-streamlit]
directory=%(ENV_HOME)s/strava-streamlit
command=python3.11 -O -m streamlit run src/app.py
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
```

TODO: why is the output of logger missing?

### Deploy update

see [deploy.sh](scripts/deploy.sh)
