from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

#############################################
#                                           #
#             CODE BY CHAT GPT              #
#                                           #
#############################################

def get_pinterest_images(query: str, limit: int) -> list[str]:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
        driver.get(search_url)

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[srcset]')))

        collected_urls = set()
        scroll_attempts = 0

        while len(collected_urls) < limit and scroll_attempts < 20:
            img_elements = driver.find_elements(By.CSS_SELECTOR, 'img[srcset]')
            for img in img_elements:
                try:
                    srcset = img.get_attribute("srcset")
                    if not srcset:
                        continue

                    entries = [
                        (entry.strip().split(" ")[0], int(entry.strip().split(" ")[1][:-1]))
                        for entry in srcset.split(",") if " " in entry
                    ]
                    if entries:
                        best_url = max(entries, key=lambda x: x[1])[0]
                        collected_urls.add(best_url)

                        if len(collected_urls) >= limit:
                            break
                except Exception:
                    continue

            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(1.5)
            scroll_attempts += 1

        return list(collected_urls)[:limit]

    finally:
        driver.quit()
