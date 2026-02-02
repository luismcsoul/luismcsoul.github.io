#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel -> Jekyll Collections generator (with two-ring navigation)

Generates Markdown files into your Jekyll collections:

  _written-photography
  _photograph
  _taglines
  _personal-micro-dictionary
  _visualartwork
  _epistolary
  _sculpture
  _songs
  _article
  _capsule-review

Front matter includes:
- layout, collection, title, slug, schema_type, keywords, excerpt, media_*, taglines, references, album
- permalink: /:collection/:slug/
- managed_by: spreadsheet
- nav:
    prev_in_collection
    next_in_collection
    prev_collection
    next_collection
"""

import re
import sys
import unicodedata
import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd
import yaml

# ---------- PATHS ----------
ROOT = Path(__file__).resolve().parent.parent
DATA_XLSX = ROOT / "data" / "luismcsoul_content.xlsx"

# Collections folders (with underscores) that this generator manages
OUTPUT_COLLECTIONS = [
    "_written-photography",
    "_photograph",
    "_taglines",
    "_personal-micro-dictionary",
    "_visualartwork",
    "_epistolary",
    "_sculpture",
    "_songs",
    "_article",
    "_capsule-review",
]

# You already have this constant in your file. Keep it as-is.
# Finalized collection order (NO WRAP) — underscore style.
COLLECTION_ORDER = [
    "_written-photography",
    "_photograph",
    "_taglines",
    "_personal-micro-dictionary",
    "_visualartwork",
    "_epistolary",
    "_sculpture",
    "_songs",
    "_article",
    "_capsule-review",
]

# Map flexible names from Excel -> official Jekyll folder
COLL_MAP: Dict[str, str] = {
    "written photography": "_written-photography",
    "written-photography": "_written-photography",
    "written_photography": "_written-photography",

    "photograph": "_photograph",
    "photo": "_photograph",

    "taglines": "_taglines",
    "tagline": "_taglines",

    "personal micro dictionary": "_personal-micro-dictionary",
    "personal-micro-dictionary": "_personal-micro-dictionary",

    "visualartwork": "_visualartwork",
    "visual artwork": "_visualartwork",

    "epistolary": "_epistolary",

    "sculpture": "_sculpture",

    "songs": "_songs",
    "song": "_songs",

    "article": "_article",

    "capsule review": "_capsule-review",
    "capsule-review": "_capsule-review",
}

STOPWORDS = set((
    "a an and the of to in is are was were be been being for with on as at "
    "by from into over after before under above about against between among "
    "across within without not no nor but or so than too very just can will "
    "would could should might must also this that these those it its they "
    "them their you your we our i he she his her him my me mine ours yours "
    "theirs im ive id youre were theyre dont cant wont"
).split())

URL_RE = re.compile(r'https?://\S+', re.I)
NON_ALNUM = re.compile(r'[^A-Za-z0-9\s\-]')
SPACES = re.compile(r'\s+')
MULTIDASH = re.compile(r'-{2,}')


# ---------- HELPERS ----------

def to_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def first_nonempty_line(text: str) -> str:
    if not isinstance(text, str):
        return ""
    for line in text.splitlines():
        cleaned = line.strip(' "\t')
        if cleaned:
            return cleaned
    return ""


def clean_references_to_keywords(ref: str) -> List[str]:
    if not isinstance(ref, str) or not ref.strip():
        return []
    t = URL_RE.sub(" ", ref)
    t = NON_ALNUM.sub(" ", t)
    toks = [to_ascii(w.lower()) for w in t.split()]
    toks = [w for w in toks if w and w not in STOPWORDS and len(w) >= 3]
    out, seen = [], set()
    for w in toks:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:12]


def derive_keywords(title, body, provided_kw, refs, max_k=10):
    # use provided keywords first
    if isinstance(provided_kw, str) and provided_kw.strip():
        parts = [to_ascii(p.strip().lower())
                 for p in re.split(r'[;,]', provided_kw) if p.strip()]
    else:
        parts = clean_references_to_keywords(refs)

    # If still empty → extract from text
    if not parts:
        text = f"{title or ''} {body or ''}"
        text = URL_RE.sub(" ", text)
        text = NON_ALNUM.sub(" ", text)
        toks = [to_ascii(w.lower()) for w in text.split()]
        toks = [w for w in toks if w and w not in STOPWORDS and len(w) >= 3]
        if toks:
            order = {}
            for i, w in enumerate(toks):
                order.setdefault(w, i)
            vc = pd.Series(toks).value_counts()
            ranked = sorted(vc.index.tolist(), key=lambda w: (-vc[w], order[w]))
            parts = ranked

    # dedupe + cap at max_k
    seen, out = set(), []
    for w in parts:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= max_k:
            break
    return out


def seo_slug(title, body, provided_kw, refs, max_words=5, max_len=64):
    # get title tokens
    t = to_ascii((title or "").strip())
    t = NON_ALNUM.sub(" ", t)
    t = SPACES.sub(" ", t).strip().lower()
    title_tokens = [w for w in t.split() if w and w not in STOPWORDS]

    key_tokens = derive_keywords(title, body, provided_kw, refs, max_k=12)

    chosen = []
    for w in title_tokens + key_tokens:
        if w not in chosen:
            chosen.append(w)
        if len(chosen) >= max_words:
            break

    if not chosen:
        chosen = ["work"]

    slug = "-".join(chosen)
    slug = slug.replace("&", "and").replace("/", " ")
    slug = SPACES.sub("-", slug)
    slug = NON_ALNUM.sub("", slug).lower()
    slug = MULTIDASH.sub("-", slug).strip("-")
    if len(slug) > max_len:
        slug = slug[:max_len].strip("-")
    return slug or "work"


def sentence_excerpt(body: str, limit=160):
    if not isinstance(body, str) or not body.strip():
        return ""
    text = body.strip().replace("\r", " ")
    parts = re.split(r'(?<=[\.\!\?])\s+', text)
    for p in parts:
        s = p.strip().replace("\n", " ")
        if not s:
            continue
        if len(s) <= limit:
            return s
        # else truncate
        cut = s[:limit]
        cut = cut.rsplit(" ", 1)[0]
        return cut + "..."
    return ""


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    for col in ["collection", "slug", "title", "body_md", "excerpt", "order",
                "schema_type", "media_hero", "media_alt", "references",
                "keywords", "album", "taglines"]:
        if col not in df.columns:
            df[col] = None
    return df


def map_collection(value: str):
    key = (value or "").strip().lower().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())
    return COLL_MAP.get(key, None)


def parse_front_matter(path: Path):
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
        if not txt.startswith("---"):
            return {}
        end = txt.find("\n---", 3)
        if end == -1:
            return {}
        fm_text = txt[3:end]
        return yaml.safe_load(fm_text) or {}
    except Exception:
        return {}


# ---------- NAVIGATION MAP (two-ring, no-wrap) ----------

def build_navigation_map(df: pd.DataFrame) -> dict:
    """
    Returns a dict keyed by (collection_no_underscore, slug) with:
      {
        'prev_in_collection': '/collection/slug/' or None,
        'next_in_collection': '/collection/slug/' or None,
        'prev_collection':    '/prev-collection/first-item/' or None,
        'next_collection':    '/next-collection/first-item/' or None,
      }
    """
    # Normalize essentials used for ordering within collection
    rows = []
    for _, row in df.iterrows():
        coll_folder = map_collection(row.get("collection"))
        if not coll_folder:
            continue
        coll_no_us = coll_folder.lstrip("_")

        # Title (for stable sort fallback)
        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            title = first_nonempty_line(row.get("body_md"))
        if not title:
            title = "Untitled Work"

        # Slug (preliminary for mapping)
        provided_kw = row.get("keywords") or ""
        references = row.get("references") or ""
        body = row.get("body_md") or ""
        slug_in = row.get("slug")
        if isinstance(slug_in, str) and slug_in.strip():
            slug = slug_in.strip()
        else:
            slug = seo_slug(title, body, provided_kw, references)

        # Order (optional)
        order_val = row.get("order")
        try:
            order_num = int(order_val) if order_val is not None and str(order_val).strip() != "" else 10**9
        except Exception:
            order_num = 10**9

        permalink = f"/{coll_no_us}/{slug}/"
        rows.append({
            "coll": coll_no_us,
            "slug": slug,
            "title": title.strip().lower(),
            "order": order_num,
            "permalink": permalink
        })

    # Group by collection and sort within collection
    by_coll = {}
    for rec in rows:
        by_coll.setdefault(rec["coll"], []).append(rec)
    for c in by_coll:
        by_coll[c].sort(key=lambda r: (r["order"], r["title"], r["slug"]))

    # First item per collection (for up/down)
    first_item = {c: (by_coll[c][0]["permalink"] if by_coll[c] else None) for c in by_coll}

    # Build in-collection prev/next
    nav_map = {}
    for c, items in by_coll.items():
        n = len(items)
        for i, rec in enumerate(items):
            key = (c, rec["slug"])
            prev_in = items[i-1]["permalink"] if i > 0 else None
            next_in = items[i+1]["permalink"] if i < n-1 else None
            nav_map[key] = {
                "prev_in_collection": prev_in,
                "next_in_collection": next_in,
                "prev_collection": None,
                "next_collection": None,
            }

    # Determine non-wrapping prev/next collection by your curated order
    # NOTE: your order constant includes underscores; normalize to no-underscore for comparison
    order_no_us = [c.lstrip("_") for c in COLLECTION_ORDER]
    existing = [c for c in order_no_us if c in by_coll and len(by_coll[c]) > 0]
    index = {c: idx for idx, c in enumerate(existing)}

    for c in existing:
        idx = index[c]
        prev_c = existing[idx-1] if idx-1 >= 0 else None
        next_c = existing[idx+1] if idx+1 < len(existing) else None
        prev_link = first_item.get(prev_c) if prev_c else None
        next_link = first_item.get(next_c) if next_c else None

        # assign same prev/next collection for every item of c
        for rec in by_coll[c]:
            key = (c, rec["slug"])
            nav_map[key]["prev_collection"] = prev_link
            nav_map[key]["next_collection"] = next_link

    return nav_map


# ---------- MAIN ----------

def main():
    if not DATA_XLSX.exists():
        print(f"[ERROR] Excel not found: {DATA_XLSX}")
        return 1

    df = pd.read_excel(DATA_XLSX, engine="openpyxl")
    df = normalize_columns(df)

    # Ensure folders exist
    for folder in OUTPUT_COLLECTIONS:
        (ROOT / folder).mkdir(exist_ok=True)

    # Build nav lookup from the current Excel content
    nav_map = build_navigation_map(df)

    now = datetime.datetime.utcnow().isoformat() + "Z"
    seen = set()
    slug_used = {}

    for i, row in df.iterrows():
        coll_folder = map_collection(row.get("collection"))
        if not coll_folder:
            print(f"[WARN] Row {i+1}: unknown collection '{row.get('collection')}'. Skipping.")
            continue

        coll = coll_folder                # e.g., "_songs"
        coll_no_us = coll.lstrip("_")     # e.g., "songs"

        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            title = first_nonempty_line(row.get("body_md"))
        if not title:
            title = "Untitled Work"

        schema_type = row.get("schema_type")
        if not isinstance(schema_type, str) or not schema_type.strip():
            schema_type = "CreativeWork"

        provided_kw = row.get("keywords") or ""
        references = row.get("references") or ""
        body = row.get("body_md") or ""

        slug_in = row.get("slug")
        if isinstance(slug_in, str) and slug_in.strip():
            slug = slug_in.strip()
        else:
            slug = seo_slug(title, body, provided_kw, references)

        # ensure uniqueness within collection during this run
        base = slug
        n = slug_used.get((coll, slug), 0)
        while (coll, slug) in slug_used:
            n += 1
            slug = f"{base}-{n}"
        slug_used[(coll, slug)] = 1

        excerpt = row.get("excerpt")
        if not isinstance(excerpt, str) or not excerpt.strip():
            excerpt = sentence_excerpt(body)

        kw_list = derive_keywords(title, body, provided_kw, references, max_k=10)

        fm = {
            "layout": "work",
            "collection": coll_no_us,
            "title": title.strip(),
            "slug": slug,
            "schema_type": schema_type,
            "keywords": kw_list,
            "excerpt": excerpt,
            "media_hero": row.get("media_hero") or "",
            "media_alt": row.get("media_alt") or "",
            "taglines": row.get("taglines") or "",
            "references": references,
            "album": row.get("album") or "",
            "permalink": f"/{coll_no_us}/{slug}/",
            "managed_by": "spreadsheet",
            "last_generated": now,
        }

        # order (optional)
        order_val = row.get("order")
        try:
            if order_val is not None and str(order_val).strip() != "":
                fm["order"] = int(order_val)
        except Exception:
            pass

        # Attach nav (safe lookup)
        nav_key = (coll_no_us, slug)
        if nav_key in nav_map:
            fm["nav"] = {
                "prev_in_collection": nav_map[nav_key]["prev_in_collection"],
                "next_in_collection": nav_map[nav_key]["next_in_collection"],
                "prev_collection":    nav_map[nav_key]["prev_collection"],
                "next_collection":    nav_map[nav_key]["next_collection"],
            }

        md_path = ROOT / coll / f"{slug}.md"
        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
        content = f"---\n{front}---\n\n{body}\n"
        md_path.write_text(content, encoding="utf-8")
        seen.add(md_path.resolve())

    # deletion pass: remove previously managed files no longer present
    removed = 0
    for coll in OUTPUT_COLLECTIONS:
        for md_path in (ROOT / coll).glob("*.md"):
            if md_path.resolve() in seen:
                continue
            fm = parse_front_matter(md_path)
            if fm.get("managed_by") == "spreadsheet":
                md_path.unlink()
                removed += 1

    print(f"[INFO] Generation complete. Files removed: {removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())