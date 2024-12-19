# Craigslist Vehicle Listings Scraper

A Python-based web scraper designed to extract vehicle listings from Craigslist that explicitly mention being open to trades. The scraper targets specific cities, filters listings based on predefined keywords, and collects detailed information along with images.

## Features

- Scrapes Craigslist vehicle listings in Southern California.
- Filters listings containing terms like "trade," "swap," or "open to trading," while excluding terms like "no trades" or "no swap."
- Collects the following details for each listing:
  - Title
  - Description
  - Price
  - Vehicle details (make, model, year, mileage, etc.)
  - Location
  - Contact information (if publicly available)
  - Associated images
- Saves data in a structured JSON file and organizes images by listing.
- Handles pagination and ensures compliance with Craigslist's terms of use.

## Requirements

- Python 3.7+
- Libraries:
  - `requests`
  - `beautifulsoup4`
  - `lxml`
  - `logging`

Install the dependencies using:
```bash
pip install -r requirements.txt
```

## Parameters

The scraper behavior can be configured through the following constants at the top of the code:

- **SUBDOMAINS**: A list of Craigslist subdomains to scrape, representing cities or regions. Example:
  ```python
  SUBDOMAINS = ["losangeles", "orangecounty", "sandiego"]
  ```

- **CATEGORY_PATH**: The Craigslist category path to target. For vehicles by owner:
  ```python
  CATEGORY_PATH = "d/cars-trucks-by-owner/search/cto"
  ```

- **INCLUDE_TERMS**: Keywords to identify listings open to trades. Example:
  ```python
  INCLUDE_TERMS = ["trade", "swap", "open to trading"]
  ```

- **EXCLUDE_TERMS**: Keywords to filter out listings explicitly not open to trades. Example:
  ```python
  EXCLUDE_TERMS = ["no trade", "no trades", "no swap", "not open to trading"]
  ```

- **CRAWL_DELAY**: Delay (in seconds) between requests to reduce bot detection:
  ```python
  CRAWL_DELAY = 1
  ```

- **MAX_PAGES**: The maximum number of pages to scrape per subdomain:
  ```python
  MAX_PAGES = 10
  ```

- **IMAGES_DIR**: Directory where images will be downloaded and stored:
  ```python
  IMAGES_DIR = "images"
  ```

- **OUTPUT_JSON**: Name of the output file where scraped data will be saved:
  ```python
  OUTPUT_JSON = "listings.json"
  ```

- **USER_AGENTS**: A list of User-Agent strings to randomize requests and reduce bot detection:
  ```python
  USER_AGENTS = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)",
      "Mozilla/5.0 (X11; Linux x86_64)"
  ]
  ```

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/craigslist-trade-scraper.git
   cd craigslist-trade-scraper
   ```

2. Run the script:
   ```bash
   python scraper.py
   ```

3. Output:
   - Scraped data is saved in `listings.json`.
   - Images are downloaded into the `images/` directory, organized by listing ID.

## Output Example

### JSON Structure
```json
[
  {
      "listing_id": "2000_bmw_m5_lemans_blue_extreme_service_records_an",
      "title": "2000 BMW M5 - LeMans Blue - Extreme Service Records and Mint condition",
      "description": "2000 BMW M5\nClean title \n180k Miles...",
      "price": "$25,000",
      "year": "2000",
      "make_model": "BMW M5",
      "condition": null,
      "cylinders": null,
      "drivetrain": null,
      "fuel_type": "gas",
      "mileage": "180,000",
      "paint_color": null,
      "title_status": "clean",
      "transmission": "manual",
      "body_type": null,
      "latitude": "34.090100",
      "longitude": "-118.406500",
      "specifications": {},
      "post_id": "7811620185",
      "created_at": "2024-12-18T17:19:37-0800",
      "updated_at": null,
      "contact_info": [],
      "image_paths": [
          "images/2000_bmw_m5_lemans_blue_extreme_service_records_an/img_1.jpg",
          "images/2000_bmw_m5_lemans_blue_extreme_service_records_an/img_2.jpg",
      ],
      "url": "https://losangeles.craigslist.org/lac/cto/d/beverly-hills-2000-bmw-m5-lemans-blue/7811620185.html"
  },
]
```

## Notes

- The script uses randomized user agents to reduce detection risk.
- Craigslist scraping must comply with [Craigslist Terms of Use](https://www.craigslist.org/about/terms.of.use).
- For large-scale scraping, consider adding proxy rotation and rate limiting.
