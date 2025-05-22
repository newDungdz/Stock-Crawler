from src.scraping.link_scaper_vietstock import scrape_links_vietstock
from src.scraping.link_scaper_tinnhanh import scrape_links_tinnhanh
from src.scraping.article_scrape_vietstock import scrape_article_vietstock
from src.scraping.article_scrape_tinnhanh import scrape_article_tinnhanh
from src.scraping.stock_scraper import get_stock_data
import pandas as pd
from datetime import datetime
from datetime import timedelta

vietstock_links_data = scrape_links_vietstock(page_limit=1)
tinnhanh_links_data = scrape_links_tinnhanh(url="https://www.tinnhanhchungkhoan.vn/chung-khoan/", max_clicks=1)
print(vietstock_links_data)
print(tinnhanh_links_data)
vietstock_articles = scrape_article_vietstock(link_data=vietstock_links_data, limit=-1)
tinnhanh_articles = scrape_article_tinnhanh(links_data=tinnhanh_links_data, limit=20)
all_articles = vietstock_articles + tinnhanh_articles
print(all_articles)

# Get current date in YYYY-MM-DD format
current_date = datetime.now().strftime('%Y-%m-%d')
stock_codes = [
    "VCB",
    "CTG",
    "VPB",
    "BID",
    "TCB",
    "HPG",
    "MWG",
    "VNM",
    "VIC",
    "FPT"
]
yesterday = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
source = "VCI"
df = pd.DataFrame()
for symbol in stock_codes:
    df = pd.concat([df, get_stock_data(source=source, symbol = symbol, start_date=yesterday, end_date=current_date)])
print(df)