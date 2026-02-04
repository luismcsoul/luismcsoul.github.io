import pandas as pd
import os
import yaml
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheet details
SHEET_ID = "YOUR_SHEET_ID"   # <-- replace with your actual Sheet ID
RANGE_NAME = "Sheet1"        # adjust if your sheet/tab has a different name

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

def load_google_sheet():
    """Fetch Google Sheet data into a pandas DataFrame."""
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
    """Load YAML front matter from a markdown file safely."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().split("---")
        if len(lines) >= 3:
            front_matter = yaml.safe_load(lines[1])
            body = "---".join(lines[2:])
            return front_matter or {}, body
        else:
            return {}, f.read()

def write_yaml_file(filepath, front_matter, body):
    """Write updated YAML + body back to file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        f.write(body.strip() + "\n")

def update_content():
    df = load_google_sheet()
    updated_rows = []

    for _, row in df.iterrows():
        collection = str(row.get("collection", "misc")).strip().lower()
        slug = str(row.get("slug", "")).strip()
        permalink = row.get("permalink", "")
        media_hero = row.get("media_hero", None)

        if not slug:
            continue  # skip rows without slug

        # Pick directory based on collection
        content_dir = COLLECTION_DIRS.get(collection, "_misc")
        os.makedirs(content_dir, exist_ok=True)

        filename = os.path.join(content_dir, f"{slug}.md")

        if os.path.exists(filename):
            front_matter, body = safe_yaml_load(filename)

            # Update only empty fields
            if ("media_hero" not in front_matter or not front_matter["media_hero"]) and media_hero:
                front_matter["media_hero"] = media_hero

            # Preserve existing values or fill from sheet if missing
            front_matter["title"] = front_matter.get("title", row.get("title", ""))
            front_matter["slug"] = front_matter.get("slug", slug)
            front_matter["permalink"] = front_matter.get("permalink", permalink)

            write_yaml_file(filename, front_matter, body)
            print(f"Updated {filename}")
        else:
            # Create new file if missing
            front_matter = {
                "layout": row.get("collection", "work"),
                "title": row.get("title", ""),
                "slug": slug,
                "permalink": permalink,
                "schema_type": row.get("schema_type", "CreativeWork"),
                "excerpt": row.get("excerpt", ""),
                "keywords": row.get("keywords", ""),
                "media_hero": media_hero,
                "media_alt": row.get("media_alt", ""),
                "taglines": row.get("taglines", ""),
                "references": row.get("references", ""),
                "album": row.get("album", "")
            }
            body = row.get("body_md", "")
            write_yaml_file(filename, front_matter, body)
            print(f"Created {filename}")

        updated_rows.append(row)

    # Save updated Excel snapshot
    pd.DataFrame(updated_rows).to_excel(OUTPUT_EXCEL, index=False)
    print(f"Saved updated snapshot to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    update_content()
