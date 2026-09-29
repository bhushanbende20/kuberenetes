import requests
import json
import os
from requests.auth import HTTPBasicAuth

# Elasticsearch credentials
username = "data-platform"
password = "$2a$10$bhHwSoSBTc5xNEFYOGzVnuTDvnwWHYdkjHqbFhxc4ffR5VXUlSrHm"

base_url = "https://prod-elasticsearch-dp-search-coord-external.platform.onclusive.org"
index_url = f"{base_url}/broadcast-1-2026.04/_search"
scroll_url = f"{base_url}/_search/scroll"

output_dir = "es_data"
os.makedirs(output_dir, exist_ok=True)

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def write_batch(docs, count):
    """Write batch of documents to JSON file"""
    filename = os.path.join(output_dir, f"data_{count}.json")
    with open(filename, 'w') as f:
        json.dump(docs, f, indent=2)
    print(f"✅ Written {len(docs)} records to {filename}")

print("🚀 Starting Elasticsearch data extraction...")
print(f"📊 Index: broadcast-1-2026.04")
print("=" * 50)

# Initial search request with scroll - scroll as PARAMETER, not in body
scroll_size = 1000
scroll_time = "5m"

print("📡 Fetching first batch...")

# Pass scroll as a query parameter
response = requests.post(
    index_url,
    auth=HTTPBasicAuth(username, password),
    params={"scroll": scroll_time},  # ← KEY FIX: scroll as parameter
    json={"size": scroll_size, "query": {"match_all": {}}},
    headers={'Content-Type': 'application/json'},
    verify=False
)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

data = response.json()
scroll_id = data["_scroll_id"]
total_hits = data["hits"]["total"]["value"]
hits = data["hits"]["hits"]

print(f"📈 Total documents to fetch: {total_hits:,}")
print("💾 Saving data in batches of 100 records...")
print("-" * 50)

all_docs = []
file_count = 1
docs_processed = 0

while hits:
    for hit in hits:
        all_docs.append(hit["_source"])
        docs_processed += 1
        
        # Show progress every 1000 documents
        if docs_processed % 1000 == 0:
            print(f"📥 Processed {docs_processed:,} / {total_hits:,} documents...")
        
        # Write to disk when we have 100 documents
        if len(all_docs) == 100:
            write_batch(all_docs, file_count)
            all_docs = []
            file_count += 1
    
    # Get next batch using scroll
    response = requests.post(
        scroll_url,
        auth=HTTPBasicAuth(username, password),
        params={"scroll": scroll_time},  # ← scroll as parameter again
        json={"scroll_id": scroll_id},
        headers={'Content-Type': 'application/json'},
        verify=False
    )
    
    if response.status_code != 200:
        print(f"⚠️ Scroll error: {response.status_code}")
        print(f"Response: {response.text}")
        break
        
    data = response.json()
    scroll_id = data["_scroll_id"]
    hits = data["hits"]["hits"]

# Write remaining documents
if all_docs:
    write_batch(all_docs, file_count)

# Clear scroll context
print("-" * 50)
try:
    requests.delete(
        scroll_url,
        auth=HTTPBasicAuth(username, password),
        json={"scroll_id": scroll_id},
        headers={'Content-Type': 'application/json'},
        verify=False
    )s
    print("🧹 Scroll context cleared")
except Exception as e:
    print(f"Note: {e}")

print("=" * 50)
print(f"✅ Extraction complete!")
print(f"📁 Total documents saved: {docs_processed:,}")
print(f"📄 Total files created: {file_count}")
print(f"💾 Data saved in: {output_dir}/")