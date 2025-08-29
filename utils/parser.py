from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def get_pinterest_images(query: str, limit: int) -> list[str]:
    image_urls = []
    max_scrolls = 50

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.pinterest.com/search/pins/?q=" + query.replace(" ", "%20"))
        time.sleep(5)

        scrolls = 0
        while len(image_urls) < limit and scrolls < max_scrolls:
            html = page.inner_html('body')
            soup = BeautifulSoup(html, 'lxml')
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and 'pinimg.com' in src and '/236x/' in src:
                    full_src = src.replace("/236x/", "/originals/")
                    if full_src not in image_urls:
                        image_urls.append(full_src)
                if len(image_urls) >= limit:
                    break

            if len(image_urls) >= limit:
                break

            page.mouse.wheel(0, 4000)
            time.sleep(2)
            scrolls += 1

        context.close()
        browser.close()

    return image_urls[:limit]