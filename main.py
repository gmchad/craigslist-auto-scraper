import requests
from bs4 import BeautifulSoup
import re
import os
import time
import json
import logging
import random

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ======================
# Configuration
# ======================
SUBDOMAINS = [
    "losangeles",
    # "orangecounty",
    # "inlandempire",
    # "sandiego"
]

# Base URL pattern for used cars by owner category: /d/cars-trucks-by-owner/search/cto
CATEGORY_PATH = "d/cars-trucks-by-owner/search/cto"

# Keywords to detect trade-friendly listings
INCLUDE_TERMS = ["trade", "swap", "open to trading"]
EXCLUDE_TERMS = ["no trade", "no trades", "no swap", "not open to trading"]

# Delay between requests (in seconds)
CRAWL_DELAY = 1

# Maximum pages per subdomain to prevent infinite scraping (adjust as needed)
MAX_PAGES = 1

# Directory to save images
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Output file for final listings data
OUTPUT_JSON = "listings.json"

# User-Agent rotation (a small set to reduce being flagged as bot)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    }

# ======================
# Utility Functions
# ======================

def fetch_page(url):
    """Fetch a page with retries."""
    for attempt in range(3):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Non-200 status {response.status_code} for URL: {url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Exception fetching {url}: {e}")
        time.sleep(CRAWL_DELAY * (attempt + 1))
    return None

def contains_trade_terms(text):
    """Check if the text includes positive trade terms and does not include exclude terms."""
    text_lower = text.lower()
    # Check include terms
    if not any(term in text_lower for term in INCLUDE_TERMS):
        return False
    # Check exclude terms
    if any(term in text_lower for term in EXCLUDE_TERMS):
        return False
    return True

def parse_listing(link):
    """Parse a single listing page and extract required details."""
    html = fetch_page(link)
    if not html:
        return None

    logger.info(f"Scraping: {link}")
    soup = BeautifulSoup(html, "lxml")

    # Extract title
    title_el = soup.find("span", {"id": "titletextonly"})
    title = title_el.get_text().strip() if title_el else ""

    # Extract price
    price_el = soup.find("span", {"class": "price"})
    price = price_el.get_text().strip() if price_el else ""

    # Extract description (posting body)
    desc_section = soup.find("section", {"id": "postingbody"})
    if desc_section:
        # The text might have some leading boilerplate text; strip it
        description = desc_section.get_text().strip().replace("QR Code Link to This Post", "").strip()
    else:
        description = ""

    # Filter out by trade terms after full details fetched
    full_text = (title + " " + description).lower()
    if not contains_trade_terms(full_text):
        logger.info("Listing does not contain trade terms, skipping.")
        return None

    # Extract location
    # Some Craigslist postings show location inside <div class="mapaddress"> or near the title
    location_el = soup.find("div", {"class": "mapaddress"})
    location = location_el.get_text().strip() if location_el else ""

    # Extract Contact info
    # Craigslist often doesn't show direct contact, might show a craigslist email relay.
    # Sometimes there's a reply button leading to a popup form with email.
    # For simplicity, we'll look for visible emails or phone numbers in description.
    # Basic pattern match for emails and phone numbers:
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", description)
    phones = re.findall(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", description)
    contact_info = list(set(emails + phones))

    # Extract Basic Details
    year = None
    make_model = None
    condition = None
    cylinders = None
    drivetrain = None
    fuel_type = None
    mileage = None
    paint_color = None
    title_status = None
    transmission = None
    body_type = None
    latitude = None
    longitude = None

    # Extract attributes from the "attrgroup" section
    attributes = soup.select("div.attrgroup div.attr")
    for attr in attributes:
        label = attr.find("span", {"class": "labl"})
        value = attr.find("span", {"class": "valu"})
        if label and value:
            label_text = label.get_text(strip=True).lower()
            value_text = value.get_text(strip=True)
            if "condition" in label_text:
                condition = value_text
            elif "cylinders" in label_text:
                cylinders = value_text
            elif "drive" in label_text:
                drivetrain = value_text
            elif "fuel" in label_text:
                fuel_type = value_text
            elif "odometer" in label_text:
                mileage = value_text
            elif "paint color" in label_text:
                paint_color = value_text
            elif "title status" in label_text:
                title_status = value_text
            elif "transmission" in label_text:
                transmission = value_text
            elif "type" in label_text:
                body_type = value_text

    # Extract year and make/model from the important attributes
    important_attrs = soup.select("div.attrgroup div.important span.valu")
    if important_attrs:
        year = important_attrs[0].get_text(
            strip=True) if len(important_attrs) > 0 else None
        make_model = important_attrs[1].get_text(
            strip=True) if len(important_attrs) > 1 else None

    # Extract map coordinates
    map_data = soup.find("div", {"id": "map"})
    if map_data:
        latitude = map_data.get("data-latitude")
        longitude = map_data.get("data-longitude")

    # Extract additional specifications from the posting body
    posting_body = soup.find("section", {"id": "postingbody"})
    specifications = {}
    if posting_body:
        body_text = posting_body.get_text(strip=True)
        for line in body_text.split("\n"):
            parts = line.split(":")
            if len(parts) == 2:
                key, value = parts[0].strip().lower(), parts[1].strip()
                specifications[key] = value

    # Extract Post Info
    post_id = None
    created_at = None
    updated_at = None
    post_infos = soup.select("div.postinginfos p.postinginfo")
    for info in post_infos:
        if "post id:" in info.get_text(strip=True).lower():
            post_id = info.get_text(strip=True).split(":")[-1].strip()
        elif "posted:" in info.get_text(strip=True).lower():
            created_at = info.find("time")["datetime"]
        elif "updated:" in info.get_text(strip=True).lower():
            updated_at = info.find("time")["datetime"]

    # Extract images
    images = []
    gallery = soup.find_all("img")
    for img_tag in gallery:
        img_url = img_tag.get("src")
        if img_url and "images.craigslist.org" in img_url and img_url not in images:
            images.append(img_url)

    # Download images
    listing_id = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower())[:50]
    if not listing_id:
        # fallback if no title
        listing_id = "listing_" + str(int(time.time()))
    listing_image_dir = os.path.join(IMAGES_DIR, listing_id)
    os.makedirs(listing_image_dir, exist_ok=True)

    image_paths = []
    for i, img_url in enumerate(images):
        img_path = os.path.join(listing_image_dir, f"img_{i+1}.jpg")
        download_image(img_url, img_path)
        image_paths.append(img_path)
        
    # Build the result dictionary
    listing_data = {
        "listing_id": listing_id,
        "title": title,
        "description": description,
        "price": price,
        "year": year,
        "make_model": make_model,
        "condition": condition,
        "cylinders": cylinders,
        "drivetrain": drivetrain,
        "fuel_type": fuel_type,
        "mileage": mileage,
        "paint_color": paint_color,
        "title_status": title_status,
        "transmission": transmission,
        "body_type": body_type,
        "latitude": latitude,
        "longitude": longitude,
        "specifications": specifications,
        "post_id": post_id,
        "created_at": created_at,
        "updated_at": updated_at,
        "contact_info": contact_info,
        "image_paths": image_paths,
        "url": link
    }
    
    return listing_data

def download_image(url, path):
    """Download image from URL and save to path."""
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
        else:
            logger.warning(f"Failed to download image {url} - status {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Exception downloading image {url}: {e}")

def scrape_subdomain(subdomain):
    """Scrape listings from a given Craigslist subdomain."""
    base_url = f"https://{subdomain}.craigslist.org"
    search_url = f"{base_url}/{CATEGORY_PATH}"

    listings_data = []
    page = 0

    while page < MAX_PAGES:
        # Add s param for pagination (0 for first page, 120 per page typically)
        url = search_url
        if page > 0:
            url = f"{search_url}#search=1~gallery~{page}~0"

        logger.info(f"Scraping: {url}")
        html = fetch_page(url)
        if not html:
            break

        soup = BeautifulSoup(html, "lxml")
        results = soup.find_all("li", {"class": "cl-static-search-result"})
        if not results:
            logger.info("No more results found.")
            break

        for result in results:
            a_tag = result.find("a")
            if not a_tag:
                continue
            listing_link = a_tag.get("href")
            
            # Small delay before fetching each listing
            time.sleep(CRAWL_DELAY)
            listing_data = parse_listing(listing_link)
            if listing_data:
                listings_data.append(listing_data)

        page += 1
        # Delay between pages
        time.sleep(CRAWL_DELAY)

    return listings_data

def main():
    all_listings = []
    for subd in SUBDOMAINS:
        listings = scrape_subdomain(subd)
        all_listings.extend(listings)

    # Deduplication by listing_id if needed
    unique_ids = set()
    deduped_listings = []
    for l in all_listings:
        if l['listing_id'] not in unique_ids:
            deduped_listings.append(l)
            unique_ids.add(l['listing_id'])

    # Save output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(deduped_listings, f, ensure_ascii=False, indent=4)

    logger.info(f"Scraping complete. {len(deduped_listings)} listings saved to {OUTPUT_JSON}.")

if __name__ == "__main__":
    main()
