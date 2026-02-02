import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def scrape_ifma_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the IFMA website.
    Returns a list of dictionaries containing event details.
    """
    url = "https://www.ifma.org/events/"
    events = []
    
    try:
        logger.info(f"Fetching IFMA events from {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Locate the schedule section
        schedule = soup.find(id='event-schedule')
        if not schedule:
            logger.warning("Could not find '#event-schedule' section on IFMA page.")
            return []
            
        # Find <a> tags that look like events (simple heuristic based on year '2026' or just assuming all links in the grid are events)
        # However, to be more robust, let's look for the structure identified:
        # The events seem to be presented as simple text links inside the grid, or we can just grab all links in the grid that are not filters.
        
        grid = schedule.find(class_='event-listing-grid')
        if not grid:
            logger.warning("Could not find '.event-listing-grid' inside schedule.")
            return []
            
        # Extract links text and href
        # Based on research, the links were direct children of the grid containers or close to it.
        # "Match 0 parent: a class=None ... > World Workplace 2026"
        
        event_cards = grid.find_all(class_='event-card') # Hypothesizing class name based on typical structure if direct children were 2.
        # Wait, previous output said "Grid has 2 direct children". One was filters.
        # Let's try to iterate over proper card elements if we can identify them, or look for specific heading tags.
        
        # Re-analyzing based on "Learn More" links. The text "Learn More" suggests these are buttons.
        # Valid logic: find the "Learn More" link, then look at its siblings or parents for the title.
        
        seen_urls = set()
        links = grid.find_all('a', href=True)
        for link in links:
            if "learn more" in link.get_text(strip=True).lower():
                # Traverse up to find the details container
                details_container = link.find_parent(class_='event-listing-grid__event-details')
                if details_container:
                    # The header is a direct child usually, or very close. 
                    # Debug output showed: Parent 2: <div class=['event-listing-grid__event-details']> -> Headers (direct): ['Title']
                    title_tag = details_container.find(['h3', 'h4', 'h2'])
                    if title_tag:
                         title = title_tag.get_text(strip=True)
                    else:
                         title = "N/A"
                    
                    url_href = link['href']
                    if url_href not in seen_urls:
                        seen_urls.add(url_href)
                        events.append({
                            'title': title,
                            'date': "See details", 
                            'location': "See details", 
                            'url': url_href,
                            'source': 'IFMA'
                        })
                
    except Exception as e:
        logger.error(f"Error scraping IFMA: {e}")
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(scrape_ifma_events())
