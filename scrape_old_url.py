import re
import csv
import mysql.connector

# --- CONFIG ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # <-- replace this
    "database": "test_wp_2"
}
OUTPUT_CSV = "db_urls.csv"
# ---------------

# Connect to DB
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute("""
    SELECT guid, post_content
    FROM wp_posts
    WHERE guid LIKE '%uploads%' OR post_content LIKE '%uploads%'
""")
rows = cursor.fetchall()

# Regex for WordPress image URLs
pattern = r"https://the-tartan\.org/wp-content/uploads/[^\s\"']+\.(?:png|jpe?g|gif|webp)"

found_urls = set()

for guid, content in rows:
    if guid:
        found_urls.update(re.findall(pattern, guid))
    if content:
        found_urls.update(re.findall(pattern, content))

print(f"✅ Found {len(found_urls)} unique image URLs in the database.")

# Write to CSV
with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["db_url"])
    for url in sorted(found_urls):
        writer.writerow([url])

print(f"✅ Extracted URLs written to: {OUTPUT_CSV}")
