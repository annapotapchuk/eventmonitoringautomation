import requests
from bs4 import BeautifulSoup

url = "https://www.gefma.de/hashtag/event"
try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    cards = soup.select('div.article.articletype-0')
    print(f"Found {len(cards)} cards.")

    if cards:
        card = cards[0]
        # Print structured representation
        print(card.prettify())
        
        # Attempt extraction
        title_tag = card.select_one('.titledatelocation a')
        title = title_tag['title'] if title_tag and 'title' in title_tag.attrs else "N/A"
        link = title_tag['href'] if title_tag else "N/A"
        
        # Try to find date and location. Usually text in the cell titledatelocation
        content_cell = card.select_one('.titledatelocation')
        print("\n--- Text Content of titledatelocation ---")
        if content_cell:
            print(content_cell.get_text(separator=' | ', strip=True))

except Exception as e:
    print(e)
