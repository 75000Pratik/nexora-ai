import pytest

from app.core.rate_limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()

    yield

    limiter.reset()
