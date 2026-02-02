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
        
        # Look for date patterns - IWFM often has "Date:" or specific date formats
        date_match = re.search(r'Date[:\s]+([^\n]+)', text, re.IGNORECASE)
        if date_match:
            details['date'] = date_match.group(1).strip()
        else:
            # Try to find date in format "DD Month YYYY" or similar
            date_match = re.search(r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text, re.IGNORECASE)
            if date_match:
                details['date'] = date_match.group(0)
        
        # Look for location/venue
        location_match = re.search(r'(?:Location|Venue)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if location_match:
            details['location'] = location_match.group(1).strip()
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_iwfm_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the IWFM website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.iwfm.org.uk/community/events.html"
    events = []
    
    try:
        logger.info(f"Fetching IWFM events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find event links in h3 headers
        event_links = soup.select('h3 a[href*="/events/"]')
        
        # Fallback: find any event links
        if not event_links:
            event_links = soup.find_all('a', href=re.compile(r'/community/events/'))
        
        logger.info(f"Found {len(event_links)} event links on IWFM page.")
        
        seen_urls = set()
        for link in event_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Skip the main events page link
            if href.endswith('/events.html') or href.endswith('/events'):
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://www.iwfm.org.uk' + href
            elif not href.startswith('http'):
                href = 'https://www.iwfm.org.uk/' + href
            
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            if not title:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'IWFM'
            }
            
            events.append(event_data)
        
        # Fetch additional details from event pages
        logger.info("Fetching additional details from event pages...")
        for event in events:
            if event['url']:
                details = fetch_event_details(event['url'])
                if 'date' in details and event.get('date') == 'See details':
                    event['date'] = details['date']
                if 'location' in details and event.get('location') == 'See details':
                    event['location'] = details['location']
            
    except Exception as e:
        logger.error(f"Error scraping IWFM: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_iwfm_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
