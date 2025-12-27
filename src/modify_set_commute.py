"""Modify Activity: set commute."""

import requests

# obtain token from Strava V1 Perl App
token = ""

# list of activities where I want to set the commute flag
ACTIVITIES = {16851917279}


def _api_put(url: str, data: dict) -> dict | list:
    try:
        resp = requests.put(url=url, data=data, headers=HEADERS, timeout=(3, 30))
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(e)
    return {}


# from helper_api import URL_BASE
URL_BASE = "https://www.strava.com/api/v3"
HEADERS = {"Authorization": f"Bearer {token}"}
BODY = {"commute": True}

for activity_id in ACTIVITIES:
    print(activity_id)
    url = URL_BASE + "/activities/" + str(activity_id)
    resp_dict = _api_put(url=url, data=BODY)
    assert type(resp_dict) is dict
    print(resp_dict["id"], resp_dict["name"])
