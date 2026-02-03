import argparse
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Iterable, List, Optional
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
)


@dataclass
class SupplierRecord:
    serial_number: int
    name: str
    company_details: Optional[str] = None
    export_capabilities: Optional[str] = None
    operational_experience_years: Optional[str] = None
    product_service_capability: Optional[str] = None
    annual_capacity_mt: Optional[str] = None
    process_capabilities: Optional[str] = None
    supply_chain_solutions_available: Optional[str] = None
    quality_certifications: Optional[str] = None
    business_metrics: Optional[str] = None
    commercial_capabilities: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    year_of_establishment: Optional[str] = None
    company_ownership: Optional[str] = None
    management_structure: Optional[str] = None
    factory_locations: Optional[str] = None
    key_clients: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    capability_to_export: Optional[str] = None
    global_presence: Optional[str] = None
    products_services_offered: Optional[str] = None
    end_use_applications: Optional[str] = None
    key_usps: Optional[str] = None
    total_capacity_units_per_annum: Optional[str] = None
    open_capacity_percent: Optional[str] = None
    process_1: Optional[str] = None
    process_2: Optional[str] = None
    process_3: Optional[str] = None
    other_certifications: Optional[str] = None
    annual_revenues_usd_mn: Optional[str] = None
    number_of_employees: Optional[str] = None
    pricing_capabilities: Optional[str] = None
    lead_time: Optional[str] = None
    payment_terms: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    notes: Optional[str] = None


def _scraperapi_url(api_key: str, target_url: str, country_code: str) -> str:
    return (
        "https://api.scraperapi.com/?"
        f"api_key={api_key}&url={quote_plus(target_url)}&country_code={country_code}"
    )


def _get_html(session: requests.Session, api_key: str, url: str, country_code: str) -> str:
    response = session.get(_scraperapi_url(api_key, url, country_code), timeout=30)
    response.raise_for_status()
    return response.text


def google_search(
    session: requests.Session, api_key: str, query: str, country_code: str, num_results: int
) -> List[str]:
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
    html = _get_html(session, api_key, search_url, country_code)
    soup = BeautifulSoup(html, "lxml")
    links = []
    for result in soup.select("a"):
        href = result.get("href", "")
        if href.startswith("/url?q="):
            link = href.split("/url?q=")[-1].split("&")[0]
            if link and "google.com" not in link:
                links.append(link)
        if len(links) >= num_results:
            break
    return list(dict.fromkeys(links))


def _extract_emails(text: str) -> List[str]:
    return sorted(set(match.group(0) for match in EMAIL_RE.finditer(text)))


def _extract_phones(text: str) -> List[str]:
    phones = []
    for match in PHONE_RE.finditer(text):
        value = match.group(0)
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 7:
            phones.append(value.strip())
    return sorted(set(phones))


def _cleanup_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _page_summary(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return _cleanup_text(meta["content"])
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    if paragraphs:
        return _cleanup_text(" ".join(paragraphs[:3]))
    return ""


def _best_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return _cleanup_text(soup.title.string)
    h1 = soup.find("h1")
    if h1:
        return _cleanup_text(h1.get_text(" ", strip=True))
    return ""


def scrape_supplier_page(
    session: requests.Session,
    api_key: str,
    url: str,
    country: str,
    region: str,
    country_code: str,
) -> SupplierRecord:
    html = _get_html(session, api_key, url, country_code)
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    emails = _extract_emails(text)
    phones = _extract_phones(text)
    title = _best_title(soup)
    summary = _page_summary(soup)

    return SupplierRecord(
        serial_number=0,
        name=title or urlparse(url).netloc,
        company_details=summary or None,
        website=url,
        country=country,
        region=region,
        contact_number=", ".join(phones) if phones else None,
        email=", ".join(emails) if emails else None,
        products_services_offered=None,
        export_capabilities=None,
        sources=[url],
        notes=None,
    )


def enrich_record_from_directory(record: SupplierRecord, directory_text: str) -> None:
    emails = _extract_emails(directory_text)
    phones = _extract_phones(directory_text)
    if emails and not record.email:
        record.email = ", ".join(emails)
    if phones and not record.contact_number:
        record.contact_number = ", ".join(phones)


def build_records(
    session: requests.Session,
    api_key: str,
    query: str,
    country: str,
    region: str,
    country_code: str,
    num_results: int,
    delay_s: float,
) -> List[SupplierRecord]:
    links = google_search(session, api_key, query, country_code, num_results)
    records: List[SupplierRecord] = []
    for idx, url in enumerate(links, start=1):
        try:
            record = scrape_supplier_page(
                session=session,
                api_key=api_key,
                url=url,
                country=country,
                region=region,
                country_code=country_code,
            )
            record.serial_number = idx
            records.append(record)
            time.sleep(delay_s)
        except requests.RequestException as exc:
            records.append(
                SupplierRecord(
                    serial_number=idx,
                    name=urlparse(url).netloc,
                    website=url,
                    country=country,
                    region=region,
                    notes=f"Failed to fetch page: {exc}",
                    sources=[url],
                )
            )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape supplier data using ScraperAPI + Google search"
    )
    parser.add_argument("--api-key", default=os.getenv("SCRAPERAPI_KEY"))
    parser.add_argument(
        "--query",
        default="China chemical suppliers list",
        help="Google search query for supplier discovery",
    )
    parser.add_argument("--country", default="China")
    parser.add_argument("--region", default="Asia")
    parser.add_argument("--country-code", default="cn")
    parser.add_argument("--num-results", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--output", default="suppliers.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing ScraperAPI key. Set SCRAPERAPI_KEY or --api-key.")
    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                )
            }
        )
        records = build_records(
            session=session,
            api_key=args.api_key,
            query=args.query,
            country=args.country,
            region=args.region,
            country_code=args.country_code,
            num_results=args.num_results,
            delay_s=args.delay,
        )

    payload = [asdict(record) for record in records]
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} suppliers to {args.output}")


if __name__ == "__main__":
    main()
