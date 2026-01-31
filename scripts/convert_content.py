import os, sys, re, csv
from datetime import datetime

# Config
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_XLSX = os.path.join(ROOT, "data", "content.xlsx")
DATA_CSV  = os.path.join(ROOT, "data", "content.csv")

# Try pandas if available (xlsx), else fallback to csv
def read_rows():
    rows = []
    if os.path.exists(DATA_XLSX):
        try:
            import pandas as pd
            df = pd.read_excel(DATA_XLSX, engine="openpyxl")
            rows = df.to_dict(orient="records")
            return rows
        except Exception as e:
            print("Falling back to CSV because XLSX read failed:", e, file=sys.stderr)
    if os.path.exists(DATA_CSV):
        with open(DATA_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    return rows

def slugify(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[–—/:]+", "-", s)
    s = re.sub(r"[^a-z0-9- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "untitled"

def to_bool(v, default=True):
    if v is None or v == "":
        return default
    sv = str(v).strip().lower()
    return sv in ("1","true","yes","y","on")

def parse_csv_list(v):
    if not v: return []
    return [x.strip() for x in str(v).split(",") if x.strip()]


def write_page(row):
    collection = (row.get("collection") or "").strip()
    if collection not in ("poetry","pmd","songs","sculpture","image-text","theory"):
        print(f"Skipping row with invalid collection: {collection}")
        return

    title = (row.get("title") or "").strip()
    if not title:
        print("Skipping row without title")
        return

    slug = (row.get("slug") or "").strip() or slugify(title)

    # ---- Sub-folder logic for series/albums ----
    sub = ""
    if collection in ("poetry", "pmd") and row.get("series"):
        sub = slugify(row.get("series"))
    elif collection == "songs" and row.get("album"):
        sub = slugify(row.get("album"))

    folder = os.path.join(ROOT, collection, sub) if sub else os.path.join(ROOT, collection)
    os.makedirs(folder, exist_ok=True)
    fname = os.path.join(folder, f"{slug}.md")
    # --------------------------------------------

    # Core fields
    date = (row.get("date") or "").strip()
    excerpt = (row.get("excerpt") or "").strip()
    body_md = row.get("body_md") or ""
    order = row.get("order") or ""
    schema_type = (row.get("schema_type") or "").strip()
    media_hero = (row.get("media_hero") or "").strip()
    media_alt  = (row.get("media_alt")  or "").strip()
    context_project    = (row.get("context_project")    or "").strip()
    context_philosophy = (row.get("context_philosophy") or "").strip()
    references = parse_csv_list(row.get("references"))
    keywords   = parse_csv_list(row.get("keywords"))
    edge_left   = (row.get("edge_left")   or "").strip()
    edge_right  = (row.get("edge_right")  or "").strip()
    edge_top    = (row.get("edge_top")    or "").strip()
    edge_bottom = (row.get("edge_bottom") or "").strip()
    published  = to_bool(row.get("published"), default=True)

    
# Build front matter
fm = []
# Safer quote strategy: YAML single quotes
safe_title = (title or "").replace("'", "''")
fm.append(f"title: '{safe_title}'")
fm.append("layout: work")
if schema_type: fm.append(f'schema_type: "{schema_type}"')
if date:        fm.append(f"date: {date}")

if excerpt:
    safe_excerpt = excerpt.replace("'", "''")
    fm.append(f"excerpt: '{safe_excerpt}'")

if order != "": fm.append(f"order: {int(order)}")
if not published: fm.append("published: false")

# media
if media_hero or media_alt:
    fm.append("media:")
    if media_hero: fm.append(f"  hero: {media_hero}")
    if media_alt:
        safe_alt = media_alt.replace("'", "''")
        fm.append(f"  alt: '{safe_alt}'")
