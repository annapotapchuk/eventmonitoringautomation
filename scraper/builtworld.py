import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

# Try to import selenium, but gracefully handle if not installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed. Builtworld scraper will not work. Install with: pip install selenium")

def scrape_builtworld_events() -> List[Dict[str, str]]:
    """
    Scrapes events from the Builtworld website using Selenium.
    This site blocks HTTP requests, so browser automation is required.
    Returns a list of dictionaries containing event details.
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium is not installed. Cannot scrape Builtworld.")
        return []
    
    url = "https://www.builtworld.com/events"
    events = []
    driver = None
    
    try:
        logger.info(f"Fetching Builtworld events from {url} using Selenium")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Try to click cookie consent button if present
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Alle akzeptieren') or contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            logger.debug("Clicked cookie consent button")
        except TimeoutException:
            logger.debug("No cookie consent button found or already dismissed")
        
        # Wait for event cards to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/event/']"))
            )
        except TimeoutException:
            logger.warning("Event cards did not load in time")
        
        # Find all event links
        event_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/event/']")
        logger.info(f"Found {len(event_links)} event links on Builtworld page")
        
        seen_urls = set()
        for link in event_links:
            try:
                href = link.get_attribute('href')
                if not href or href in seen_urls:
                    continue
                
                seen_urls.add(href)
                
                # Try to get title from the link text or nearby elements
                title = link.text.strip()
                
                # Try to find parent card element for more info
                parent = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card') or contains(@class, 'event')]")
                if parent and not title:
                    # Look for heading elements
                    try:
                        heading = parent.find_element(By.CSS_SELECTOR, "h2, h3, h4, .title")
                        title = heading.text.strip()
                    except:
                        pass
                
                # Look for date info
                date = 'See details'
                try:
                    date_el = parent.find_element(By.CSS_SELECTOR, ".date, time, [class*='date']")
                    if date_el:
                        date = date_el.text.strip()
                except:
                    pass
                
                # If no date found, try to find it in the card text
                if date == 'See details' and parent:
                    card_text = parent.text
                    # Look for German date format DD.MM.YYYY
                    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', card_text)
                    if date_match:
                        date = date_match.group(0)
                
                if not title:
                    # Extract from URL as fallback
                    slug = href.rstrip('/').split('/')[-1]
                    title = slug.replace('-', ' ').title()
                
                if title and len(title) > 3:
                    events.append({
                        'title': title,
                        'url': href,
                        'date': date,
                        'location': 'See details',
                        'source': 'Builtworld'
                    })
                    
            except Exception as e:
                logger.debug(f"Error processing event link: {e}")
                continue
        
        # Deduplicate by URL
        seen = set()
        unique_events = []
        for event in events:
            if event['url'] not in seen:
                seen.add(event['url'])
                unique_events.append(event)
        events = unique_events
        
    except WebDriverException as e:
        logger.error(f"WebDriver error scraping Builtworld: {e}")
    except Exception as e:
        logger.error(f"Error scraping Builtworld: {e}")
    finally:
        if driver:
            driver.quit()
        
    return events

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    events = scrape_builtworld_events()
    for e in events:
        print(f"  {e['title']} | {e['date']} | {e['location']}")
