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
        text = soup.get_text()
        
        # RealFM uses tribe-events format with structured data
        # Look for "Beginn: DD. Month" pattern
        start_match = re.search(r'Beginn[:\s]+(\d{1,2})\.?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)?', text, re.IGNORECASE)
        end_match = re.search(r'Ende[:\s]+(\d{1,2})\.?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)?', text, re.IGNORECASE)
        
        if start_match:
            start_day = start_match.group(1)
            start_month = start_match.group(2) if start_match.group(2) else ""
            
            # Try to find the year
            year_match = re.search(r'20\d{2}', text)
            year = year_match.group(0) if year_match else "2026"
            
            if end_match:
                end_day = end_match.group(1)
                end_month = end_match.group(2) if end_match.group(2) else start_month
                if start_month:
                    if end_month and end_month != start_month:
                        details['date'] = f"{start_day}. {start_month} - {end_day}. {end_month} {year}"
                    else:
                        details['date'] = f"{start_day}. - {end_day}. {start_month} {year}"
                else:
                    details['date'] = f"{start_day}. - {end_day}. April {year}"
            else:
                details['date'] = f"{start_day}. {start_month} {year}" if start_month else f"{start_day}. April {year}"
        
        # Look for Veranstaltungsort section
        venue_match = re.search(r'Veranstaltungsort\s*([A-ZÄÖÜa-zäöüß\s\-]+(?:Hotel|Hyatt|Hilton|Marriott|Center|Zentrum|Halle)[^,\n]*)', text)
        if venue_match:
            venue = venue_match.group(1).strip()
            # Try to find the city
            city_match = re.search(r'(Düsseldorf|Berlin|München|Frankfurt|Hamburg|Köln|Stuttgart|Fulda|Dresden|Leipzig)', text)
            if city_match:
                details['location'] = f"{venue}, {city_match.group(1)}"
            else:
                details['location'] = venue
        else:
            # Fallback: look for common city names
            city_match = re.search(r'(Düsseldorf|Berlin|München|Frankfurt|Hamburg|Köln|Stuttgart|Fulda|Dresden|Leipzig)', text)
            if city_match:
                details['location'] = city_match.group(1)
        
        # Also try extracting from title if contains city name
        if 'location' not in details:
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                city_match = re.search(r'(Düsseldorf|Berlin|München|Frankfurt|Hamburg|Köln|Stuttgart|Fulda|Dresden|Leipzig)', title_text)
                if city_match:
                    details['location'] = city_match.group(1)
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_realfm_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the RealFM website.
    Returns a list of dictionaries containing event details.
    """
    url = "http://realfm.de/events/"
    events = []
    
    try:
        logger.info(f"Fetching RealFM events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find event links - they are in h4 tags with anchors
        event_links = soup.select('h4 a[href*="/event/"]')
        
        # Also try tribe-events format
        if not event_links:
            event_links = soup.select('.tribe-events-list-event-title a')
        
        # Fallback: find any links containing "/event/" in href
        if not event_links:
            event_links = soup.find_all('a', href=re.compile(r'/event/'))
        
        logger.info(f"Found {len(event_links)} event links on RealFM page.")
        
        seen_urls = set()
        for link in event_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://www.realfm.de' + href
            elif not href.startswith('http'):
                href = 'https://www.realfm.de/' + href
            
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            if not title:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'RealFM'
            }
            
            # Try to extract date and location from title
            # Pattern: "NUTZERKONGRESS in Düsseldorf 21. – 22. April 2026"
            date_match = re.search(r'(\d{1,2})\.?\s*[-–]\s*(\d{1,2})\.?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})', title, re.IGNORECASE)
            if date_match:
                event_data['date'] = date_match.group(0)
            else:
                # Try simpler format
                date_match = re.search(r'(\d{1,2})\.?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})', title, re.IGNORECASE)
                if date_match:
                    event_data['date'] = date_match.group(0)
            
            # Try to extract location from title (usually "in [City]")
            location_match = re.search(r'\s+in\s+([A-ZÄÖÜa-zäöüß\-]+)(?:\s|$)', title)
            if location_match:
                event_data['location'] = location_match.group(1)
            
            events.append(event_data)
        
        # Fetch additional details from event pages
        logger.info("Fetching additional details from event pages...")
        for event in events:
            if event['url'] and (event['date'] == 'See details' or event['location'] == 'See details'):
                details = fetch_event_details(event['url'])
                if 'date' in details and event.get('date') == 'See details':
                    event['date'] = details['date']
                if 'location' in details and event.get('location') == 'See details':
                    event['location'] = details['location']
            
    except Exception as e:
        logger.error(f"Error scraping RealFM: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_realfm_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
