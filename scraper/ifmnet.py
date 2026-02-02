import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

def scrape_ifmnet_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the i-FM.net website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.i-fm.net/events"
    events = []
    
    try:
        logger.info(f"Fetching i-FM.net events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find "More info" links that lead to event pages
        more_info_links = soup.find_all('a', string=re.compile(r'More info', re.IGNORECASE))
        
        logger.info(f"Found {len(more_info_links)} 'More info' links on i-FM.net page.")
        
        seen_urls = set()
        for link in more_info_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
                
            # Skip internal i-fm.net links (we want external event links)
            if 'i-fm.net' in href and not '/events/' in href:
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://www.i-fm.net' + href
            
            seen_urls.add(href)
            
            # Try to get title from parent or sibling elements
            title = None
            parent = link.find_parent(['div', 'li', 'article'])
            if parent:
                # Look for heading or strong text
                heading = parent.find(['h2', 'h3', 'h4', 'strong'])
                if heading:
                    title = heading.get_text(strip=True)
            
            # If no title found, try to extract from URL
            if not title:
                # Parse URL to get event name
                parts = href.rstrip('/').split('/')
                if parts:
                    slug = parts[-1]
                    # Clean up common URL patterns
                    slug = re.sub(r'[?#].*$', '', slug)
                    title = slug.replace('-', ' ').replace('_', ' ').title()
            
            if not title or len(title) < 5:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'i-FM.net'
            }
            
            events.append(event_data)
            
    except Exception as e:
        logger.error(f"Error scraping i-FM.net: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_ifmnet_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
