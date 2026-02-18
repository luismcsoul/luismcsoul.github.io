import pandas as pd
import os
import yaml
import json
import colorsys
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheet details
SHEET_ID = "1nd1otXiR_JZnASjUnuKw4ASpGSCVbcU5q4l5keeRPds"
RANGE_NAME = "Sheet1"
OUTPUT_EXCEL = "data/luismcsoul_content_updated.xlsx"

# Map collections to their Base Hue (0-360)
# This creates a "Chromatic System" for your IP
COLLECTION_HUES = {
    "written-photography": 200,      # Calm Blue
    "sculpture": 25,                 # Terracotta/Clay
    "songs": 280,                    # Deep Purple
    "taglines": 190,                 # Cyan/Electric
    "visualartwork": 45,             # Golden/Ochre
    "article": 0,                    # Neutral/Red
    "capsule-review": 150,           # Mint/Fresh
    "epistolary": 330,               # Rose/Vintage
    "personal-micro-dictionary": 220, # Ink Blue
    "photograph": 100                # Natural Green
}

def get_distributed_colors(index, total_items, base_hue):
    """Generates a unique lightness/saturation pair for an item."""
    if total_items <= 1:
        return f"hsl({base_hue}, 60%, 50%)", f"hsl({base_hue}, 40%, 95%)"
    
    # We spread lightness between 35% and 75% so text remains legible
    # and the 'museum' vibe stays consistent.
    lightness_step = 40 / (total_items - 1)
    current_lightness = 35 + (index * lightness_step)
    
    base_color = f"hsl({base_hue}, 55%, {current_lightness}%)"
    light_color = f"hsl({base_hue}, 40%, 95%)" # Background gradient end
    return base_color, light_color

def clean_value(val):
    if val is None: return None
    s = str(val).strip()
    if s == "" or s.lower() in ["nan", ".nan"]: return None
    return val

# ... [Keep load_google_sheet, safe_yaml_load, and write_yaml_file logic from previous versions] ...

def update_content():
    df = load_google_sheet()
    # Normalize collection names for grouping
    df['col_clean'] = df['collection'].apply(lambda x: str(x).strip().lower())
    
    updated_rows = []

    # Process by collection to handle color distribution
    for col_name, group in df.groupby('col_clean'):
        items = group.to_dict('records')
        total = len(items)
        base_hue = COLLECTION_HUES.get(col_name, 200) # Fallback to blue

        for index, row in enumerate(items):
            slug = clean_value(row.get("slug"))
            if not slug: continue

            # Calculate the unique hue/lightness for this asset
            b_color, l_color = get_distributed_colors(index, total, base_hue)

            content_dir = f"_{col_name}"
            os.makedirs(content_dir, exist_ok=True)
            filename = os.path.join(content_dir, f"{slug}.md")

            # Front-matter Assembly
            if os.path.exists(filename):
                front_matter, body = safe_yaml_load(filename)
            else:
                front_matter = {}
                body = clean_value(row.get("body_md")) or ""

            # Update standard fields from Sheet
            fields_to_sync = [
                "title", "permalink", "schema_type", "excerpt", 
                "keywords", "media_hero", "media_alt", "citation"
            ]
            for field in fields_to_sync:
                val = clean_value(row.get(field))
                if val: front_matter[field] = val

            # Inject the Systemic Colors
            front_matter["base_color"] = b_color
            front_matter["light_color"] = l_color
            
            write_yaml_file(filename, front_matter, body)
            print(f"Synced [{col_name}] {slug} with color {b_color}")

    pd.DataFrame(df).to_excel(OUTPUT_EXCEL, index=False)

if __name__ == "__main__":
    update_content()
