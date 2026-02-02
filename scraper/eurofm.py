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
        
        # Look for "On [Month] [DD] and [DD]" or "On [Month] [DD]" patterns (English)
        date_match = re.search(r'On\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:\s+and\s+(\d{1,2}))?', text, re.IGNORECASE)
        if date_match:
            month = date_match.group(1)
            day1 = date_match.group(2)
            day2 = date_match.group(3)
            
            # Find year
            year_match = re.search(r'20\d{2}', text)
            year = year_match.group(0) if year_match else "2026"
            
            if day2:
                details['date'] = f"{day1}-{day2} {month} {year}"
            else:
                details['date'] = f"{day1} {month} {year}"
        else:
            # Try "DD-DD Month YYYY" format
            date_match = re.search(r'(\d{1,2})[-–](\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text, re.IGNORECASE)
            if date_match:
                details['date'] = date_match.group(0)
            else:
                # Try "DD Month YYYY" format
                date_match = re.search(r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text, re.IGNORECASE)
                if date_match:
                    details['date'] = date_match.group(0)
        
        # Look for location patterns
        # "in The [Venue] in [City]" or "in [City]"
        location_match = re.search(r'(?:in|at)\s+(?:The\s+)?([A-Z][A-Za-z\s\-]+(?:Terminal|Center|Centre|Hotel|Hall))\s+in\s+([A-Z][A-Za-z\s\-]+)', text)
        if location_match:
            venue = location_match.group(1).strip()
            city = location_match.group(2).strip()
            details['location'] = f"{venue}, {city}"
        else:
            # Look for common European cities mentioned
            city_match = re.search(r'(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
            if city_match:
                potential_city = city_match.group(1)
                known_cities = ['The Hague', 'Amsterdam', 'London', 'Birmingham', 'Trondheim', 'Munich', 'Vienna', 'Brussels', 'Paris']
                if potential_city in known_cities:
                    details['location'] = potential_city
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_eurofm_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the EuroFM website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://eurofm.org/events/"
    events = []
    
    try:
        logger.info(f"Fetching EuroFM events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find "More info" links that lead to event pages
        more_info_links = soup.find_all('a', string=re.compile(r'More info', re.IGNORECASE))
        
        # Also look for h4 headers containing event titles
        event_headers = soup.find_all('h4')
        
        logger.info(f"Found {len(more_info_links)} 'More info' links on EuroFM page.")
        
        seen_urls = set()
        for link in more_info_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Skip the main events page
            if href.endswith('/events/') or href == url:
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://eurofm.org' + href
            elif not href.startswith('http'):
                href = 'https://eurofm.org/' + href
            
            seen_urls.add(href)
            
            # Get title from preceding h4 or sibling text
            title = None
            parent = link.find_parent()
            if parent:
                prev_h4 = parent.find_previous_sibling('h4')
                if prev_h4:
                    title = prev_h4.get_text(strip=True)
            
            # If no h4 found, try to extract title from URL
            if not title:
                # Extract title from URL slug
                slug = href.rstrip('/').split('/')[-1]
                title = slug.replace('-', ' ').title()
            
            if not title:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'EuroFM'
            }
            
            # Try to extract location from title (often contains city)
            # "World Workplace Europe 2026 – The Hague"
            location_match = re.search(r'[-–]\s*([A-Z][A-Za-z\s]+)$', title)
            if location_match:
                event_data['location'] = location_match.group(1).strip()
            
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
        logger.error(f"Error scraping EuroFM: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_eurofm_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
