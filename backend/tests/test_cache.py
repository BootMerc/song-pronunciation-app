import time

from app.services import cache


class TestCache:
    def test_set_then_get_roundtrips(self):
        key = cache.make_key("Bohemian Rhapsody", "Queen")
        cache.set(key, {"lyrics_found": True, "lines": []})
        assert cache.get(key) == {"lyrics_found": True, "lines": []}

    def test_missing_key_returns_none(self):
        assert cache.get(cache.make_key("nope", "nobody")) is None

    def test_key_normalization_is_case_and_whitespace_insensitive(self):
        key_a = cache.make_key("Bohemian Rhapsody", "Queen")
        key_b = cache.make_key("  bohemian rhapsody  ", "QUEEN")
        assert key_a == key_b

    def test_expired_entry_treated_as_a_miss(self, monkeypatch):
        key = cache.make_key("Old Song", "Old Artist")
        cache.set(key, {"data": "stale"})
        # cache.time IS the global time module (not a copy), so the
        # replacement function must not call time.time() itself, or it
        # recurses into its own patched version. Capture the real value
        # first.
        future = time.time() + cache.TTL_SECONDS + 1
        monkeypatch.setattr(cache.time, "time", lambda: future)
        assert cache.get(key) is None

    def test_overwriting_an_existing_key(self):
        key = cache.make_key("Song", "Artist")
        cache.set(key, {"version": 1})
        cache.set(key, {"version": 2})
        assert cache.get(key) == {"version": 2}
