"""
utils.py
Reusable functions for the latam-automotive-analytics pipeline.

Design principles
------------------
- All paths are RELATIVE to the repo root (anchored via pathlib, not hardcoded),
  so the project runs identically on your machine, on Colab, or in CI.
- Every download goes through `download_csv()` or `call_json_api()`, which
  centralize retries, timeouts, and logging. If a source changes its URL,
  there is exactly one place to fix it.
- `save_processed()` deduplicates by default. This exists because of a real bug
  found during development: the UN Comtrade preview endpoint returned ~35% exact
  duplicate rows for some queries (inflating totals by up to 300% in the worst
  cases). Deduplicating on save is a cheap, permanent guard against this class
  of error for any future data source.
"""

from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Optional

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Project paths (anchored to repo root, never to your local machine)
# ---------------------------------------------------------------------------
# utils.py lives in src/, so the repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Simple console logging (renders well inside notebooks)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("latam_ev")

# Some sites (e.g. Our World in Data) block requests carrying a generic library
# User-Agent and return a false 403. A real browser User-Agent avoids this.
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "text/csv,application/json,*/*",
}

# Target countries for this project (names as they appear in the OWID/IEA source)
OWID_COUNTRIES = ["Brazil", "Mexico", "Chile", "Colombia", "Peru", "Argentina", "Ecuador", "Bolivia"]

ISO3_TO_COUNTRY = {
    "BRA": "Brazil", "MEX": "Mexico", "CHL": "Chile", "COL": "Colombia",
    "PER": "Peru", "ARG": "Argentina", "ECU": "Ecuador", "BOL": "Bolivia",
}


def download_csv(url: str, destination: Path, params: Optional[dict] = None,
                  retries: int = 3, backoff_seconds: float = 2.0) -> pd.DataFrame:
    """
    Download a CSV from a URL and save it to `destination`.
    Retries with simple linear backoff on failure (useful for public APIs with
    informal rate limits).

    Returns the loaded DataFrame.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            log.info(f"Downloading (attempt {attempt}/{retries}): {url}")
            resp = requests.get(url, params=params, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            destination.write_bytes(resp.content)
            df = pd.read_csv(destination)
            log.info(f"OK -> {destination.relative_to(REPO_ROOT)} ({len(df)} rows)")
            return df
        except Exception as e:
            last_error = e
            log.warning(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)

    raise RuntimeError(
        f"Could not download {url} after {retries} attempts: {last_error}\n"
        "If the error is 403 / host blocked, check your internet connection or a "
        "corporate firewall/antivirus filtering the domain. Try pasting the URL "
        "directly into a browser first."
    )


def call_json_api(url: str, params: Optional[dict] = None,
                   retries: int = 3, backoff_seconds: float = 2.0) -> dict:
    """
    Call a JSON endpoint (Comtrade, BCRP, etc). Centralizes retries and error handling.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            log.warning(f"Attempt {attempt} on {url} failed: {e}")
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)
    raise RuntimeError(
        f"Could not fetch JSON from {url} after {retries} attempts: {last_error}\n"
        "If the error is 403 / host blocked, check your internet connection or a "
        "corporate firewall/antivirus filtering the domain. Try pasting the URL "
        "directly into a browser first."
    )


def save_processed(df: pd.DataFrame, filename: str, deduplicate: bool = True) -> Path:
    """
    Save a cleaned DataFrame to data/processed/ and return the path.

    Deduplicates exact-duplicate rows by default (see module docstring for why).
    If deduplication removes a large share of rows, a warning is logged so the
    issue is visible rather than silently hidden.
    """
    if deduplicate:
        rows_before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        rows_dropped = rows_before - len(df)
        if rows_dropped > 0:
            pct = rows_dropped / rows_before * 100
            level = log.warning if pct > 5 else log.info
            level(f"Deduplicated: removed {rows_dropped} exact-duplicate rows ({pct:.1f}%)")

    path = DATA_PROCESSED / filename
    df.to_csv(path, index=False)
    log.info(f"Saved -> {path.relative_to(REPO_ROOT)} ({len(df)} rows, {len(df.columns)} cols)")
    return path


# ---------------------------------------------------------------------------
# UN Comtrade country reference lookup
# ---------------------------------------------------------------------------
# The Comtrade preview endpoint reliably returns numeric partner codes
# (`partnerCode`) but the human-readable text field (`partnerDesc`) is often
# empty for the free/keyless preview tier. The robust fix is to resolve codes
# against Comtrade's own official reference table instead of trusting the
# text field to be populated.
COMTRADE_PARTNER_AREAS_URL = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"

_partner_lookup_cache: Optional[dict] = None


def get_comtrade_partner_lookup(force_refresh: bool = False) -> dict:
    """
    Download (once, then cache) the official UN Comtrade partner-country
    reference table and return it as {partner_code (str): country_name (str)}.

    This is what should be used to resolve `Origen_Code` into a readable
    country name — NOT the `partnerDesc` field, which is frequently blank
    on the free preview endpoint.
    """
    global _partner_lookup_cache
    if _partner_lookup_cache is not None and not force_refresh:
        return _partner_lookup_cache

    cache_path = DATA_RAW / "comtrade_partner_areas.json"
    try:
        if not cache_path.exists() or force_refresh:
            log.info("Downloading UN Comtrade partner-country reference table...")
            resp = requests.get(COMTRADE_PARTNER_AREAS_URL, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            cache_path.write_bytes(resp.content)
        import json
        raw = json.loads(cache_path.read_text())
        # The reference file wraps the array in a "results" envelope.
        entries = raw.get("results", raw if isinstance(raw, list) else [])
        lookup = {str(e.get("id")): e.get("text") for e in entries if e.get("id") is not None}
        _partner_lookup_cache = lookup
        log.info(f"Loaded {len(lookup)} partner-country reference entries.")
        return lookup
    except Exception as e:
        log.warning(
            f"Could not load Comtrade partner reference table ({e}). "
            "Falling back to an empty lookup — Origen_Code will stay unresolved "
            "until this succeeds. Re-run this cell once you have connectivity."
        )
        return {}
