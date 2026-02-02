import requests
from bs4 import BeautifulSoup

url = "https://www.ifma.org/events/"
try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, 'html.parser')

    links = soup.find_all('a', href=True)
    count = 0
    for link in links:
        if "learn more" in link.get_text(strip=True).lower():
            count += 1
            print(f"\n--- Link {count}: {link['href']} ---")
            # Print parents up to 3 levels
            curr = link
            for i in range(3):
                curr = curr.parent
                if curr:
                    print(f"Parent {i+1}: <{curr.name} class={curr.get('class')}>")
                    # Check for headers in this parent
                    headers = curr.find_all(['h2', 'h3', 'h4'], recursive=False)
                    if headers:
                        print(f"  Headers (direct): {[h.get_text(strip=True) for h in headers]}")
            
except Exception as e:
    print(e)
