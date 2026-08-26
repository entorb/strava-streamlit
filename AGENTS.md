# strava-streamlit

Streamlit app for Strava activity analysis. Flat package, no database, dynamic page discovery.

## Commands

```sh
uv run -m streamlit run src/main.py   # run app
ruff format && ruff check --fix       # lint + format
scripts/copy_test_data.sh && uv run pytest  # seed test data, run tests
uv run pre-commit run --all-files     # all hooks
uv sync                               # install/update deps
```

## Architecture

- **Flat imports** — `src/` on `sys.path` (pytest config), no `__init__.py`. Import as `from helper_xxx import foo`.
- **Dynamic pages** — `src/reports/rNN_name.py` with `main()` = new page. `r99*` = admin-only (gated by `my_user_id` in `st.secrets`).
- **Env detection** — `get_env()` checks for `/home/entorb/strava-streamlit` on disk → PROD, else DEV. DEV enables local JSON caching + admin pages.
- **No database** — strava API responses cached as JSON in `cache/`. Locations in `data/knownLocations/*.txt`. City DB in `data/city-gps.dat`.
- **Caching** — `@st.cache_data(ttl="2h")` on activity fetch, `user_id` param in cache key for isolation.
- **Instrumentation** — `@track_function_usage` decorator wraps functions; call stats visible on `r99_internal_stats.py`.

## Testing

- Seed test data first: `scripts/copy_test_data.sh` (rsync `tests/testdata/` into `cache/` and `data/`)
- Smoke tests via `streamlit.testing.v1.AppTest` in `tests/test_reports.py`
- Unit tests in `tests/test_r20_activity_stats.py`, `tests/test_helper_activities_caching.py`
- CI runs: `ruff format --check` → `ruff check` → pytest → pre-commit

## Streamlit best practices

Existing skill at `.agents/skills/developing-with-streamlit/SKILL.md` covers: caching, layouts, theming, selection widgets, session state, CCv2, performance. Load it for Streamlit-specific work.

Key notes:

- `use_container_width` deprecated → use `width="stretch"`
- Config at `.streamlit/config.toml` (dev) and `.streamlit/config-prod.toml` (deployed)

## Lint & constraints

- Python 3.11 (`.python-version`, pre-commit default)
- Ruff: 88 cols, ALL lints, select ignores. `ruff.toml` is source of truth.
