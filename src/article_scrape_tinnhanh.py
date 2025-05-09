import requests
from bs4 import BeautifulSoup
import json, os
import logging
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# Configure logging
logging.basicConfig(level=logging.INFO, format='[ %(levelname)s ] %(message)s')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_article_info(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.select_one('h1.article__header.cms-title')
            title = title_tag.get_text(strip=True) if title_tag else "No title found"

            article_body = soup.select_one('div.article__body.cms-body[itemprop="articleBody"]')
            article_text = article_body.get_text(separator='\n', strip=True) if article_body else ""

            date_tag = soup.find("time", class_="time")
            date = date_tag.get_text(strip=True) if date_tag else ""

            return {
                "title": title,
                "link": url,
                "create_date": date,
                "text": article_text
            }
        else:
            logging.error(f"Failed with status code {response.status_code} for {url}")
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
    return None

if __name__ == "__main__":
    # Load URLs
    with open('data\\links\\link_tinnhanh.json', 'r', encoding='utf-8') as file:
        links_data = json.load(file)

    limit = -1
    links = links_data if limit == -1 else links_data[:limit]
    total = len(links)
    filename = "data\\article_data\\article_data_tinnhanh.json"
    num_process = 1
    # Run multiprocessing
    with Pool(processes=num_process) as pool:
        results = list(tqdm(pool.imap_unordered(get_article_info, [link['link'] for link in links]), total=total, desc="Processing articles"))

    # Filter out None results
    new_articles = [r for r in results if r]

    # Load existing data
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Merge and deduplicate by link
    all_articles = {article['link']: article for article in existing_data}
    for article in new_articles:
        all_articles[article['link']] = article

    # Save once at the end
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(all_articles.values()), f, indent=2, ensure_ascii=False)

    logging.info(f"Saved {len(new_articles)} new articles (total {len(all_articles)}).")
