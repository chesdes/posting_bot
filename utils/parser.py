from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import requests

import logging
logger = logging.getLogger(__name__)

def is_valid_image_url(url: str) -> bool:
        try:
            response = requests.head(url, timeout=2)
            content_type = response.headers.get('content-type', '')
            return response.status_code == 200 and 'image' in content_type.lower()
        except requests.RequestException:
            logger.info(f'{url} is invalid')
            return False

def get_pinterest_images(query: str, limit: int) -> list[str]:
    start_time = time.time()
    logger.info(f'started parse {limit} images, of query "{query}"')
    image_urls = []
    max_scrolls = 50

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.pinterest.com/search/pins/?q=" + query.replace(" ", "%20"))
        time.sleep(2)

        scrolls = 0
        while len(image_urls) < limit and scrolls < max_scrolls:
            html = page.inner_html('body')
            soup = BeautifulSoup(html, 'lxml')
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and 'pinimg.com' in src and '/236x/' in src:
                    full_src = src.replace("/236x/", "/originals/")
                    if full_src not in image_urls and is_valid_image_url(full_src):
                        image_urls.append(full_src)
                if len(image_urls) >= limit:
                    break

            if len(image_urls) == 0:
                end_time = time.time()
                logger.info(f'Error. No pins were found, of query "{query}". ({end_time-start_time:.2f} seconds)')
                return None
            
            if len(image_urls) >= limit:
                end_time = time.time()
                logger.info(f'query "{query}" parse finished ({end_time-start_time:.2f} seconds)')
                break

            check_time = time.time()
            logger.info(f'query "{query}" progress: {len(image_urls)}/{limit} ({check_time-start_time:.2f}s)')

            page.mouse.wheel(0, 4000)
            time.sleep(2)
            scrolls += 1

        context.close()
        browser.close()

    return image_urls[:limit]