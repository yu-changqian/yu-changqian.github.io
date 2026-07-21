#!/usr/bin/env python3
"""
Fetch citation counts from Semantic Scholar and update _data/publications.yml.

Uses arXiv IDs (from links.arxiv) to query the Semantic Scholar API, which is
freely available and does not require authentication for low-volume requests.
"""

import sys
import time
from pathlib import Path

import requests
import yaml

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=citationCount"
DATA_FILE = Path(__file__).resolve().parent.parent / "_data" / "publications.yml"
REQUEST_DELAY = 1.5
MAX_RETRIES = 3


class QuotedStr(str):
    """String subclass that forces double-quoted YAML output."""


def _quoted_str_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


def _none_representer(dumper, _):
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")


yaml.add_representer(QuotedStr, _quoted_str_representer)
yaml.add_representer(type(None), _none_representer)


def _wrap_strings(obj):
    """Recursively wrap strings as QuotedStr; leave ints/bools untouched."""
    if isinstance(obj, dict):
        return {k: _wrap_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_wrap_strings(item) for item in obj]
    if isinstance(obj, str):
        return QuotedStr(obj)
    return obj


def fetch_citation_count(arxiv_id: str) -> int | None:
    url = SEMANTIC_SCHOLAR_API.format(arxiv_id=arxiv_id)
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  [WARN] Rate limited, retrying in {wait}s ...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json().get("citationCount")
        except requests.RequestException as e:
            print(f"  [WARN] API error for arXiv:{arxiv_id}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
    return None


def main():
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found")
        sys.exit(1)

    with open(DATA_FILE, encoding="utf-8") as f:
        publications = yaml.safe_load(f)

    updated, skipped, failed = [], [], []

    for pub in publications:
        key = pub.get("key", "unknown")
        arxiv_id = (pub.get("links") or {}).get("arxiv")

        if not arxiv_id:
            skipped.append(key)
            continue

        print(f"Fetching citations for {key} (arXiv:{arxiv_id}) ...")
        count = fetch_citation_count(arxiv_id)

        if count is not None:
            old = pub.get("citations")
            pub["citations"] = count
            updated.append((key, old, count))
            print(f"  -> {count} citations (was: {old})")
        else:
            failed.append(key)
            print("  -> failed to fetch")

        time.sleep(REQUEST_DELAY)

    publications = _wrap_strings(publications)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(
            publications,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    print("\n=== Summary ===")
    print(f"Updated: {len(updated)}")
    for key, old, new in updated:
        print(f"  {key}: {old} -> {new}")
    if skipped:
        print(f"Skipped (no arXiv ID): {', '.join(skipped)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
