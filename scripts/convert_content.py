#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel -> Jekyll Collections generator (with navigation)
-------------------------------------------------------

Reads data/luismcsoul_content.xlsx and generates Markdown files inside:
  _written-photography, _photograph, _taglines, _personal-micro-dictionary,
  _visualartwork, _epistolary, _sculpture, _songs, _article, _capsule-review

Adds front matter:
  nav:
    prev_in_collection: /collection/slug/
    next_in_collection: /collection/slug/
    prev_collection: /collection/first-item-slug/
    next_collection: /collection/first-item-slug/

No wrap between collections (top/bottom collections have no UP/DOWN links).
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

# Finalized collection order (NO WRAP)
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

OUTPUT_COLLECTIONS = COLLECTION_ORDER[:]  # same set

# flexible names from Excel -> canonical underscored folders
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

# ---------- helpers ----------
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
    if isinstance(provided_kw, str) and provided_kw.strip():
        parts = [to_ascii(p.strip().lower())
                 for p in re.split(r'[;,]', provided_kw) if p.strip()]
    else:
        parts = clean_references_to_keywords(refs)

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

    seen, out = set(), []
    for w in parts:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= max_k:
            break
    return out

def seo_slug(title, body, provided_kw, refs, max_words=5, max_len=64):
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
        cut = s[:limit]
        cut = cut.rsplit(" ", 1)[0]
        return cut + "..."
    return ""

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    for col in ["collection", "slug", "title", "body_md", "excerpt", "order",
                "schema_type", "media_hero", "media_alt", "references",
                "keywords", "album", "taglines"]:
