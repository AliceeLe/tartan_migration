import csv
import os
import time
import requests
import subprocess
from urllib.parse import urlparse

# --- CONFIG ---
BUCKET_NAME = "thetartan-assets"
PREFIX = "assets"
CSV_PATH = "db_urls.csv"
TMP_DIR = "tmp_images"  # Temp folder for downloads
# ---------------

def extract_path_parts(url):
    parts = urlparse(url).path.split('/')
    year = parts[3]
    month = parts[4]
    filename = parts[5]
    return year, month, filename

def generate_unique_id():
    return time.strftime("%d%H%M%S")  # e.g., 30141233

# Ensure temp folder exists
os.makedirs(TMP_DIR, exist_ok=True)

output_rows = []

with open(CSV_PATH, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        db_url = row["db_url"].strip()

        try:
            year, month, filename = extract_path_parts(db_url)
        except IndexError:
            print(f"❌ Skipping malformed URL: {db_url}")
            continue

        local_filename = os.path.join(TMP_DIR, filename)

        # Download the image
        try:
            response = requests.get(db_url, timeout=10)
            response.raise_for_status()
            with open(local_filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed to download {db_url}: {e}")
            continue

        unique_id = generate_unique_id()
        s3_key = f"{PREFIX}/{year}/{month}/{unique_id}/{filename}"
        s3_uri = f"s3://{BUCKET_NAME}/{s3_key}"
        public_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        # Upload to S3
        try:
            subprocess.run(["aws", "s3", "cp", local_filename, s3_uri, "--acl", "public-read"], check=True)
            print(f"⬆️ Uploaded to {public_url}")
            output_rows.append({"old_url": db_url, "new_url": public_url})
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload failed for {filename}: {e}")

# Save mapping to new CSV
with open("s3_uploaded_mapping.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["old_url", "new_url"])
    writer.writeheader()
    writer.writerows(output_rows)

print(f"\n✅ Upload complete. Mapping saved to: s3_uploaded_mapping.csv")
