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


python scraper.py \
  --query "China chemical suppliers list" \
  --country "China" \
  --region "Asia" \
  --country-code cn \
  --num-results 20 \
  --output suppliers.json
```



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
