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
import hashlib
import html
import re
import time
import unicodedata
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
MY_NAMES = {"changqian yu"}
MY_NAME_DISPLAY = "Changqian Yu"

# Opaque blocklist: entries are sha256 hashes so the list reveals nothing.
# Title hashes use title_signature(title); arXiv IDs and normalized author names use raw text.
EXCLUDED_TITLE_HASHES = {
    "9ab2e71b77fe7edd76e4643627198b0cac59a64142b162b2e6a1e087191c7da8",
    "f94f8231a345fb58b0c58b34da93bb4988de21a160d1a1864bf0cb0c74af1f94",
    "71f7d2ac81ec01fe21847234c534021008065605c443716736354858352f250f",
    "5e283e48121e03c8d2de6d5c88190e2f2649603dd6cdfdb7ee19067d43f22421",
}
EXCLUDED_ARXIV_HASHES = {
    "84222acdaae1b8c2d4546e3588d580a556e6d135dd9f7f9d9ba10217b6127efe",
    "86c1f86546f9193cfd457c5fb10241edb2e9fb494d139d4ed27e6eb95c478d25",
}
EXCLUDED_AUTHOR_HASHES = {
    "55a2f44e83b806b96505e2cf138299b0e2d5fc68948767f4c678c33af22e5a06",
    "9c5bf24af982e53766f1b391e86d9bc84450b710d3000f917c47cd4078f2db3f",
    "af650879958da1888cdef45c9bc2deea7514fb291703a505ca0c32ac5f013b89",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_excluded(title: str = "", arxiv_id: str | None = None) -> bool:
    if title and _sha256(title_signature(title)) in EXCLUDED_TITLE_HASHES:
        return True
    if arxiv_id and _sha256(arxiv_id) in EXCLUDED_ARXIV_HASHES:
        return True
    return False


def is_excluded_author(name: str) -> bool:
    cleaned = re.sub(r"\s+", " ", name.strip().lower())
    candidates = {cleaned, cleaned.replace(" ", "")}
    if "," in cleaned:
        last, first = [p.strip() for p in cleaned.split(",", 1)]
        flipped = re.sub(r"\s+", " ", f"{first} {last}".strip())
        candidates.add(flipped)
        candidates.add(flipped.replace(" ", ""))
    return any(_sha256(value) in EXCLUDED_AUTHOR_HASHES for value in candidates)


def bibtex_has_excluded_author(bib_text: str | None) -> bool:
    if not bib_text:
        return False
    m = re.search(r"\bauthor\s*=\s*\{([^}]+)\}", bib_text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return False
    raw_authors = re.sub(r"\s+", " ", m.group(1)).split(" and ")
    return any(is_excluded_author(a) for a in raw_authors if a.strip())

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
    folded = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", folded.lower())


def slug(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", folded.lower()).strip("-")
    return s[:80] if s else "paper"


def parse_author_names(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(name).strip() for name in raw if str(name).strip()]
    if isinstance(raw, str):
        separator = r"\s+and\s+" if re.search(r"\s+and\s+", raw) else r",\s*"
        return [name.strip() for name in re.split(separator, raw) if name.strip()]
    return []


def format_authors(raw: Any) -> str:
    names = parse_author_names(raw)
    return ", ".join(
        f"<strong>{name}</strong>" if name.lower() in MY_NAMES else name for name in names
    )


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


def clean_title_text(title: str) -> str:
    t = html.unescape(title or "").strip()
    t = re.sub(r"Fr(?:\\'|')echet", "Fréchet", t)
    t = re.sub(r"\s+", " ", t)
    return t


def extract_arxiv_id(text: str | None) -> str | None:
    if not text:
        return None
    for pat in [
        r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})",
        r"10\.48550/arxiv\.([0-9]{4}\.[0-9]{4,5})",
        r"\barxiv\s*:\s*([0-9]{4}\.[0-9]{4,5})\b",
    ]:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    if re.fullmatch(r"[0-9]{4}\.[0-9]{4,5}", text.strip()):
        return text.strip()
    return None


def is_arxiv_url_or_doi(url: str | None) -> bool:
    if not url:
        return False
    low = url.lower()
    return "arxiv.org/" in low or "10.48550/arxiv" in low


def normalize_links(raw_links: dict[str, str]) -> dict[str, str]:
    links: dict[str, str] = {}
    arxiv_id = extract_arxiv_id(raw_links.get("arxiv"))
    paper_url = (raw_links.get("paper") or "").strip()
    if paper_url:
        paper_arxiv = extract_arxiv_id(paper_url)
        if paper_arxiv or is_arxiv_url_or_doi(paper_url):
            arxiv_id = arxiv_id or paper_arxiv
        else:
            links["paper"] = paper_url
    if arxiv_id:
        links["arxiv"] = arxiv_id
    for k in ("code", "demo"):
        val = (raw_links.get(k) or "").strip()
        if val:
            links[k] = val
    return links


def fallback_bibtex(key: str, title: str, authors: str, year: int | None, venue_full: str) -> str:
    authors_clean = re.sub(r"<[^>]+>", "", authors or "").strip()
    authors_bib = " and ".join(a.strip() for a in authors_clean.split(",") if a.strip())
    is_conf = any(
        kw in (venue_full or "").lower()
        for kw in ("conference", "workshop", "neural information processing", "aaai", "multimedia", "iclr", "icml")
    )
    entry_type = "inproceedings" if is_conf else "article"
    venue_field = "booktitle" if is_conf else "journal"
    return (
        f"@{entry_type}{{{key},\n"
        f"  title={{{clean_title_text(title)}}},\n"
        f"  author={{{authors_bib}}},\n"
        f"  {venue_field}={{{venue_full}}},\n"
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
    author = scholarly.fill(author, sections=["indices", "counts", "publications"])
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
        if any(is_excluded_author(name) for name in author_names):
            return {"_excluded": True}
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
    best["is_formal"] = bool(formal)

    for c in candidates:
        if c.get("arxiv_id") and not best.get("arxiv_id"):
            best["arxiv_id"] = c["arxiv_id"]

    best.pop("_is_formal", None)
    return best


# ---------------------------------------------------------------------------
# arXiv enrichment (exact authors, venue acceptance comments, project/code URLs)
# ---------------------------------------------------------------------------

def search_arxiv_by_title(title: str) -> str | None:
    """Find an arXiv ID by exact title signature on arxiv.org search."""
    sig = title_signature(title)
    if not sig:
        return None
    query = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    query = re.sub(r"[^a-zA-Z0-9\s:-]+", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    try:
        resp = SESSION.get(
            "https://arxiv.org/search/",
            params={"query": query, "searchtype": "title", "source": "header"},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)"},
            timeout=15,
        )
    except requests.RequestException:
        return None
    if resp.status_code >= 400:
        return None
    for block in re.findall(r'<li class="arxiv-result">(.*?)</li>', resp.text, flags=re.S):
        id_m = re.search(r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5})", block)
        title_m = re.search(r'<p class="title[^"]*">(.*?)</p>', block, flags=re.S)
        if not id_m or not title_m:
            continue
        found_title = re.sub(r"<[^>]+>", "", title_m.group(1))
        fsig = title_signature(found_title)
        if fsig and (fsig == sig or sig in fsig or fsig in sig):
            return id_m.group(1)
    return None


def enrich_from_arxiv(arxiv_id: str) -> dict[str, Any] | None:
    """Fetch metadata from https://arxiv.org/abs/<id>."""
    clean_id = extract_arxiv_id(arxiv_id)
    if not clean_id:
        return None
    if is_excluded(arxiv_id=clean_id):
        return {"_excluded": True}
    try:
        resp = SESSION.get(
            f"https://arxiv.org/abs/{clean_id}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)"},
            timeout=15,
        )
    except requests.RequestException:
        return None
    if resp.status_code >= 400:
        return None

    title_m = re.search(r'<meta name="citation_title" content="([^"]+)"', resp.text)
    raw_authors = re.findall(r'<meta name="citation_author" content="([^"]+)"', resp.text)
    date_m = re.search(r'<meta name="citation_date" content="(\d{4})', resp.text)
    comment_m = re.search(r'<td class="tablecell comments mathjax">(.*?)</td>', resp.text, flags=re.S)

    norm_authors: list[str] = []
    for raw in raw_authors:
        raw_unescaped = html.unescape(raw).strip()
        if "," in raw_unescaped:
            last, first = [p.strip() for p in raw_unescaped.split(",", 1)]
            norm_authors.append(f"{first} {last}".strip())
        else:
            norm_authors.append(raw_unescaped)

    title = clean_title_text(title_m.group(1)) if title_m else ""
    if is_excluded(title=title, arxiv_id=clean_id):
        return {"_excluded": True}
    if any(is_excluded_author(a) for a in norm_authors):
        return {"_excluded": True}
    if norm_authors and not any(a.lower() in MY_NAMES for a in norm_authors):
        return None

    venue_hint: tuple[str, str] | None = None
    code_url: str | None = None
    demo_url: str | None = None

    if comment_m:
        comment_html = comment_m.group(1)
        comment_text = html.unescape(re.sub(r"<[^>]+>", " ", comment_html)).strip()
        low_c = comment_text.lower()
        if not any(neg in low_c for neg in ("submitted to", "under review", "preprint")):
            for ac, mapped in ACRONYM_TO_VENUE.items():
                if re.search(rf"\b{re.escape(ac)}\b", comment_text, flags=re.IGNORECASE):
                    venue_hint = mapped
                    break
        urls = [html.unescape(u).strip() for u in re.findall(r'href="([^"]+)"', comment_html)]
        for u in urls:
            if is_arxiv_url_or_doi(u):
                continue
            if "github.com/" in u.lower() and not code_url:
                code_url = u
            elif not demo_url:
                demo_url = u

    return {
        "title": title,
        "authors_formatted": format_authors(norm_authors) if norm_authors else "",
        "year": int(date_m.group(1)) if date_m else None,
        "venue_hint": venue_hint,
        "code_url": code_url,
        "demo_url": demo_url,
    }


