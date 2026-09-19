"""
Download podcast transcripts from the public Lenny's Newsletter repository.
Source: https://github.com/LennysNewsletter/lennys-newsletterpodcastdata
"""

import os
import json
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download_transcripts")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GITHUB_API_PODCASTS = "https://api.github.com/repos/LennysNewsletter/lennys-newsletterpodcastdata/contents/podcasts"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/LennysNewsletter/lennys-newsletterpodcastdata/main/podcasts"
GITHUB_INDEX_URL = "https://raw.githubusercontent.com/LennysNewsletter/lennys-newsletterpodcastdata/main/index.json"

def fetch_url(url: str, timeout: int = 15) -> bytes:
    headers = {"User-Agent": "LennyGrowthAssistant/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def download_index():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index_file = DATA_DIR / "index.json"
    if not index_file.exists():
        logger.info("Downloading dataset index.json...")
        try:
            content = fetch_url(GITHUB_INDEX_URL)
            with open(index_file, "wb") as f:
                f.write(content)
            logger.info("Saved index.json")
        except Exception as e:
            logger.warning(f"Failed to download index.json: {e}")
    else:
        logger.info("index.json already exists, skipping.")

def download_all_transcripts(max_episodes: int = 50):
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    download_index()

    logger.info("Querying GitHub repository for podcast transcript files...")
    try:
        data = fetch_url(GITHUB_API_PODCASTS)
        files = json.loads(data.decode("utf-8"))
    except Exception as e:
        logger.error(f"Error fetching directory list from GitHub: {e}")
        return

    md_files = [f for f in files if f.get("name", "").endswith(".md")]
    logger.info(f"Found {len(md_files)} podcast transcript files in repository.")

    downloaded = 0
    for idx, item in enumerate(md_files[:max_episodes]):
        file_name = item["name"]
        target_path = TRANSCRIPTS_DIR / file_name

        if target_path.exists() and target_path.stat().st_size > 500:
            logger.debug(f"[{idx+1}/{len(md_files)}] Already downloaded: {file_name}")
            downloaded += 1
            continue

        download_url = item.get("download_url") or f"{GITHUB_RAW_BASE}/{file_name}"
        logger.info(f"[{idx+1}/{len(md_files)}] Downloading: {file_name}")
        try:
            content = fetch_url(download_url)
            with open(target_path, "wb") as f:
                f.write(content)
            downloaded += 1
        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")

    logger.info(f"Completed! Total transcripts available locally: {downloaded}")

if __name__ == "__main__":
    download_all_transcripts()
