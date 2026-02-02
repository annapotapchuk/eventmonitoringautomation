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
        
        # Look for German date patterns
        date_match = re.search(r'(\d{1,2})\.?\s*[-–]?\s*(\d{1,2})?\.?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})', text, re.IGNORECASE)
        if date_match:
            details['date'] = date_match.group(0)
        else:
            date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
            if date_match:
                details['date'] = date_match.group(0)
        
        # Look for location/venue
        location_match = re.search(r'(?:Ort|Veranstaltungsort|Location)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if location_match:
            details['location'] = location_match.group(1).strip()
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_i2fm_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the i2FM website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://i2fm.de/termine/"
    events = []
    
    try:
        logger.info(f"Fetching i2FM events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find event links - look for "mehr lesen" links or direct event links
        event_links = soup.find_all('a', href=re.compile(r'i2fm\.de/(?!termine/$)'))
        
        logger.info(f"Found {len(event_links)} potential links on i2FM page.")
        
        seen_urls = set()
        for link in event_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Skip navigation links
            if any(skip in href for skip in ['/ueber-uns', '/plattformen', '/mediathek', '/referenzprojekte', 
                                              '/workplace', '/cafm', '/datenschutz', '/impressum',
                                              '/allgemeine-teilnahmebedingungen', '/termine/?', '/termine/#']):
                continue
            
            # Skip the main termine page
            if href.rstrip('/').endswith('/termine'):
                continue
            
            # Clean up URL (some have trailing spaces)
            href = href.strip().rstrip('%20').rstrip(' ')
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://i2fm.de' + href
            
            # Only include i2fm.de links (including subdomains like nutzerkongress.i2fm.de)
            if 'i2fm.de' not in href:
                continue
            
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            
            # Skip "mehr lesen" links - try to get title from sibling/parent
            if title.lower() == 'mehr lesen':
                parent = link.find_parent(['div', 'li', 'article'])
                if parent:
                    # Look for another link with the actual title
                    title_link = parent.find('a', string=lambda s: s and s.lower() != 'mehr lesen')
                    if title_link:
                        title = title_link.get_text(strip=True)
                    else:
                        # Try to find any heading
                        heading = parent.find(['h2', 'h3', 'h4', 'strong'])
                        if heading:
                            title = heading.get_text(strip=True)
            
            if not title or len(title) < 5 or title.lower() == 'mehr lesen':
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'i2FM'
            }
            
            events.append(event_data)
        
        # Deduplicate by title (keep first occurrence)
        seen_titles = set()
        unique_events = []
        for event in events:
            if event['title'] not in seen_titles:
                seen_titles.add(event['title'])
                unique_events.append(event)
        events = unique_events
        
        # Fetch additional details from event pages
        logger.info("Fetching additional details from event pages...")
        for event in events[:10]:  # Limit to avoid too many requests
            if event['url'] and event.get('date') == 'See details':
                details = fetch_event_details(event['url'])
                if 'date' in details:
                    event['date'] = details['date']
                if 'location' in details:
                    event['location'] = details['location']
            
    except Exception as e:
        logger.error(f"Error scraping i2FM: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_i2fm_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
