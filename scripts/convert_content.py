import os, sys, re, csv
from datetime import datetime

# ---------- Config ----------
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_XLSX = os.path.join(ROOT, "data", "content.xlsx")
DATA_CSV  = os.path.join(ROOT, "data", "content.csv")

# Which collections are allowed & the order used for the GLOBAL ring
COLLECTIONS_ALLOWED = ["poetry","songs","image-text","sculpture","theory","pmd"]  # keep 'pmd' for backward-compat
COLLECTION_ORDER    = ["poetry","songs","image-text","sculpture","theory","pmd"]  # pmd (legacy) goes last by default

# ---------- IO ----------
def read_rows():
    """
    Reads XLSX if possible, otherwise CSV (UTF-8).
    Returns a list[dict].
    """
    rows = []
    if os.path.exists(DATA_XLSX):
        try:
            import pandas as pd
            df = pd.read_excel(DATA_XLSX, engine="openpyxl")
            return df.to_dict(orient="records")
        except Exception as e:
            print("Falling back to CSV because XLSX read failed:", e, file=sys.stderr)
    if os.path.exists(DATA_CSV):
        with open(DATA_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    return rows

# ---------- Utils ----------
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

def safe_yaml_single(s):
    """Return YAML-safe single-quoted string (escape single quotes by doubling)."""
    return (s or "").replace("'", "''")

# ---------- Normalization of path intent ----------
def normalize_path_from_row(row):
    """
    Decide collection + subpath from row, in this priority:
      1) content_path (e.g., 'poetry/personal-micro-dictionary', 'songs/animal/guitar-chords')
      2) subpath       (used under the selected collection)
      3) series/album  (legacy convenience)
    Returns (collection, subpath) where subpath may be ''.
    """
    # 1) content_path
    cp = (row.get("content_path") or "").strip().strip("/")
    if cp:
        parts = [slugify(p) for p in cp.split("/") if p.strip() and p.strip() != "." and p.strip() != ".."]
        if not parts:
            return None, ""
        collection = parts[0]
        subpath = "/".join(parts[1:]) if len(parts) > 1 else ""
        return collection, subpath

    # 2) subpath
    collection = (row.get("collection") or "").strip()
    subpath = (row.get("subpath") or "").strip()
    if subpath:
        return collection, "/".join(slugify(p) for p in subpath.split("/") if p.strip())

    # 3) series/album
    if collection in ("poetry","pmd"):
        series = (row.get("series") or "").strip()
        if series:
            return collection, slugify(series)
    if collection == "songs":
        album = (row.get("album") or "").strip()
        if album:
            return collection, slugify(album)

    return collection, ""

# ---------- Pass 1: enrich rows ----------
def enrich_rows(rows):
    """
    Produce normalized records with:
      - collection, subpath, title, slug
      - url_path (expected URL path based on /:collection/:path/)
      - order (int or large sentinel)
      - keys for grouping (local ring key = (collection, subpath))
    """
    enriched = []
    for row in rows:
        collection_raw = (row.get("collection") or "").strip()
        collection, subpath = normalize_path_from_row(row)

        collection = (collection or "").strip()
        if collection not in COLLECTIONS_ALLOWED:
            print(f"Skipping row with invalid collection: {collection}  (title={row.get('title')})")
            continue

        title = (row.get("title") or "").strip()
        if not title:
            print("Skipping row without title")
            continue

        slug = (row.get("slug") or "").strip() or slugify(title)

        # compute folder path for writing
        folder = os.path.join(ROOT, collection, subpath) if subpath else os.path.join(ROOT, collection)
        os.makedirs(folder, exist_ok=True)
        fname = os.path.join(folder, f"{slug}.md")

        # expected URL path (matches permalink /<collection>/:path/)
        if subpath:
            url_path = f"/{collection}/{subpath}/{slug}/"
        else:
            url_path = f"/{collection}/{slug}/"

        # sorting key within subpath: numeric order then title
        try:
            order_val = int(row.get("order")) if str(row.get("order")).strip() != "" else 10**9
        except Exception:
            order_val = 10**9

        rec = {
            "row": row,
            "collection": collection,
            "subpath": subpath,
            "title": title,
            "slug": slug,
            "folder": folder,
            "fname": fname,
            "url_path": url_path,
            "order_val": order_val,
            "gkey": f"{collection}::{subpath}",   # local ring key
        }
        enriched.append(rec)
    return enriched

# ---------- Build rings (prev/next) ----------
def build_rings(enriched):
    """
    Compute three rings:
      - local ring: items grouped by (collection, subpath)
      - collection ring: all items in same collection (by subpath then order)
      - global ring: COLLECTION_ORDER across collections

    Returns dict: key=url_path -> dict(prev/next at each level)
    """
    index = { rec["url_path"]: rec for rec in enriched }

    # local rings
    groups = {}
    for rec in enriched:
        groups.setdefault(rec["gkey"], []).append(rec)
    for key in groups:
        groups[key].sort(key=lambda r: (r["order_val"], r["title"].lower(), r["slug"]))

    # collection rings
    per_collection = {}
    for rec in enriched:
        per_collection.setdefault(rec["collection"], []).append(rec)
    for coll in per_collection:
        per_collection[coll].sort(key=lambda r: (r["subpath"], r["order_val"], r["title"].lower(), r["slug"]))

    # global ring (respect collection ordering)
    global_list = []
    for coll in COLLECTION_ORDER:
        global_list.extend(per_collection.get(coll, []))
    # plus any collections not in order list
    for coll in per_collection:
        if coll not in COLLECTION_ORDER:
            global_list.extend(per_collection[coll])

    nav = {}
    # helper to set ring prev/next circularly
    def ring_links(lst, label):
        n = len(lst)
        if n == 0: return
        for i, rec in enumerate(lst):
            prev_rec = lst[(i-1) % n]
            next_rec = lst[(i+1) % n]
            entry = nav.setdefault(rec["url_path"], {})
            entry[f"{label}_prev"] = prev_rec["url_path"]
            entry[f"{label}_next"] = next_rec["url_path"]

    # apply
    for key, lst in groups.items():
        ring_links(lst, "local")
    for coll, lst in per_collection.items():
        ring_links(lst, "collection")
    ring_links(global_list, "global")

    return nav

# ---------- Write a page ----------
def write_page(rec, nav_map):
    row          = rec["row"]
    collection   = rec["collection"]
    title        = rec["title"]
    slug         = rec["slug"]
    folder       = rec["folder"]
    fname        = rec["fname"]
    url_path     = rec["url_path"]
    subpath      = rec["subpath"]

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

    # Front matter
    fm = []
    fm.append("---")
    fm.append(f"title: '{safe_yaml_single(title)}'")
    fm.append("layout: work")
    if schema_type: fm.append(f'schema_type: "{schema_type}"')
    if date:        fm.append(f"date: {date}")
    if excerpt:     fm.append(f"excerpt: '{safe_yaml_single(excerpt)}'")
    if order != "": fm.append(f"order: {int(order)}")
    if not published: fm.append("published: false")

    # keep resolved mapping for debugging / future use
    fm.append(f"collection: {collection}")
    if subpath: fm.append(f"subpath: {subpath}")

    # context
    if context_project or context_philosophy:
        fm.append("context:")
        if context_project:    fm.append(f"  project: {context_project}")
        if context_philosophy: fm.append(f"  philosophy: {context_philosophy}")

    # media
    if media_hero or media_alt:
        fm.append("media:")
        if media_hero: fm.append(f"  hero: {media_hero}")
        if media_alt:  fm.append(f"  alt: '{safe_yaml_single(media_alt)}'")

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

    # rings written as 'nav' (used by edge include)
    n = nav_map.get(url_path, {})
    if n:
        fm.append("nav:")
        for k in ("local_prev","local_next","collection_prev","collection_next","global_prev","global_next"):
            if n.get(k):
                fm.append(f"  {k}: {n[k]}")

    fm.append("---")

    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(fm))
        f.write("\n\n")
        f.write(body_md.strip())
        f.write("\n")

    print("Wrote:", os.path.relpath(fname, ROOT))

# ---------- Main ----------
def main():
    rows = read_rows()
    if not rows:
        print("No rows found in /data/content.xlsx or /data/content.csv")
        sys.exit(0)

    # First enrich and compute rings
    enriched = enrich_rows(rows)
    nav_map  = build_rings(enriched)

    # Then write all files with ring data
    for rec in enriched:
        write_page(rec, nav_map)

if __name__ == "__main__":
    main()
