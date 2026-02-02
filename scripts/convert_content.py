#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel -> Jekyll Collections generator
-------------------------------------

Reads data/luismcsoul_content.xlsx and generates Markdown files inside:
  _written-photography
  _sculpture
  _songs
  _taglines
  _visualartwork
  _article
  _capsule-review
  _epistolary
  _personal-micro-dictionary
  _photograph

Rules:
- schema_type: defaults to CreativeWork
- title: if empty, uses first non-empty line of body_md
- keywords: from "keywords" column OR from "references" OR extracted from body_md
- slug: SEO-friendly (2-5 good keywords, ascii, lowercase, unique)
- excerpt: first sentence <=160 chars
- Removing a row from Excel removes its file (only if managed_by=spreadsheet)
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

OUTPUT_COLLECTIONS = [
    "_written-photography",
    "_sculpture",
    "_songs",
    "_taglines",
    "_visualartwork",
    "_article",
    "_capsule-review",
    "_epistolary",
    "_personal-micro-dictionary",
    "_photograph",
]

# map flexible names from Excel -> official Jekyll folder
COLL_MAP: Dict[str, str] = {
    "written photography": "_written-photography",
    "written-photography": "_written-photography",
    "written_photography": "_written-photography",

    "sculpture": "_sculpture",

    "songs": "_songs",
    "song": "_songs",

    "taglines": "_taglines",
    "tagline": "_taglines",

    "visualartwork": "_visualartwork",
    "visual artwork": "_visualartwork",

    "article": "_article",

    "capsule review": "_capsule-review",
    "capsule-review": "_capsule-review",

    "epistolary": "_epistolary",

    "personal micro dictionary": "_personal-micro-dictionary",
    "personal-micro-dictionary": "_personal-micro-dictionary",

    "photograph": "_photograph",
    "photo": "_photograph",
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


# ---------- MAIN ----------

def main():
    if not DATA_XLSX.exists():
        print(f"[ERROR] Excel not found: {DATA_XLSX}")
        return 1

    df = pd.read_excel(DATA_XLSX, engine="openpyxl")
    df = normalize_columns(df)

    # make sure folders exist
    for folder in OUTPUT_COLLECTIONS:
        (ROOT / folder).mkdir(exist_ok=True)

    now = datetime.datetime.utcnow().isoformat() + "Z"
    seen = set()
    slug_used = {}

    for i, row in df.iterrows():
        raw_coll = row.get("collection")
        coll = map_collection(raw_coll)
        if not coll:
            print(f"[WARN] Row {i+1}: unknown collection '{raw_coll}'. Skipping.")
            continue

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

        # ensure slug uniqueness
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
            "collection": coll.lstrip("_"),
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
            "permalink": f"/{coll.lstrip('_')}/{slug}/",
            "managed_by": "spreadsheet",
            "last_generated": now,
        }

        order_val = row.get("order")
        try:
            if order_val is not None and str(order_val).strip() != "":
                fm["order"] = int(order_val)
        except:
            pass

        md_path = ROOT / coll / f"{slug}.md"

        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
        content = f"---\n{front}---\n\n{body}\n"

        md_path.write_text(content, encoding="utf-8")
        seen.add(md_path.resolve())

    # deletion pass
    removed = 0
    for coll in OUTPUT_COLLECTIONS:
        for md_path in (ROOT / coll).glob("*.md"):
            if md_path.resolve() not in seen:
                fm = parse_front_matter(md_path)
                if fm.get("managed_by") == "spreadsheet":
                    md_path.unlink()
                    removed += 1

    print(f"[INFO] Generation complete. Files removed: {removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())