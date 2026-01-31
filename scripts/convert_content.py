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

# Sub-folder logic for series (poetry) and albums (songs)
sub = ""
# Support both 'poetry' (recommended) and legacy 'pmd' for your poetry rows
if collection in ("poetry", "pmd") and row.get("series"):
    sub = slugify(row.get("series"))
elif collection == "songs" and row.get("album"):
    sub = slugify(row.get("album"))

# Final folder path (with sub-folder if present)
folder = os.path.join(ROOT, collection, sub) if sub else os.path.join(ROOT, collection)
os.makedirs(folder, exist_ok=True)

# Final filename
fname = os.path.join(folder, f"{slug}.md")

    # Core fields
    date = (row.get("date") or "").strip()
    excerpt = (row.get("excerpt") or "").strip()
    body_md = row.get("body_md") or ""
    order = row.get("order") or ""
    schema_type = (row.get("schema_type") or "").strip()
    media_hero = (row.get("media_hero") or "").strip()
    media_alt = (row.get("media_alt") or "").strip()
    context_project = (row.get("context_project") or "").strip()
    context_philosophy = (row.get("context_philosophy") or "").strip()
    references = parse_csv_list(row.get("references"))
    keywords = parse_csv_list(row.get("keywords"))
    edge_left  = (row.get("edge_left")  or "").strip()
    edge_right = (row.get("edge_right") or "").strip()
    edge_top   = (row.get("edge_top")   or "").strip()
    edge_bottom= (row.get("edge_bottom")or "").strip()
    published  = to_bool(row.get("published"), default=True)

    # Build front matter
    fm = []
    fm.append("---")
    fm.append(f'title: "{title.replace(\'"\', "\'")}"')
    fm.append(f"layout: work")
    if schema_type: fm.append(f'schema_type: "{schema_type}"')
    if date:        fm.append(f"date: {date}")
    if excerpt:     fm.append(f'excerpt: "{excerpt.replace(\'"\', "\'")}"')
    if order != "": fm.append(f"order: {int(order)}")
    if not published: fm.append("published: false")

    # context
    if context_project or context_philosophy:
        fm.append("context:")
        if context_project:   fm.append(f"  project: {context_project}")
        if context_philosophy:fm.append(f"  philosophy: {context_philosophy}")

    # media
    if media_hero or media_alt:
        fm.append("media:")
        if media_hero: fm.append(f"  hero: {media_hero}")
        if media_alt:  fm.append(f"  alt: \"{media_alt.replace('\"','\\'')}\"")

    # references
    if references:
        fm.append("references:")
        for r in references:
            fm.append(f"  - ref: {r}")

    # keywords
    if keywords:
        fm.append("keywords:")
        for k in keywords:
            fm.append(f"  - {k}")

    # per-page edge overrides (optional)
    if any([edge_left, edge_right, edge_top, edge_bottom]):
        fm.append("edges:")
        if edge_left:   fm.append(f"  left: {edge_left}")
        if edge_right:  fm.append(f"  right: {edge_right}")
        if edge_top:    fm.append(f"  top: {edge_top}")
        if edge_bottom: fm.append(f"  bottom: {edge_bottom}")

    fm.append("---")

    # Write file
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(fm))
        f.write("\n\n")
        f.write(body_md.strip())
        f.write("\n")

    print("Wrote:", os.path.relpath(fname, ROOT))

def main():
    rows = read_rows()
    if not rows:
        print("No rows found in /data/content.xlsx or /data/content.csv")
        sys.exit(0)

    for row in rows:
        write_page(row)

if __name__ == "__main__":
    main()
