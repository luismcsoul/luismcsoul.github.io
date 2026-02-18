import pandas as pd
import os
import yaml
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ... (Keep your SHEET_ID and RANGE_NAME same)

# Add your colors file if you want to pull defaults from assets/colors.yml
# COLORS_FILE = "assets/colors.yml"

# Map collection names to directories
COLLECTION_DIRS = {
    "taglines": "_taglines",
    "visualartwork": "_visualartwork",
    "personal-micro-dictionary": "_personal-micro-dictionary",
    "written-photography": "_written-photography",
    "epistolary": "_epistolary",
    "sculpture": "_sculpture",
    "songs": "_songs",
    "article": "_article",
    "capsule-review": "_capsule-review",
    "photograph": "_photograph",
    "misc": "_misc"
}

def clean_value(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ["nan", ".nan"]:
        return None
    return val

# ... (Keep load_google_sheet, safe_yaml_load, and write_yaml_file same)

def update_content():
    df = load_google_sheet()
    updated_rows = []

    # fields_to_check expanded to include color logic
    fields_to_check = [
        "layout", "title", "slug", "permalink", "schema_type",
        "excerpt", "keywords", "media_hero", "media_alt",
        "taglines", "references", "album", "citation",
        "base_color", "light_color"  # <--- CRITICAL: Added color fields
    ]

    for _, row in df.iterrows():
        collection = clean_value(row.get("collection")) or "misc"
        slug = clean_value(row.get("slug"))
        
        if not slug:
            continue

        content_dir = COLLECTION_DIRS.get(collection.lower(), "_misc")
        os.makedirs(content_dir, exist_ok=True)
        filename = os.path.join(content_dir, f"{slug}.md")

        if os.path.exists(filename):
            front_matter, body = safe_yaml_load(filename)
            for field in fields_to_check:
                sheet_value = clean_value(row.get(field))
                if sheet_value is not None:
                    front_matter[field] = sheet_value
            
            if not body.strip() and clean_value(row.get("body_md")):
                body = row.get("body_md", "")
            
            write_yaml_file(filename, front_matter, body)
            print(f"Updated {filename}")
        else:
            # Logic for brand new files
            front_matter = {
                "layout": clean_value(row.get("collection")) or "work",
                "title": clean_value(row.get("title")),
                "slug": slug,
                "permalink": clean_value(row.get("permalink")),
                "schema_type": clean_value(row.get("schema_type")) or "CreativeWork",
                "base_color": clean_value(row.get("base_color")) or "#f0f0f0", # Fallback
                "light_color": clean_value(row.get("light_color")) or "#ffffff", # Fallback
                "media_hero": clean_value(row.get("media_hero")),
                # ... add other fields as needed
            }
            body = clean_value(row.get("body_md")) or ""
            write_yaml_file(filename, front_matter, body)
            print(f"Created {filename}")

        updated_rows.append(row)

    pd.DataFrame(updated_rows).to_excel(OUTPUT_EXCEL, index=False)
    print(f"Saved updated snapshot to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    update_content()
