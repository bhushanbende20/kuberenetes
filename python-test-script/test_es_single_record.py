import json
import os
import sys

import requests
import urllib3
from requests.auth import HTTPBasicAuth


BASE_URL = os.getenv(
    "ES_BASE_URL",
    "https://prod-elasticsearch-dp-search-coord-external.platform.onclusive.org",
)
INDEX = os.getenv("ES_INDEX", "broadcast-1-2026.04")
VERIFY_TLS = os.getenv("ES_VERIFY_TLS", "false").lower() in {"1", "true", "yes"}


def main():
    username = "data-platform" 
    password = "$2a$10$bhHwSoSBTc5xNEFYOGzVnuTDvnwWHYdkjHqbFhxc4ffR5VXUlSrHm"
    if not username or not password:
        print("Set ES_USERNAME and ES_PASSWORD before running this script.", file=sys.stderr)
        return 2

    if not VERIFY_TLS:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)`passenger_count`

    search_url = f"{BASE_URL.rstrip('/')}/{INDEX}/_search"
    try:
        response = requests.post(
            search_url,
            auth=HTTPBasicAuth(username, password),
            json={"size": 1, "query": {"match_all": {}}},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=VERIFY_TLS,
        )
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
    except requests.RequestException as error:
        print(f"Elasticsearch request failed: {error}", file=sys.stderr)
        if error.response is not None:
            print(error.response.text, file=sys.stderr)
        return 1

    if not hits:
        print(f"No records found in index {INDEX}.")
        return 0

    print(json.dumps(hits[0], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())