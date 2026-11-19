import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """AI API 횟수 제한(분당 40번)은 시험 전체가 한 주소로 센다. 시험마다 비워 시험이 늘어도 429가 나지 않게 한다."""
    from careerlens import api
    api._hits.clear()
