import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

def scrape_fmj_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the FMJ (Facilities Management Journal) website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.fmj.co.uk/events/category/events/"
    events = []
    
    try:
        logger.info(f"Fetching FMJ events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find event articles - they have h2 headers with links
        event_articles = soup.select('article, .post, .event-item')
        
        # If no articles found, look for h2 links directly
        if not event_articles:
            event_links = soup.select('h2 a[href*="/events/event/"]')
        else:
            event_links = []
            for article in event_articles:
                link = article.select_one('h2 a, .entry-title a')
                if link:
                    event_links.append(link)
        
        # Fallback: find any links to event pages
        if not event_links:
            event_links = soup.find_all('a', href=re.compile(r'/events/event/'))
        
        logger.info(f"Found {len(event_links)} event links on FMJ page.")
        
        seen_urls = set()
        for link in event_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Make sure it's a full URL
            if href.startswith('/'):
                href = 'https://www.fmj.co.uk' + href
            elif not href.startswith('http'):
                href = 'https://www.fmj.co.uk/' + href
            
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            if not title:
                continue
            
            event_data = {
                'title': title,
                'url': href,
                'date': 'See details',
                'location': 'See details',
                'source': 'FMJ'
            }
            
            # Try to find date in surrounding text
            # FMJ often has dates in the description like "04 February 2026"
            parent = link.find_parent(['article', 'div'])
            if parent:
                text = parent.get_text()
                date_match = re.search(r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text, re.IGNORECASE)
                if date_match:
                    event_data['date'] = date_match.group(0)
                
                # Look for location in format "Location: ..." or city names
                location_match = re.search(r'Location[:\s]+([^,\n]+)', text, re.IGNORECASE)
                if location_match:
                    event_data['location'] = location_match.group(1).strip()
                else:
                    # Try to extract location from title (many FMJ events include city)
                    city_match = re.search(r'(London|Manchester|Birmingham|Leeds|Bristol|Essex|Maidstone|York|Hertford|Redhill)', title, re.IGNORECASE)
                    if city_match:
                        event_data['location'] = city_match.group(1)
            
            events.append(event_data)
            
    except Exception as e:
        logger.error(f"Error scraping FMJ: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_fmj_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
