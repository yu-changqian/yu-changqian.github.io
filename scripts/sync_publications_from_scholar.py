#!/usr/bin/env python3
"""
Sync publications from Google Scholar → enrich via OpenAlex/DOI → output YAML.

Data flow:
  1. scholarly fetches the COMPLETE paper list from Google Scholar profile.
  2. For each paper, OpenAlex title search provides venue, DOI, arXiv ID, BibTeX.
  3. If OpenAlex misses the paper, scholarly.fill() is used as fallback for venue.
  4. BibTeX is fetched from DOI or generated as fallback.
  5. Papers already in _data/publications.yml (selected) are excluded.

Usage:
  python scripts/sync_publications_from_scholar.py --scholar-id Hv-vj2sAAAAJ
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CURATED_FILE = ROOT / "_data" / "publications.yml"
AUTO_FILE = ROOT / "_data" / "publications_all.yml"
STATS_FILE = ROOT / "_data" / "scholar_stats.yml"

OPENALEX_WORKS = "https://api.openalex.org/works"
DOI_BIBTEX = "https://doi.org/{doi}"
MY_NAMES = {"changqian yu", "kai wu"}
MY_NAME_DISPLAY = "Changqian Yu"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "yu-changqian-site-bot/1.0 (+https://yu-changqian.github.io)",
        "Accept": "application/json",
    }
)

# ---------------------------------------------------------------------------
# Venue mapping
# ---------------------------------------------------------------------------

VENUE_MAP = {
    # CV/ML workshops (before main conferences)
    "ieee conference on computer vision and pattern recognition workshops": ("CVPRW", "IEEE/CVF CVPR Workshops"),
    "ieee cvf conference on computer vision and pattern recognition workshops": ("CVPRW", "IEEE/CVF CVPR Workshops"),
    "ieee international conference on computer vision workshops": ("ICCVW", "IEEE/CVF ICCV Workshops"),
    "european conference on computer vision workshops": ("ECCVW", "ECCV Workshops"),
    # CV/ML conferences
    "ieee conference on computer vision and pattern recognition": ("CVPR", "IEEE/CVF Conference on Computer Vision and Pattern Recognition"),
    "ieee cvf conference on computer vision and pattern recognition": ("CVPR", "IEEE/CVF Conference on Computer Vision and Pattern Recognition"),
    "ieee international conference on computer vision": ("ICCV", "IEEE/CVF International Conference on Computer Vision"),
    "international conference on computer vision": ("ICCV", "IEEE/CVF International Conference on Computer Vision"),
    "european conference on computer vision": ("ECCV", "European Conference on Computer Vision"),
    "advances in neural information processing systems": ("NeurIPS", "Advances in Neural Information Processing Systems"),
    "international conference on learning representations": ("ICLR", "International Conference on Learning Representations"),
    "international conference on machine learning": ("ICML", "International Conference on Machine Learning"),
    "aaai conference on artificial intelligence": ("AAAI", "AAAI Conference on Artificial Intelligence"),
    "proceedings of the aaai conference on artificial intelligence": ("AAAI", "AAAI Conference on Artificial Intelligence"),
    "annual conference on neural information processing systems": ("NeurIPS", "Advances in Neural Information Processing Systems"),
    "conference on robot learning": ("CoRL", "Conference on Robot Learning"),
    "ieee international conference on robotics and automation": ("ICRA", "IEEE International Conference on Robotics and Automation"),
    # NLP conferences
    "annual meeting of the association for computational linguistics": ("ACL", "Annual Meeting of the Association for Computational Linguistics"),
    "conference on empirical methods in natural language processing": ("EMNLP", "Conference on Empirical Methods in Natural Language Processing"),
    "naacl-hlt": ("NAACL", "NAACL-HLT"),
    "north american chapter of the association for computational linguistics": ("NAACL", "NAACL-HLT"),
    "findings of the association for computational linguistics": ("Findings", "Findings of the Association for Computational Linguistics"),
    # Chinese CV conferences (before short journal names to avoid substring collision)
    "pattern recognition and computer vision": ("PRCV", "Chinese Conference on Pattern Recognition and Computer Vision"),
    # Journals
    "international journal of computer vision": ("IJCV", "International Journal of Computer Vision"),
    "ieee transactions on pattern analysis and machine intelligence": ("IEEE TPAMI", "IEEE Transactions on Pattern Analysis and Machine Intelligence"),
    "ieee transactions on image processing": ("IEEE TIP", "IEEE Transactions on Image Processing"),
    "ieee transactions on multimedia": ("IEEE TMM", "IEEE Transactions on Multimedia"),
    "ieee signal processing letters": ("IEEE SPL", "IEEE Signal Processing Letters"),
    "pattern recognition": ("PR", "Pattern Recognition"),
    "computer vision and image understanding": ("CVIU", "Computer Vision and Image Understanding"),
    "transactions on machine learning research": ("TMLR", "Transactions on Machine Learning Research"),
    # Multimedia
    "acm international conference on multimedia": ("ACM MM", "ACM International Conference on Multimedia"),
    "proceedings of the acm international conference on multimedia": ("ACM MM", "ACM International Conference on Multimedia"),
    "acm multimedia": ("ACM MM", "ACM International Conference on Multimedia"),
    # Other conferences
    "international conference on graphics and image processing": ("ICGIP", "International Conference on Graphics and Image Processing"),
    "ieee international conference on image processing": ("ICIP", "IEEE International Conference on Image Processing"),
    # Other journals
    "ieee transactions on cybernetics": ("IEEE TCYB", "IEEE Transactions on Cybernetics"),
    "neurocomputing": ("Neurocomputing", "Neurocomputing"),
    "journal of image and graphics": ("Journal of Image and Graphics", "Journal of Image and Graphics"),
    "caai transactions on intelligence technology": ("CAAI TIT", "CAAI Transactions on Intelligence Technology"),
    # Series names (low-value, should be overridden by BibTeX venue)
    "lecture notes in computer science": ("LNCS", "Lecture Notes in Computer Science"),
}

ACRONYM_TO_VENUE = {
    "CVPRW": ("CVPRW", "IEEE/CVF CVPR Workshops"),
    "ICCVW": ("ICCVW", "IEEE/CVF ICCV Workshops"),
    "ECCVW": ("ECCVW", "ECCV Workshops"),
    "CVPR": ("CVPR", "IEEE/CVF Conference on Computer Vision and Pattern Recognition"),
    "ICCV": ("ICCV", "IEEE/CVF International Conference on Computer Vision"),
    "ECCV": ("ECCV", "European Conference on Computer Vision"),
    "NEURIPS": ("NeurIPS", "Advances in Neural Information Processing Systems"),
    "NIPS": ("NeurIPS", "Advances in Neural Information Processing Systems"),
    "ICLR": ("ICLR", "International Conference on Learning Representations"),
    "ICML": ("ICML", "International Conference on Machine Learning"),
    "AAAI": ("AAAI", "AAAI Conference on Artificial Intelligence"),
    "ACL": ("ACL", "Annual Meeting of the Association for Computational Linguistics"),
    "EMNLP": ("EMNLP", "Conference on Empirical Methods in Natural Language Processing"),
    "NAACL": ("NAACL", "NAACL-HLT"),
    "ICRA": ("ICRA", "IEEE International Conference on Robotics and Automation"),
    "CORL": ("CoRL", "Conference on Robot Learning"),
    "ACM MM": ("ACM MM", "ACM International Conference on Multimedia"),
    "ACM MULTIMEDIA": ("ACM MM", "ACM International Conference on Multimedia"),
    "ICGIP": ("ICGIP", "International Conference on Graphics and Image Processing"),
    "ICIP": ("ICIP", "IEEE International Conference on Image Processing"),
    "PRCV": ("PRCV", "Chinese Conference on Pattern Recognition and Computer Vision"),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOPWORDS = {"the", "of", "on", "in", "and", "for", "a", "an", "at", "to", "proceedings"}


def normalize_venue_text(s: str) -> str:
    t = s.lower().replace("–", " ").replace("-", " ").replace("/", " ")
    t = re.sub(r"\b\d{4}\b", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _word_set(s: str, remove_stopwords: bool = False) -> set[str]:
    words = set(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())
    if remove_stopwords:
        words -= _STOPWORDS
        words = {w for w in words if not re.fullmatch(r"\d+(st|nd|rd|th)?", w)}
    return words


def title_signature(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:80] if s else "paper"


def venue_info(source_name: str) -> tuple[str, str]:
    if not source_name:
        return "Unknown", "Unknown venue"
    low = source_name.lower().strip()
    if "arxiv" in low:
        return "arXiv", "arXiv preprint"
    norm = normalize_venue_text(source_name)

    if low in VENUE_MAP:
        return VENUE_MAP[low]
    if norm in VENUE_MAP:
        return VENUE_MAP[norm]

    for ac, mapped in ACRONYM_TO_VENUE.items():
        if re.search(rf"\b{ac}\b", source_name, flags=re.IGNORECASE):
            return mapped

    source_cwords = _word_set(norm, remove_stopwords=True)
    for k, (short, full) in sorted(VENUE_MAP.items(), key=lambda kv: len(kv[0]), reverse=True):
        kn = normalize_venue_text(k)
        if not kn:
            continue
        if low in k or norm in kn:
            return short, full
        if kn in norm or k in low:
            key_cwords = _word_set(kn, remove_stopwords=True)
            if source_cwords and key_cwords:
                if len(key_cwords & source_cwords) / len(source_cwords) >= 0.6:
                    return short, full

    return source_name, source_name


def infer_venue_from_bibtex(bibtex: str | None) -> str | None:
    if not bibtex:
        return None
    for pat in [r"\bbooktitle\s*=\s*\{([^}]+)\}", r"\bjournal\s*=\s*\{([^}]+)\}"]:
        m = re.search(pat, bibtex, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def request_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = SESSION.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_bibtex_from_doi(doi_url: str | None) -> str | None:
    if not doi_url:
        return None
    doi = doi_url.replace("https://doi.org/", "").strip()
    if not doi:
        return None
    try:
        resp = SESSION.get(
            DOI_BIBTEX.format(doi=doi),
            headers={"Accept": "application/x-bibtex", "User-Agent": SESSION.headers["User-Agent"]},
            timeout=20,
        )
    except requests.RequestException:
        return None
    if resp.status_code >= 400:
        return None
    text = resp.text.strip()
    return text if text.startswith("@") else None


def fallback_bibtex(key: str, title: str, authors: str, year: int | None, venue_full: str) -> str:
    authors_clean = re.sub(r"<[^>]+>", "", authors)
    return (
        f"@article{{{key},\n"
        f"  title={{{title}}},\n"
        f"  author={{{authors_clean}}},\n"
        f"  journal={{{venue_full}}},\n"
        f"  year={{{year or 0}}}\n"
        f"}}"
    )


def load_yaml(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def save_yaml(path: Path, data: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)


# ---------------------------------------------------------------------------
# Google Scholar → paper list
# ---------------------------------------------------------------------------

def fetch_gs_publications(scholar_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return (publications, author_stats) from Google Scholar."""
    from scholarly import scholarly

    author = scholarly.search_author_id(scholar_id)
    author = scholarly.fill(author, sections=["publications"])
    stats = {
        "total_citations": int(author.get("citedby", 0)),
        "h_index": int(author.get("hindex", 0)),
        "i10_index": int(author.get("i10index", 0)),
    }
    return author.get("publications", []), stats


