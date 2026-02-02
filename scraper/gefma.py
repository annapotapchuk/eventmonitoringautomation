import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict, Optional

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
        
        # Look for "Veranstaltungstermin:" pattern
        date_match = re.search(r'Veranstaltungstermin:\s*([^\n]+)', text)
        if date_match:
            details['date'] = date_match.group(1).strip()
        
        # Look for "Veranstaltungsort:" pattern
        location_match = re.search(r'Veranstaltungsort:\s*([^\n]+)', text)
        if location_match:
            details['location'] = location_match.group(1).strip()
            
    except Exception as e:
        logger.warning(f"Could not fetch details from {url}: {e}")
    
    return details

def scrape_gefma_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the GEFMA website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.gefma.de/hashtag/event"
    events = []
    
    try:
        logger.info(f"Fetching GEFMA events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Select event cards
        cards = soup.select('div.article.articletype-0')
        logger.info(f"Found {len(cards)} event cards on GEFMA page.")
        
        for card in cards:
            event_data = {}
            
            # Title extraction
            title_tag = card.select_one('.header h3 span')
            # Fallback to title attribute in link if h3 is empty/missing
            if not title_tag:
                 link_tag_title = card.select_one('.titledatelocation > a')
                 if link_tag_title and 'title' in link_tag_title.attrs:
                     event_data['title'] = link_tag_title['title']
                 else:
                     event_data['title'] = "N/A"
            else:
                event_data['title'] = title_tag.get_text(strip=True)

            # Link extraction
            link_tag = card.select_one('.titledatelocation > a')
            if link_tag and 'href' in link_tag.attrs:
                event_data['url'] = "https://www.gefma.de" + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href']
            else:
                event_data['url'] = "N/A"

            # Date extraction
            date_tag = card.select_one('.teaser-text .date')
            if date_tag:
                # The date text might contain extra info like " - Details..."
                full_date_text = date_tag.get_text(strip=True)
                # Only take the DD.MM.YYYY part if it exists at the start
                date_part = full_date_text.split('-')[0].strip()
                event_data['date'] = date_part
            else:
                event_data['date'] = "See details"
                
            # Location - initially set as See details
            event_data['location'] = "See details"
            event_data['source'] = 'GEFMA'
            
            events.append(event_data)
        
        # Fetch additional details from each event's detail page
        logger.info("Fetching additional details from event pages...")
        for event in events:
            if event['url'] != "N/A":
                details = fetch_event_details(event['url'])
                
                # Update date if we got a better one
                if 'date' in details and event.get('date') == "See details":
                    event['date'] = details['date']
                    
                # Update location if found
                if 'location' in details:
                    event['location'] = details['location']
            
    except Exception as e:
        logger.error(f"Error scraping GEFMA: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_gefma_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
