import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

def fetch_event_details(url: str) -> Dict[str, str]:
    """
    Fetches additional details from an event's detail page.
    Returns dict with 'date' and 'location' if found.
    """
    details = {}
    try:
        logger.debug(f"Fetching details from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # First, try to get date and location from OG description meta tag
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            desc_text = og_desc['content']
            
            # Pattern: "Am DD./DD. Month YYYY" (date range) or "Am DD. Month YYYY"
            date_range_match = re.search(r'Am\s+(\d{1,2})\.\s*/?\s*(\d{1,2})?\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})', desc_text, re.IGNORECASE)
            if date_range_match:
                day1 = date_range_match.group(1)
                day2 = date_range_match.group(2)
                month = date_range_match.group(3)
                year = date_range_match.group(4)
                if day2:
                    details['date'] = f"{day1}./​{day2}. {month} {year}"
                else:
                    details['date'] = f"{day1}. {month} {year}"
            
            # Try to extract location - often "in [City]" or mentions like "Esperanto ... in Fulda"
            location_match = re.search(r'(?:in|im)\s+(?:der\s+)?(?:dem\s+)?([A-ZÄÖÜa-zäöüß\s\-]+(?:Halle|Zentrum|Hotel|Center|halle|zentrum)?)(?:\s+in\s+([A-ZÄÖÜa-zäöüß\-]+))?', desc_text, re.IGNORECASE)
            if location_match:
                venue = location_match.group(1).strip() if location_match.group(1) else ""
                city = location_match.group(2).strip() if location_match.group(2) else ""
                if city:
                    details['location'] = f"{venue}, {city}" if venue else city
                elif venue:
                    details['location'] = venue
        
        # If not found in OG description, search in the page text
        text = soup.get_text()
        
        if 'date' not in details:
            # Look for "Am DD./DD. Month YYYY" pattern in text
            date_range_match = re.search(r'Am\s+(\d{1,2})\.\s*/?\s*(\d{1,2})?\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})', text, re.IGNORECASE)
            if date_range_match:
                day1 = date_range_match.group(1)
                day2 = date_range_match.group(2)
                month = date_range_match.group(3)
                year = date_range_match.group(4)
                if day2:
                    details['date'] = f"{day1}./​{day2}. {month} {year}"
                else:
                    details['date'] = f"{day1}. {month} {year}"
            else:
                # Try DD.MM.YYYY format
                date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
                if date_match:
                    details['date'] = date_match.group(0)
        
        if 'location' not in details:
            # Look for common venue patterns
            # "Esperanto Kongress & Kulturzentrum in Fulda" or similar
            venue_match = re.search(r'(Esperanto[^,\.]+?)(?:\s+in\s+|\s*,\s*)([A-ZÄÖÜa-zäöüß\-]+)', text)
            if venue_match:
                details['location'] = f"{venue_match.group(1).strip()}, {venue_match.group(2).strip()}"
            else:
                # Look for "Veranstaltungsort:" or "Ort:" patterns
                location_match = re.search(r'(?:Ort|Veranstaltungsort|Location)[:\s]+([^\n]+)', text, re.IGNORECASE)
                if location_match:
                    details['location'] = location_match.group(1).strip()
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_facility_manager_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the Facility-Manager.de website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.facility-manager.de/category/veranstaltungen/"
    events = []
    
    try:
        logger.info(f"Fetching Facility-Manager.de events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find event links in h3 headers
        event_links = soup.select('h3 a[href]')
        
        # Filter to only include veranstaltungen-related links
        if not event_links:
            event_links = soup.find_all('a', href=re.compile(r'facility-manager\.de'))
        
        logger.info(f"Found {len(event_links)} potential event links on Facility-Manager.de page.")
        
        seen_urls = set()
        for link in event_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Skip category pages and author pages
            if '/category/' in href or '/author/' in href or '/tag/' in href:
                continue
            
            # Skip aktuelles (news) pages - focus on actual events
            if '/aktuelles/' in href:
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://www.facility-manager.de' + href
            elif not href.startswith('http'):
                continue
            
            # Only include facility-manager.de links
            if 'facility-manager.de' not in href:
                continue
            
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'Facility-Manager.de'
            }
            
            events.append(event_data)
        
        # Fetch details from each event page
        logger.info("Fetching additional details from event pages...")
        for event in events:
            if event['url']:
                details = fetch_event_details(event['url'])
                if 'date' in details:
                    event['date'] = details['date']
                if 'location' in details:
                    event['location'] = details['location']
            
    except Exception as e:
        logger.error(f"Error scraping Facility-Manager.de: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_facility_manager_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
