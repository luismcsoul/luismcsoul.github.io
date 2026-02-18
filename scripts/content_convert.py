import pandas as pd
import os
import yaml
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheet details
SHEET_ID = "1nd1otXiR_JZnASjUnuKw4ASpGSCVbcU5q4l5keeRPds"
RANGE_NAME = "Sheet1"

# Output Excel snapshot
OUTPUT_EXCEL = "data/luismcsoul_content_updated.xlsx"

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
    """Normalize values: replace NaN/.nan/empty with None (YAML null)."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ["nan", ".nan"]:
        return None
    return val

def load_google_sheet():
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    if not values:
        raise ValueError("No data found in Google Sheet.")
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def safe_yaml_load(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().split("---")
        if len(lines) >= 3:
            front_matter = yaml.safe_load(lines[1])
            body = "---".join(lines[2:])
            return front_matter or {}, body
        else:
            return {}, f.read()

def write_yaml_file(filepath, front_matter, body):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        f.write(body.strip() + "\n")

def update_content():
    df = load_google_sheet()
    updated_rows = []

    for _, row in df.iterrows():
        collection = clean_value(row.get("collection")) or "misc"
        slug = clean_value(row.get("slug"))
        permalink = clean_value(row.get("permalink"))
        media_hero = clean_value(row.get("media_hero"))

        if not slug:
            continue

        content_dir = COLLECTION_DIRS.get(collection.lower(), "_misc")
        os.makedirs(content_dir, exist_ok=True)
        filename = os.path.join(content_dir, f"{slug}.md")

        if os.path.exists(filename):
            front_matter, body = safe_yaml_load(filename)
            fields_to_check = [
                "layout", "title", "slug", "permalink", "schema_type",
                "excerpt", "keywords", "media_hero", "media_alt",
                "taglines", "references", "album", "citation"
            ]
            for field in fields_to_check:
                sheet_value = clean_value(row.get(field))
                if sheet_value is not None:
                    front_matter[field] = sheet_value
            if not body.strip() and clean_value(row.get("body_md")):
                body = row.get("body_md", "")
            write_yaml_file(filename, front_matter, body)
            print(f"Updated {filename}")
        else:
            front_matter = {
                "layout": clean_value(row.get("collection")) or "work",
                "title": clean_value(row.get("title")),
                "slug": slug,
                "permalink": permalink,
                "schema_type": clean_value(row.get("schema_type")) or "CreativeWork",
                "excerpt": clean_value(row.get("excerpt")),
                "keywords": clean_value(row.get("keywords")),
                "media_hero": media_hero,
                "media_alt": clean_value(row.get("media_alt")),
                "taglines": clean_value(row.get("taglines")),
                "references": clean_value(row.get("references")),
                "album": clean_value(row.get("album")),
                "citation": clean_value(row.get("citation"))
            }
            body = clean_value(row.get("body_md")) or ""
            write_yaml_file(filename, front_matter, body)
            print(f"Created {filename}")

        updated_rows.append(row)

    pd.DataFrame(updated_rows).to_excel(OUTPUT_EXCEL, index=False)
    print(f"Saved updated snapshot to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    update_content()
