import requests
from bs4 import BeautifulSoup
import json, os, random, time
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='[ %(levelname)s ] %(message)s')

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def get_article_info(url):
    """Get article information with rotating user agents"""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.tinnhanhchungkhoan.vn/",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
    }
    
    for attempt in range(3):
        try:
            time.sleep(random.uniform(0.1, 0.5))
            response = requests.get(url, headers=headers, timeout=20)
            
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
            elif response.status_code in [403, 429]:
                logging.warning(f"Rate limited ({response.status_code}) for {url}, retrying...")
                headers["User-Agent"] = random.choice(USER_AGENTS)
                time.sleep(2 * (attempt + 1))
            else:
                logging.error(f"Failed with status code {response.status_code} for {url}")
                break
                
        except Exception as e:
            logging.warning(f"Error fetching {url}: {e}, retrying...")
            headers["User-Agent"] = random.choice(USER_AGENTS)
            time.sleep(2 * (attempt + 1))
    
    return None

def scrape_article_tinnhanh(links_data, limit=-1):
    """Process articles from links and return article data"""
    # Load URLs


    links = links_data if limit == -1 else links_data[:limit]
    failed_urls = []
    articles = []
    
    # Process articles
    for link_data in tqdm(links, desc="Processing articles"):
        url = link_data['link']
        article = get_article_info(url)
        if article:
            articles.append(article)
        else:
            failed_urls.append(url)
    
    logging.info(f"Successfully fetched: {len(articles)} articles")
    logging.info(f"Failed: {len(failed_urls)} articles")
    
    return articles

def save_articles_to_json(articles, output_file):
    """Save articles to JSON file with deduplication"""
    # Load existing data and merge
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # Deduplicate by link
    all_articles = {article['link']: article for article in existing_data}
    for article in articles:
        all_articles[article['link']] = article
    
    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(all_articles.values()), f, indent=2, ensure_ascii=False)
    
    logging.info(f"Total articles saved: {len(all_articles)}")

if __name__ == "__main__":
    links_file = 'data\\links\\link_tinnhanh.json'
    try:
        with open(links_file, 'r', encoding='utf-8') as file:
            links_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading links file: {e}")
    article_data = scrape_article_tinnhanh(links_data=links_data, limit=2)
    print(article_data)