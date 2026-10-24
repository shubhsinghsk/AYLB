"""Authorize the AYLB app to send mail through Gmail's HTTPS API.

Run locally with a downloaded Google OAuth Desktop client JSON file. The script
prints secrets to the terminal; copy them directly into Render and do not share
or commit the output.
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/get_gmail_refresh_token.py /path/to/oauth-client.json")

    client_file = Path(sys.argv[1]).expanduser()
    if not client_file.is_file():
        raise SystemExit(f"OAuth client file not found: {client_file}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    client_config = json.loads(client_file.read_text(encoding="utf-8"))
    client = client_config.get("installed") or client_config.get("web") or {}
    if not credentials.refresh_token:
        raise SystemExit("Google did not return a refresh token. Revoke prior access and run this again.")

    print("\nCopy these values into Render Environment settings. Treat all three as secrets:\n")
    print(f"GMAIL_API_CLIENT_ID={client['client_id']}")
    print(f"GMAIL_API_CLIENT_SECRET={client['client_secret']}")
    print(f"GMAIL_API_REFRESH_TOKEN={credentials.refresh_token}")


if __name__ == "__main__":
    main()
