import requests
from bs4 import BeautifulSoup
import json, os
import logging

def save_articles_to_json(new_article, filename='link.json'):
    # Check if file exists and load existing data
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Append only new links
    links_seen = set(article['link'] for article in existing_data)
    if(new_article['link'] in links_seen): return 

    # Append new items
    existing_data.append(new_article)

    # Save back to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

def scrape_article_vietstock(link_data, limit=-1):
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='[ %(levelname)s ] %(message)s')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    session = requests.Session()
    def get_article_info(url):
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.select_one('h1.article-title, h3.title')
            title = title_tag.text.strip() if title_tag else "No title found"
            # Extract only article body content        
            clean_text = []

            # Get all pBody and pSubtitle paragraphs
            paragraphs = soup.find_all('p', class_=["pBody", "pSubTitle"])
            

            for p in paragraphs:
                # Skip ">>" links
                if p.text.strip().startswith(">>"):
                    continue

                # Check if it's a subtitle
                if 'pSubTitle' in p.get('class', []):
                    subtitle = p.get_text(separator=" ", strip=True)
                    clean_text.append(f"**{subtitle}**")  # or use ## {subtitle}
                else:
                    # Check for image
                    img = p.find('img')
                    if img and img.get('src'):
                        img_url = img['src']
                        clean_text.append(f"[Image: {img_url}]")
                    else:
                        text = p.get_text(separator=" ", strip=True)
                        clean_text.append(text)

            article_text = "\n\n".join(clean_text)

            date_tag = soup.find("span", class_ = "date")
            date = date_tag.get_text(strip= True)
            logging.info(f"Title: {title}")
            logging.info(f"Link: {url}")
            logging.info(f"Date: {date}")
            logging.info(f"Text: {article_text[:40]}...{article_text[-40:]}")  # Log first and last 40 characters of the text
            return {
                "title": title,
                "link": url,
                "date": date,
                "text": article_text
            }

        else:
            logging.error(f"Failed with status code {response.status_code}")
    all_data = []
    processed_count = 0
    for data in link_data:
        if limit != -1 and processed_count >= limit:
            logging.info("Reached the processing limit.")
            break
        logging.info(f"Processing article: {data['link']}")
        try:
            all_data.append(get_article_info(data['link']))
        except Exception as e:
            logging.error(f"Error processing {data['link']}: {e}")
            continue    
        processed_count += 1
    return all_data

if __name__ == "__main__":
    # Load URLs from link.json
    with open('data/links/link_vietstock.json', 'r', encoding='utf-8') as file:
        links = json.load(file)
    all_data = scrape_arlticle_vietstock(links, limit=2)
    print(all_data)
