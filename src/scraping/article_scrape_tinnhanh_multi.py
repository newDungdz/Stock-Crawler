import requests
from bs4 import BeautifulSoup
import json, os, random
import logging
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='[ %(levelname)s ] %(message)s')

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
]

def get_article_info(args):
    """Get article information with rotating user agents"""
    url, failed_urls = args
    
    # Select a user agent based on process ID for deterministic assignment per worker
    user_agent = USER_AGENTS[os.getpid() % len(USER_AGENTS)]
    
    headers = {
        "User-Agent": user_agent,
        "Referer": "https://www.tinnhanhchungkhoan.vn/",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8,pt-BR;q=0.7,pt;q=0.6",
    }
    
    # Add a small random delay to avoid synchronized requests
    time.sleep(random.uniform(0.1, 0.5))
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                title_tag = soup.select_one('h1.article__header.cms-title')
                title = title_tag.get_text(strip=True) if title_tag else "No title found"
                
                article_body = soup.select_one('div.article__body.cms-body[itemprop="articleBody"]')
                article_text = article_body.get_text(separator='\n', strip=True) if article_body else ""
                
                date_tag = soup.find("time", class_="time")
                date = date_tag.get_text(strip=True) if date_tag else ""
                # print(f"Title: {title}")
                return {
                    "title": title,
                    "link": url,
                    "date": date,
                    "text": article_text
                }
            elif response.status_code in [403, 429]:
                # Rate limited or blocked - retry with a different user agent
                logging.warning(f"Rate limited ({response.status_code}) for {url}, retrying...")
                retry_count += 1
                # Choose a different user agent
                user_agent = random.choice(USER_AGENTS)
                headers["User-Agent"] = user_agent
                time.sleep(2 * retry_count)  # Exponential backoff
            else:
                logging.error(f"Failed with status code {response.status_code} for {url}")
                failed_urls.append(url)
                break
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request error fetching {url}: {e}, retrying...")
            retry_count += 1
            # Choose a different user agent
            user_agent = random.choice(USER_AGENTS)
            headers["User-Agent"] = user_agent
            time.sleep(2 * retry_count)  # Exponential backoff
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            failed_urls.append(url)
            break
    
    if retry_count >= max_retries:
        logging.error(f"Max retries reached for {url}, waiting 10 seconds and retrying with new headers...")
        time.sleep(10)
        retry_count = 0
        user_agent = random.choice(USER_AGENTS)
        headers["User-Agent"] = user_agent
        return get_article_info((url, failed_urls))
    
    return None

if __name__ == "__main__":
    # Load URLs
    try:
        with open('data\\links\\link_tinnhanh.json', 'r', encoding='utf-8') as file:
            links_data = json.load(file)
        # with open('data\\failed_links_1.txt', 'r', encoding='utf-8') as file:
        #     links_data = file.readlines()
        # links_data = [{"link": link.strip()} for link in links_data]
    except FileNotFoundError:
        logging.error("Links file not found")
        exit(1)
    except json.JSONDecodeError:
        logging.error("Invalid JSON in links file")
        exit(1)
    
    limit = -1
    links = links_data if limit == -1 else links_data[:limit]
    total = len(links)
    filename = "data\\article_data\\tinnhanh.json"
    failed_links_file = "data\\failed_links.txt"
    num_process = 30
    
    # Track statistics
    start_time = time.time()
    
    # Create a list to store failed links
    # Using a list for thread safety in multiprocessing
    manager = Pool(processes=num_process)._ctx.Manager()
    failed_urls = manager.list()
    
    # Prepare arguments for workers - each worker gets a URL and access to the failed_urls list
    args_list = [(link['link'], failed_urls) for link in links]
    # Run multiprocessing
    with Pool(processes=num_process) as pool:
        results = list(tqdm(
            pool.imap_unordered(get_article_info, args_list),
            total=total,
            desc="Processing articles"
        ))
    
    # Filter out None results
    new_articles = [r for r in results]
    failed_count = len(failed_urls)
    
    # Save failed links to a text file
    if failed_urls:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(failed_links_file), exist_ok=True)
        
        with open(failed_links_file, 'w', encoding='utf-8') as f:
            for url in failed_urls:
                f.write(f"{url}\n")
        logging.info(f"Saved {len(failed_urls)} failed URLs to {failed_links_file}")
    
    print(f"Total articles fetched: {len(new_articles)}")
    # Reset the JSON file by clearing its content
    if os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("[]")
        logging.info(f"Reset the JSON file: {filename}")

    # Load existing data
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    print(f"Existing articles loaded: {len(existing_data)}")
    # Merge and deduplicate by link
    all_articles = {article['link']: article for article in existing_data}
    for article in new_articles:
        all_articles[article['link']] = article
    print(f"Total articles after merging: {len(all_articles)}")
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save once at the end
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(all_articles.values()), f, indent=2, ensure_ascii=False)
    
    # Log statistics
    elapsed_time = time.time() - start_time
    logging.info(f"Completed in {elapsed_time:.2f} seconds")
    logging.info(f"Successfully fetched: {len(new_articles)} articles")
    logging.info(f"Failed: {failed_count} articles")
    logging.info(f"Saved {len(new_articles)} new articles (total {len(all_articles)}).")