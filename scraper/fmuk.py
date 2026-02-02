import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def scrape_fmuk_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the FMUK (Facilities Management UK) website.
    Returns a list of dictionaries containing event details.
    
    Note: This page currently appears to have no events listed.
    The scraper will gracefully return an empty list if no events are found.
    """
    url = "https://fmuk-online.co.uk/events/"
    events = []
    
    try:
        logger.info(f"Fetching FMUK events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for event articles or list items
        event_items = soup.select('article.event, .event-item, .tribe-events-list-event')
        
        # Fallback: look for any links that might be events
        if not event_items:
            event_links = soup.find_all('a', href=lambda h: h and '/events/' in h and h != url)
            for link in event_links:
                # Filter out navigation/menu links
                parent = link.find_parent(['nav', 'header', 'footer', 'aside'])
                if parent:
                    continue
                    
                href = link.get('href', '')
                if href and href != url and not href.endswith('/events/') and not href.endswith('/events'):
                    title = link.get_text(strip=True)
                    if title and len(title) > 5:  # Filter out very short text
                        if not href.startswith('http'):
                            href = 'https://fmuk-online.co.uk' + ('' if href.startswith('/') else '/') + href
                        
                        events.append({
                            'title': title,
                            'url': href,
                            'date': 'See details',
                            'location': 'See details',
                            'source': 'FMUK'
                        })
        
        logger.info(f"Found {len(events)} events on FMUK page.")
            
    except Exception as e:
        logger.error(f"Error scraping FMUK: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_fmuk_events()
    if events:
        for e in events:
            print(f"  {e['title']} | {e['date']} | {e['location']}")
    else:
        print("  No events found on FMUK page (this may be expected)")
