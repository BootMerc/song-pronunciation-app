"""Shared pytest fixtures.

The key one is db_path: cache.py points at a fixed DB_PATH constant by
default (backend/cache.db). Without isolation, tests would read/write
the real dev database — polluting it, leaking state between test runs,
and potentially colliding with a running dev server. autouse=True means
every test gets a fresh temp file automatically, without needing to
remember to request the fixture.
"""

import pytest


@pytest.fixture(autouse=True)
def db_path(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr("app.services.cache.DB_PATH", test_db)
    return test_db
