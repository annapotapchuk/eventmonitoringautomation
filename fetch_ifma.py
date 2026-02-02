import requests
from bs4 import BeautifulSoup

url = "https://www.ifma.org/events/"
try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    schedule = soup.find(id='event-schedule')
    if schedule:
        # Look for the grid
        grid = schedule.find(class_='event-listing-grid')
        if grid:
            # Look for what likely represents an event card. 
            # Usually child divs of the grid, often with col-* classes.
            # Let's check children that have classes.
            children = grid.find_all(recursive=False)
            print(f"Grid has {len(children)} direct children.")
            
            # The output showed filters in the first child.
            # Let's look for other children that might be events.
            # Searching for children that contain '2026' text or similar event indicators
            
            event_cards = []
            for child in grid.descendants:
                # heuristic: class name containing 'card' or 'item' or 'event'
                if child.name == 'div' and child.get('class'):
                    classes = child.get('class')
                    if any('card' in c for c in classes) or 'event-card' in classes: # Hypothesis
                        # print(child.prettify()[:200])
                        pass
            
            # Better approach: find the <a> tags with event names and look at their parents
            links = schedule.find_all('a', string=lambda s: s and '2026' in s)
            if links:
                print(f"Found {len(links)} event links.")
                parent_card = links[0].find_parent(class_=lambda x: x and ('card' in x or 'item' in x or 'col' in x))
                if parent_card:
                    print("\n--- Parent Card Structure ---")
                    print(parent_card.prettify()[:1000])

except Exception as e:
    print(e)
