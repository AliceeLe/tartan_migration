import re
import csv
import mysql.connector

# --- CONFIG ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "test_wp_2"
}
CSV_PATH = "url_replacements.csv"
OUTPUT_SQL_PATH = "url_update_script.sql"
# ---------------

# Connect to MySQL
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Extract post_content
cursor.execute("SELECT ID, post_content, guid FROM wp_posts WHERE post_content LIKE '%uploads/%' OR guid LIKE '%uploads/%'")
rows = cursor.fetchall()

# Regex pattern for WordPress image URLs
pattern = r"https://the-tartan\.org/wp-content/uploads/[^\s\"']+\.(?:png|jpe?g|gif|webp)"

# Extract all image URLs in a set
found_urls = set()
for _, post_content, guid in rows:
    if post_content:
        matches = re.findall(pattern, post_content)
        found_urls.update(matches)
    if guid:
        matches = re.findall(pattern, guid)
        found_urls.update(matches)

print(f"Extracted {len(found_urls)} unique image URLs from post_content.")
print("Sample URLs:", list(found_urls)[:3])
print("https://the-tartan.org/wp-content/uploads/2025/02/kmyers-dailys_32-3.jpeg" in found_urls)

# Load CSV mappings
mapping = {}
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        mapping[row['old_url'].strip()] = row['new_url'].strip()
print(mapping)
print("https://the-tartan.org/wp-content/uploads/2025/02/kmyers-dailys_32-3.jpeg" in mapping.keys())

# Match & generate update statements
updates = []
for url in found_urls:
    if url in mapping:
        print(url)
        updates.append((
            url,
            mapping[url]
        ))

print(f"Found {len(updates)} matches between content and mapping CSV.")
print(updates)

# Write SQL script to file
with open(OUTPUT_SQL_PATH, "w") as f:
    for old, new in updates:
        f.write(f"""UPDATE wp_posts
SET post_content = REPLACE(post_content, '{old}', '{new}')
WHERE post_content LIKE '%{old}%';\n""")

print(f"✅ SQL script written to: {OUTPUT_SQL_PATH}")
# Check if all old_url entries in the CSV file are in the found_urls set
missing_urls = [url for url in mapping.keys() if url not in found_urls]

if missing_urls:
    print(f"⚠️ {len(missing_urls)} URLs from the CSV file were not found in the extracted URLs.")
    print("Sample missing URLs:", missing_urls[:3])
else:
    print("✅ All URLs from the CSV file were found in the extracted URLs.")