# ---------------------------------------------------------------------------
# OpenAlex enrichment (title-based search, no author-id dependency)
# ---------------------------------------------------------------------------

def enrich_from_openalex(title: str) -> dict[str, Any] | None:
    """Search OpenAlex by title and return enrichment data.

    When multiple versions exist (e.g. arXiv preprint + published paper),
    prefer the version with a formal venue.
    """
    sig = title_signature(title)
    try:
        data = request_json(OPENALEX_WORKS, params={"search": title, "per-page": 10})
    except requests.RequestException:
        return None

    candidates: list[dict[str, Any]] = []
    for work in data.get("results", []):
        wsig = title_signature(work.get("title", ""))
        if not wsig or not (sig == wsig or sig in wsig or wsig in sig):
            continue

        author_names = [
            (a.get("author") or {}).get("display_name", "").strip()
            for a in work.get("authorships", [])
        ]
        if not any(n.lower() in MY_NAMES for n in author_names):
            continue

        source_name = ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""
        doi_url = work.get("doi")

        arxiv_id = None
        for loc in work.get("locations") or []:
            src = (loc.get("source") or {}).get("host_organization_name") or ""
            for url in [loc.get("landing_page_url") or "", loc.get("pdf_url") or ""]:
                if "arxiv" in src.lower() or "arxiv.org" in url:
                    m = re.search(r"arxiv\.org/(abs|pdf)/([0-9]{4}\.[0-9]{4,5})", url)
                    if m:
                        arxiv_id = m.group(2)

        authors_list = []
        for a in work.get("authorships", []):
            name = (a.get("author") or {}).get("display_name", "").strip()
            if not name:
                continue
            if name.lower() in MY_NAMES:
                authors_list.append(f"<strong>{name}</strong>")
            else:
                authors_list.append(name)

        is_arxiv_source = "arxiv" in source_name.lower()
        is_arxiv_doi = "10.48550/arxiv" in (doi_url or "").lower()
        has_formal_doi = bool(doi_url) and not is_arxiv_doi

        candidates.append({
            "source_name": source_name,
            "doi_url": doi_url,
            "arxiv_id": arxiv_id,
            "authors_formatted": ", ".join(authors_list),
            "cited_by_count": int(work.get("cited_by_count") or 0),
            "year": work.get("publication_year"),
            "_is_formal": (not is_arxiv_source and not is_arxiv_doi) and (bool(source_name) or has_formal_doi),
        })

    if not candidates:
        return None

    formal = [c for c in candidates if c["_is_formal"]]
    best = formal[0] if formal else candidates[0]

    if not formal and candidates:
        for c in candidates:
            if c.get("arxiv_id") and not best.get("arxiv_id"):
                best["arxiv_id"] = c["arxiv_id"]

    best.pop("_is_formal", None)
    return best


