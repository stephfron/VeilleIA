"""Tests du cache fichier : TTL, fallback seed, mémoïsation RAM."""
import json
import time

import pandas as pd
import pytest

from utils import cache


@pytest.fixture()
def dirs(tmp_path, monkeypatch):
    raw, seed = tmp_path / "raw", tmp_path / "seed"
    raw.mkdir()
    seed.mkdir()
    monkeypatch.setattr(cache, "DATA_RAW_DIR", raw)
    monkeypatch.setattr(cache, "DATA_SEED_DIR", seed)
    return raw, seed


def test_load_prefers_fresh_primary(dirs):
    raw, seed = dirs
    (raw / "k.json").write_text('["primaire"]')
    (seed / "k.json").write_text('["seed"]')
    assert cache.load("k") == ["primaire"]


def test_load_falls_back_to_seed_when_primary_missing(dirs):
    _, seed = dirs
    (seed / "k.json").write_text('["seed"]')
    assert cache.load("k") == ["seed"]


def test_load_falls_back_to_seed_when_primary_expired(dirs):
    raw, seed = dirs
    p = raw / "k.json"
    p.write_text('["primaire"]')
    old = time.time() - 100_000
    import os
    os.utime(p, (old, old))
    (seed / "k.json").write_text('["seed"]')
    assert cache.load("k") == ["seed"]


def test_load_returns_none_without_primary_nor_seed(dirs):
    assert cache.load("absent") is None


def test_save_then_load_roundtrip(dirs):
    cache.save("k", {"a": 1})
    assert cache.load("k") == {"a": 1}


def test_memoize_caches_and_expires(monkeypatch):
    calls = {"n": 0}

    @cache.memoize(ttl=3600)
    def fn() -> pd.DataFrame:
        calls["n"] += 1
        return pd.DataFrame({"x": [calls["n"]]})

    a, b = fn(), fn()
    assert calls["n"] == 1
    assert a is b  # même objet, pas de re-parse

    fn.cache_clear()
    fn()
    assert calls["n"] == 2
