from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from supabase import create_client, Client
import random
import logging

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=chrome_options)
logging.info("Connecting to the web...")
driver.get("https://vietstock.vn/chung-khoan.htm")

# Setup logging
# Clear existing handlers (important in long-running or rerun scripts)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Now set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# In-memory set of all seen links
seen_links = set()

def insert_with_retries(data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = supabase.table("stock_article_links").insert(data).execute()
            if not response.data:
                if "duplicate key value" in str(response.error).lower():
                    logging.warning(f"Duplicate key value conflict detected. Skipping insertion.")
                    return None
                raise Exception(response.error)
            return response.data
        except Exception as e:
            # Extract error message for duplicate key check
            err_msg = str(e)
            if "23505" in err_msg and "duplicate key value violates unique constraint" in err_msg:
                logging.warning(f"Duplicate key detected. Skipping this batch.")
                return None  # Don't retry on duplicate
            else:
                logging.warning(f"Insertion attempt {attempt+1} failed: {e}")
                time.sleep(2 * (attempt + 1))  # Exponential backoff
    logging.error("Max retries reached. Skipping insertion.")
    return None

def change_page(driver, page_number):
    try:
        # Wait for the pagination area to be present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.pagination')))

        # Scroll to pagination
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Find and click the page number or "next" button
        page_btn = driver.find_element(By.CSS_SELECTOR, f'a[page="{page_number}"]')
        driver.execute_script("arguments[0].click();", page_btn)

        time.sleep(2)  # Wait for page to load
    except Exception as e:
        print(f"Failed to change to page {page_number}: {e}")

def scrape_data(driver, page_number):
    articles = []
    try:
        # Wait until articles in #channel-container are loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#channel-container .single_post_text h4 a'))
        )
        posts = driver.find_elements(By.CSS_SELECTOR, '#channel-container .single_post_text h4 a')
        
        for post in posts:
            title = post.get_attribute('title')
            if(post.get_attribute('href').startswith('/')):
                link = "https://vietstock.vn" + post.get_attribute('href')
            else:
                link = post.get_attribute('href')
            articles.append({
                "page": page_number,
                "title": title, 
                "link": link
            })
    except Exception as e:
        print(f"Error while scraping: {e}")
    return articles

supabase_url = "https://ezwvfhlfykfdfrnbdcwo.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6d3ZmaGxmeWtmZGZybmJkY3dvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDE2MDQyMywiZXhwIjoyMDU5NzM2NDIzfQ.m1yRubO6kiaFUAAduIX9SEQa2MqA5ASa4lvaisSEUAU"
supabase: Client = create_client(supabase_url, supabase_key)
# Create or connect to the table

# Page loop
i = 1
failures = 0
MAX_SCRAPE_FAILURES = 5
MAX_FAILURES = 5

try:
    while True:
        # if i > 2: break
        if i > 1:
            change_page(driver, i)
            logging.info(f"Changed to page {i}")
        
        # Random delay to prevent bot detection
        delay_time = random.uniform(4.5, 7.5)
        time.sleep(delay_time)
        logging.info(f"Waiting for {delay_time}, range 4.5s - 7.5s")

        # Scrape articles
        for retry_count in range(MAX_SCRAPE_FAILURES):
            logging.info(f"Scraping data, attempt {retry_count}")
            page_data = scrape_data(driver, i)
            if not page_data:
                failures += 1
                logging.warning(f"No articles scraped on page {i}. Failure count: {failures}. Try again after {2 * (retry_count + 1)}s")
                time.sleep(2 * (retry_count + 1))  # exponential backoff
                if failures >= MAX_FAILURES:
                    logging.error("Too many consecutive failures. Exiting loop.")
                    break
                continue
            else:
                failures = 0  # reset failures on success
                break
        # Filter already-seen articles
        if not page_data:
            logging.info(f"No new articles found on page {i}. Possibly end of new content.")
            break
        logging.info(f"Crawl {len(page_data)} article on page {i}")

        # Insert and mark as seen
        result = insert_with_retries(page_data)
        if result:
            for article in page_data:
                seen_links.add(article["link"])
            logging.info(f"Inserted {len(result)} new articles into Supabase.")
        else:
            logging.warning("No articles inserted this round.")
        i += 1
except Exception as e:
    logging.exception(f"Unexpected error: {e}")
finally:
    logging.info(f"Total unique articles collected: {len(seen_links)}")
    driver.quit()
