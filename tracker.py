import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Takip edilecek tüm Sahibinden linklerini bir liste haline getirdik
SEARCH_URLS = [
    "https://www.sahibinden.com/hyundai-accent-blue?a5_min=2016&price_max=380000&sorting=date_desc#!",
    "https://www.sahibinden.com/renault-symbol?a5_min=2016&price_max=320000&sorting=date_desc",
    "https://www.sahibinden.com/fiat-egea?price_max=360000&sorting=date_desc"
]

SEEN_FILE = "/tmp/seen_ids.json"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"},
]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_listings(url):
    headers = random.choice(HEADERS_LIST)
    headers["Accept-Language"] = "tr-TR,tr;q=0.9"
    headers["Referer"] = "https://www.sahibinden.com/"
    
    time.sleep(random.uniform(2, 4))
    
    session = requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"Hata ({resp.status_code}): {url} adresi çekilemedi.")
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        
        for row in soup.select("tr.searchResultsItem"):
            link_tag = row.select_one("td.searchResultsTitleValue a")
            price_tag = row.select_one("td.searchResultsPriceValue")
            
            if not link_tag:
                continue
            
            item_id = row.get("data-id", "")
            title = link_tag.get_text(strip=True)
            href = "https://www.sahibinden.com" + link_tag.get("href", "")
            price = price_tag.get_text(strip=True) if price_tag else "Fiyat yok"
            
            items.append({"id": item_id, "title": title, "url": href, "price": price})
        return items
    except Exception as e:
        print(f"Tarama hatası: {e}")
        return []

def main():
    seen = load_seen()
    ilk_calisma = len(seen) == 0
    toplam_yeni = 0
    
    for index, url_link in enumerate(SEARCH_URLS, 1):
        print(f"🔄 {index}. Link taranıyor...")
        listings = fetch_listings(url_link)
        
        for item in listings:
            if item["id"] and item["id"] not in seen:
                seen.add(item["id"])
                
                if not ilk_calisma:
                    toplam_yeni += 1
                    msg = (
                        f"🚗 <b>YENİ İLAN DÜŞTÜ!</b>\n"
                        f"📌 {item['title']}\n"
                        f"💰 {item['price']}\n"
                        f"🔗 <a href=\"{item['url']}\">İlana Git</a>"
                    )
                    send_telegram(msg)
                    time.sleep(1)
                    
    save_seen(seen)
    print(f"Kontrol bitti. Gönderilen yeni ilan sayısı: {toplam_yeni}")

if __name__ == "__main__":
    main()

def main():
    # --- TEST SATIRI (Bağlantıyı kontrol etmek için ekledik) ---
    send_telegram("🚀 GitHub ve Telegram bağlantısı BAŞARILI! Bot çalışıyor.")
    # ----------------------------------------------------------
    
    seen = load_seen()
    ilk_calisma = len(seen) == 0
    toplam_yeni = 0
