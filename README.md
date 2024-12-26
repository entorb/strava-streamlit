# Torben's Strava App V2 using Streamlit

This is a modern rewrite of my old [Strava Äpp](https://github.com/entorb/strava/), that was written in Perl.
Will be hosted later at <https://entorb.net/strava/>

## Repo Setup

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

#### Done Feature TODOs

* activity: download all activities data and convert to DataFrame
* activity: geo calculations
* gear: download gear data
* activity table
* activity status
* edit known locations
* list unknown frequent locations
