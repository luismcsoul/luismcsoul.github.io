import pandas as pd
import os
import yaml
import json
import colorsys
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
SHEET_ID = "1nd1otXiR_JZnASjUnuKw4ASpGSCVbcU5q4l5keeRPds"
RANGE_NAME = "Sheet1"
OUTPUT_EXCEL = "data/luismcsoul_content_updated.xlsx"

COLLECTION_HUES = {
    "written-photography": 200, "sculpture": 25, "songs": 280,
    "taglines": 190, "visualartwork": 45, "article": 0,
    "capsule-review": 150, "epistolary": 330,
    "personal-micro-dictionary": 220, "photograph": 100
}

def clean_value(val):
    if val is None: return None
    s = str(val).strip()
    return None if s == "" or s.lower() in ["nan", ".nan"] else val

def load_google_sheet():
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json: raise ValueError("Credentials secret not found.")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    if not values: raise ValueError("No data found in Sheet.")
    return pd.DataFrame(values[1:], columns=values[0])

def safe_yaml_load(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        parts = f.read().split("---")
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}, "---".join(parts[2:])
        return {}, f.read()

def write_yaml_file(filepath, front_matter, body):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        f.write(body.strip() + "\n")

def update_content():
    df = load_google_sheet()
    df['col_clean'] = df['collection'].apply(lambda x: str(x).strip().lower() if x else "misc")
    
    for col_name, group in df.groupby('col_clean'):
        items = group.to_dict('records')
        total = len(items)
        base_hue = COLLECTION_HUES.get(col_name, 200)

        for index, row in enumerate(items):
            slug = clean_value(row.get("slug"))
            if not slug: continue

            # Distribute Lightness
            l_val = 35 + (40 * (index / (total - 1 if total > 1 else 1)))
            b_color = f"hsl({base_hue}, 55%, {int(l_val)}%)"
            l_color = f"hsl({base_hue}, 40%, 95%)"

            content_dir = f"_{col_name}"
            os.makedirs(content_dir, exist_ok=True)
            filename = os.path.join(content_dir, f"{slug}.md")

            fm, body = safe_yaml_load(filename) if os.path.exists(filename) else ({}, clean_value(row.get("body_md")) or "")
            
            fields = ["title", "permalink", "schema_type", "excerpt", "media_hero", "media_alt"]
            for f in fields:
                val = clean_value(row.get(f))
                if val: fm[f] = val

            fm["base_color"] = b_color
            fm["light_color"] = l_color
            if "layout" not in fm: fm["layout"] = "work"

            write_yaml_file(filename, fm, body)

if __name__ == "__main__":
    update_content()
