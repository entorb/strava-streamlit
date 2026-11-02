import sys
from pathlib import Path

sys.path.insert(0, (Path(__file__).parent.parent / "src").as_posix())
import helper_api
from helper_api import PER_PAGE, fetch_all_activities


def test_fetch_all_activities_stops_at_short_page(monkeypatch) -> None:
    sizes = {1: PER_PAGE, 2: PER_PAGE, 3: PER_PAGE, 4: 7}
    pages = []

    def fake(page: int, **_) -> list[dict]:
        pages.append(page)
        return [{}] * sizes.get(page, 0)

    monkeypatch.setattr(helper_api, "fetch_activities_page", fake)
    assert len(fetch_all_activities(year_start=0, year_end=0)) == 3 * PER_PAGE + 7
    assert sorted(pages) == [1, 2, 3, 4]
