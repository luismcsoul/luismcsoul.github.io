import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheet details
SHEET_ID = "YOUR_SHEET_ID"
RANGE_NAME = "Sheet1"  # adjust if your sheet/tab has a different name

def load_google_sheet():
    # Load credentials from environment secret
    import json, os
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

    # Convert to DataFrame
    df = pd.DataFrame(values[1:], columns=values[0])
    return df