# ---------------------------------------------------------------------------
# Scholarly fallback for venue
# ---------------------------------------------------------------------------

def fill_from_scholarly(gs_pub: dict[str, Any]) -> dict[str, Any]:
    """Call scholarly.fill() on a publication to recover missing metadata."""
    try:
        from scholarly import scholarly

        return scholarly.fill(gs_pub)
    except Exception:
        return {}


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

    # Keep curated/featured publications on the same Google Scholar citation
    # source as the automatically generated publication list.
    gs_citations = {
        title_signature((p.get("bib") or {}).get("title", "")): int(p.get("num_citations") or 0)
        for p in gs_pubs
        if (p.get("bib") or {}).get("title")
    }
    curated_updates = 0
    for item in curated:
        citation_count = gs_citations.get(title_signature(item.get("title", "")))
        if citation_count is not None and item.get("citations") != citation_count:
            item["citations"] = citation_count
            curated_updates += 1
    if curated_updates:
        save_yaml(CURATED_FILE, curated)
    print(f"[INFO] Updated Google Scholar citations for {curated_updates} curated publications")

    seen_keys: set[str] = set()
    results: list[dict[str, Any]] = []
    unfilled_gs_pubs: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for gs_pub in gs_pubs:
        bib = gs_pub.get("bib", {})
        title = clean_title_text(bib.get("title") or "")
        if not title:
            continue
        if any(is_excluded_author(name) for name in parse_author_names(bib.get("author", ""))):
            continue
        year = int(bib.get("pub_year") or 0) or None
        citations = int(gs_pub.get("num_citations") or 0)

        if is_excluded(title=title):
            continue

        sig = title_signature(title)
        if any(sig == curated_sig or sig in curated_sig or curated_sig in sig for curated_sig in curated_sigs):
            continue

        key_base = slug(title)
        key = f"auto-{year}-{key_base}" if year else f"auto-{key_base}"
        if key in seen_keys:
            key = f"{key}-{len(seen_keys)}"
        seen_keys.add(key)

        old = existing_map.get(sig)
        if old:
            key = old.get("key", key)

        gs_citation = bib.get("citation", "")
        arxiv_id = extract_arxiv_id(gs_citation)
        if not arxiv_id and old:
            old_links = old.get("links") or {}
            arxiv_id = extract_arxiv_id(old_links.get("arxiv")) or extract_arxiv_id(old_links.get("paper"))

        enriched = enrich_from_openalex(title)
        time.sleep(0.12)

        if enriched and enriched.get("_excluded"):
            continue
        if enriched:
            source_name = enriched["source_name"]
            doi_url = enriched["doi_url"]
            arxiv_id = enriched["arxiv_id"] or arxiv_id
            authors = enriched["authors_formatted"]
            citations = max(citations, enriched.get("cited_by_count", 0))
            if enriched.get("is_formal") and enriched.get("year"):
                year = enriched["year"]
            else:
                year = year or enriched.get("year")
            if is_excluded(arxiv_id=arxiv_id):
                continue
        else:
            source_name = ""
            doi_url = None
            authors = format_authors(bib.get("author", ""))

        if not arxiv_id and not enriched and (year or 0) >= 2022:
            arxiv_id = search_arxiv_by_title(title)

        arxiv_meta = None
        if arxiv_id and (not enriched or not enriched.get("is_formal")):
            arxiv_meta = enrich_from_arxiv(arxiv_id)
            if arxiv_meta and arxiv_meta.get("_excluded"):
                continue

        if arxiv_meta:
            if arxiv_meta.get("title"):
                title = arxiv_meta["title"]
            if arxiv_meta.get("authors_formatted"):
                authors = arxiv_meta["authors_formatted"]
            year = year or arxiv_meta.get("year")

        is_arxiv = bool(arxiv_id) and not source_name
        venue, venue_full = venue_info(source_name) if source_name else ("Unknown", "Unknown venue")
        if is_arxiv and venue == "Unknown":
            venue, venue_full = "arXiv", "arXiv preprint"

        if arxiv_meta and arxiv_meta.get("venue_hint"):
            av, avf = arxiv_meta["venue_hint"]
            cur_rank = 0 if venue == "Unknown" else (1 if venue.lower() == "arxiv" else 2)
            if cur_rank < 2:
                venue, venue_full = av, avf

        # Use Google Scholar citation string as venue hint
        # (e.g. "CVPR, 2026" or "European Conference on Computer Vision (ECCV), 325-341, 2018")
        if gs_citation and "…" not in gs_citation and "..." not in gs_citation:
            gs_venue_part = re.split(r",\s*\d{4}", gs_citation)[0].strip()
            gs_venue_part = re.sub(r",\s*[\d\-–]+$", "", gs_venue_part).strip()
            if gs_venue_part and "arxiv" not in gs_venue_part.lower():
                gs_v, gs_vf = venue_info(gs_venue_part)
                gs_rank = 0 if gs_v == "Unknown" else (1 if gs_v.lower() == "arxiv" else 2)
                cur_rank = 0 if venue == "Unknown" else (1 if venue.lower() == "arxiv" else 2)
                if gs_rank > cur_rank:
                    venue, venue_full = gs_v, gs_vf

        dropped_formal_doi = False
        bib_text = fetch_bibtex_from_doi(doi_url) if (doi_url and not is_arxiv_url_or_doi(doi_url)) else None
        if bibtex_has_excluded_author(bib_text):
            dropped_formal_doi = True
            bib_text = None
            doi_url = None
            source_name = ""
            if not arxiv_id:
                continue
            if not arxiv_meta:
                arxiv_meta = enrich_from_arxiv(arxiv_id)
                if arxiv_meta and arxiv_meta.get("_excluded"):
                    continue
                if arxiv_meta and arxiv_meta.get("authors_formatted"):
                    authors = arxiv_meta["authors_formatted"]
            venue, venue_full = ("arXiv", "arXiv preprint")

        inferred = infer_venue_from_bibtex(bib_text)
        if inferred:
            iv, ivf = venue_info(inferred)
            _SERIES = {"LNCS", "Lecture Notes in Computer Science"}
            from_bib_rank = 0 if iv == "Unknown" else (1 if iv.lower() == "arxiv" else 2)
            current_rank = 0 if venue == "Unknown" else (1 if venue.lower() == "arxiv" else 2)
            current_is_series = venue in _SERIES
            if from_bib_rank > current_rank or (current_is_series and from_bib_rank >= 2):
                venue, venue_full = iv, ivf

        links: dict[str, str] = {}
        if doi_url and not is_arxiv_url_or_doi(doi_url):
            links["paper"] = doi_url
        if arxiv_id:
            links["arxiv"] = arxiv_id
        if arxiv_meta:
            if arxiv_meta.get("code_url"):
                links["code"] = arxiv_meta["code_url"]
            if arxiv_meta.get("demo_url"):
                links["demo"] = arxiv_meta["demo_url"]

        if old:
            if not authors and old.get("authors"):
                authors = old["authors"]
            if venue == "Unknown" and old.get("venue") not in {None, "Unknown"}:
                venue = old["venue"]
                venue_full = old.get("venue_full", venue_full)
            if not year and old.get("year"):
                year = old["year"]
            old_links = dict(old.get("links") or {})
            if dropped_formal_doi:
                old_links.pop("paper", None)
            merged_links = {**old_links, **links}
            links = normalize_links(merged_links)
        else:
            links = normalize_links(links)

        if not bib_text or "author={}" in bib_text:
            bib_text = fallback_bibtex(key, title, authors, year, venue_full)

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
            filled = fill_from_scholarly(gs_pub)
            filled_bib = filled.get("bib", {})
            if any(is_excluded_author(name) for name in parse_author_names(filled_bib.get("author", ""))):
                continue
            raw_venue = (
                filled_bib.get("conference")
                or filled_bib.get("journal")
                or filled_bib.get("venue")
                or ""
            )
            if raw_venue:
                v, vf = venue_info(raw_venue)
                item["venue"] = v
                item["venue_full"] = vf

            filled_authors = format_authors(filled_bib.get("author", ""))
            if filled_authors:
                item["authors"] = filled_authors

            filled_year = int(filled_bib.get("pub_year") or filled_bib.get("year") or 0)
            if filled_year and not item.get("year"):
                item["year"] = filled_year
                item["key"] = f"auto-{filled_year}-{slug(item['title'])}"

            pub_url = filled.get("pub_url") or filled_bib.get("url")
            if pub_url and not item["links"].get("paper"):
                item["links"]["paper"] = pub_url
            item["links"] = normalize_links(item["links"])
            if item["links"].get("arxiv") and item["venue"] == "Unknown":
                item["venue"] = "arXiv"
                item["venue_full"] = "arXiv preprint"

            if not item.get("year") and item.get("venue") == "Unknown":
                continue

            if item["bibtex"].startswith(("@article{", "@inproceedings{")) or "author={}" in item["bibtex"]:
                item["bibtex"] = fallback_bibtex(
                    item["key"],
                    item["title"],
                    item["authors"],
                    item.get("year"),
                    item["venue_full"],
                )
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