# ---------------------------------------------------------------------------
# Scholarly fallback for venue
# ---------------------------------------------------------------------------

def fill_venue_from_scholarly(gs_pub: dict[str, Any]) -> str:
    """Call scholarly.fill() on a single publication to get venue."""
    try:
        from scholarly import scholarly

        filled = scholarly.fill(gs_pub)
        bib = filled.get("bib", {})
        return bib.get("conference") or bib.get("journal") or bib.get("venue") or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scholar-id", required=True)
    args = parser.parse_args()

    curated = load_yaml(CURATED_FILE)
    curated_sigs = {title_signature(p.get("title", "")) for p in curated if p.get("title")}

    curated_selected = [p for p in curated if p.get("selected")]
    if len(curated_selected) != len(curated):
        save_yaml(CURATED_FILE, curated_selected)
        curated = curated_selected
        print(f"[INFO] Trimmed curated file to selected-only: {len(curated)} entries")

    existing_auto = load_yaml(AUTO_FILE)
    existing_map: dict[str, dict[str, Any]] = {}
    for item in existing_auto:
        sig = title_signature(item.get("title", ""))
        existing_map[sig] = item

    print("[INFO] Fetching publications from Google Scholar ...")
    gs_pubs, gs_stats = fetch_gs_publications(args.scholar_id)
    print(f"[INFO] Google Scholar returned {len(gs_pubs)} publications")

    seen_keys: set[str] = set()
    results: list[dict[str, Any]] = []
    unfilled_gs_pubs: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for gs_pub in gs_pubs:
        bib = gs_pub.get("bib", {})
        title = (bib.get("title") or "").strip()
        if not title:
            continue
        year = int(bib.get("pub_year") or 0) or None
        citations = int(gs_pub.get("num_citations") or 0)

        sig = title_signature(title)
        if sig in curated_sigs:
            continue

        key_base = slug(title)
        key = f"auto-{year}-{key_base}" if year else f"auto-{key_base}"
        if key in seen_keys:
            key = f"{key}-{len(seen_keys)}"
        seen_keys.add(key)

        old = existing_map.get(sig)
        if old:
            key = old.get("key", key)

        enriched = enrich_from_openalex(title)
        time.sleep(0.15)

        if enriched:
            source_name = enriched["source_name"]
            doi_url = enriched["doi_url"]
            arxiv_id = enriched["arxiv_id"]
            authors = enriched["authors_formatted"]
            citations = max(citations, enriched.get("cited_by_count", 0))
            year = year or enriched.get("year")
        else:
            source_name = ""
            doi_url = None
            arxiv_id = None
            authors_raw = bib.get("author", "")
            parts = [a.strip() for a in re.split(r"\s+and\s+", authors_raw) if a.strip()]
            authors = ", ".join(
                f"<strong>{a}</strong>" if a.lower() in MY_NAMES else a for a in parts
            )

        is_arxiv = bool(arxiv_id) and not source_name
        venue, venue_full = venue_info(source_name) if source_name else ("Unknown", "Unknown venue")
        if is_arxiv and venue == "Unknown":
            venue, venue_full = "arXiv", "arXiv preprint"

        # Use Google Scholar citation string as venue hint
        # (e.g. "CVPR, 2026" or "European Conference on Computer Vision (ECCV), 325-341, 2018")
        gs_citation = bib.get("citation", "")
        if gs_citation:
            gs_venue_part = re.split(r",\s*\d{4}", gs_citation)[0].strip()
            gs_venue_part = re.sub(r",\s*[\d\-–]+$", "", gs_venue_part).strip()
            if gs_venue_part and "arxiv" not in gs_venue_part.lower():
                gs_v, gs_vf = venue_info(gs_venue_part)
                gs_rank = 0 if gs_v == "Unknown" else (1 if gs_v.lower() == "arxiv" else 2)
                cur_rank = 0 if venue == "Unknown" else (1 if venue.lower() == "arxiv" else 2)
                if gs_rank > cur_rank:
                    venue, venue_full = gs_v, gs_vf

        bib_text = fetch_bibtex_from_doi(doi_url)
        if not bib_text and arxiv_id:
            bib_text = fetch_bibtex_from_doi(f"https://doi.org/10.48550/arXiv.{arxiv_id}")

        inferred = infer_venue_from_bibtex(bib_text)
        if inferred:
            iv, ivf = venue_info(inferred)
            _SERIES = {"LNCS", "Lecture Notes in Computer Science"}
            from_bib_rank = 0 if iv == "Unknown" else (1 if iv.lower() == "arxiv" else 2)
            current_rank = 0 if venue == "Unknown" else (1 if venue.lower() == "arxiv" else 2)
            current_is_series = venue in _SERIES
            if from_bib_rank > current_rank or (current_is_series and from_bib_rank >= 2):
                venue, venue_full = iv, ivf

        if not bib_text:
            bib_text = fallback_bibtex(key, title, authors, year, venue_full)

        links: dict[str, str] = {}
        if doi_url:
            links["paper"] = doi_url
        if arxiv_id:
            links["arxiv"] = arxiv_id

        item = {
            "key": key,
            "title": title,
            "authors": authors,
            "venue": venue,
            "venue_full": venue_full,
            "year": int(year) if year else 0,
            "selected": False,
            "citations": citations,
            "links": links,
            "bibtex": bib_text,
        }

        if venue == "Unknown" and not enriched:
            unfilled_gs_pubs.append((gs_pub, item))
        else:
            results.append(item)

    if unfilled_gs_pubs:
        print(f"[INFO] Falling back to scholarly.fill() for {len(unfilled_gs_pubs)} papers without venue ...")
        for gs_pub, item in unfilled_gs_pubs:
            raw_venue = fill_venue_from_scholarly(gs_pub)
            if raw_venue:
                v, vf = venue_info(raw_venue)
                item["venue"] = v
                item["venue_full"] = vf
                if item["bibtex"].startswith("@article{"):
                    item["bibtex"] = fallback_bibtex(item["key"], item["title"], item["authors"], item.get("year"), vf)
            results.append(item)
            time.sleep(1.0)

    def _venue_rank(v: str) -> int:
        if not v or v == "Unknown":
            return 0
        if v.lower() == "arxiv":
            return 1
        return 2

    deduped: dict[str, dict[str, Any]] = {}
    for item in results:
        s = title_signature(item.get("title", ""))
        matched_key = None
        if s in deduped:
            matched_key = s
        else:
            for existing_sig in deduped:
                if s in existing_sig or existing_sig in s:
                    matched_key = existing_sig
                    break
        if matched_key:
            old = deduped[matched_key]
            old_rank = _venue_rank(old["venue"])
            new_rank = _venue_rank(item["venue"])
            if new_rank > old_rank or (new_rank == old_rank and item.get("citations", 0) > old.get("citations", 0)):
                deduped.pop(matched_key)
                deduped[s] = item
        else:
            deduped[s] = item

    final = sorted(deduped.values(), key=lambda x: (x.get("year", 0), x.get("title", "")), reverse=True)
    save_yaml(AUTO_FILE, final)
    print(f"[INFO] Wrote {len(final)} auto publications to {AUTO_FILE}")

    all_pubs = list(curated) + list(final)
    total_papers = len(all_pubs)
    all_citations = [int(p.get("num_citations") or p.get("citations") or 0) for p in gs_pubs]
    max_citations = max(all_citations) if all_citations else 0
    max_cited_paper = ""
    for gp in gs_pubs:
        if int(gp.get("num_citations") or 0) == max_citations:
            max_cited_paper = (gp.get("bib") or {}).get("title", "")
            break

    from datetime import date

    stats = {
        "total_citations": gs_stats.get("total_citations", 0),
        "h_index": gs_stats.get("h_index", 0),
        "i10_index": gs_stats.get("i10_index", 0),
        "total_papers": total_papers,
        "max_citations": max_citations,
        "max_cited_paper": max_cited_paper,
        "last_updated": date.today().isoformat(),
    }
    save_yaml(STATS_FILE, stats)
    print(f"[INFO] Wrote scholar stats to {STATS_FILE}: {stats['total_citations']} citations, {total_papers} papers")


if __name__ == "__main__":
    main()
