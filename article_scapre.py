import requests
from bs4 import BeautifulSoup
import json

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
        
        print("Title:", title)
        print("Create Date:", date)
        print("\nArticle Text:\n", article_text)
        # print("\nLinks Texts:\n", "\n".join(href_texts))

    else:
        print(f"Failed with status code {response.status_code}")

if __name__ == "__main__":
    # Load URLs from link.json
    with open('link.json', 'r', encoding='utf-8') as file:
        links = json.load(file)

    # Process each URL
    for article_data in links:
        print(f"Processing article: {article_data['title']}")
        print(f"URL: {article_data['link']}")
        get_article_info(article_data['link'])