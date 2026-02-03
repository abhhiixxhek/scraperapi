# scraperapi

## Supplier scraping (ScraperAPI + Google)

Use `scraper.py` to discover supplier pages via Google search and extract contact details
with ScraperAPI. Output is a JSON array with a schema aligned to your supplier table.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml
```

### Run

Create a `.env` file (recommended):

```bash
SCRAPERAPI_KEY="YOUR_KEY"
```

Run the scraper:

```bash
python scraper.py \
  --query "China chemical suppliers list" \
  --country "China" \
  --region "Asia" \
  --country-code cn \
  --num-results 20 \
  --output suppliers.json
```

You can also pass the key directly:

```bash
python scraper.py --api-key "YOUR_KEY" --query "China chemical suppliers list"
```

> **Security note:** keep your ScraperAPI key in a `.env` file or secrets manager.
> Avoid committing real API keys to source control.

### Output

The script emits `suppliers.json` with fields like:

- Supplier name
- Website
- Country/region
- Email(s)
- Contact number(s)
- Company summary (from page metadata)
- Source URL(s)

You can expand the extraction logic in `scraper.py` to map additional fields such as
certifications, capacities, or export capabilities as needed.
