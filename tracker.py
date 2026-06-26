import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEARCH_URLS = [
    "https://www.sahibinden.com/hyundai-accent-blue?a5_min=2016&price_max=380000&sorting=date_desc#!",
    "https://www.sahibinden.com/renault-symbol?a5_min=2016&price_max=320000&sorting=date_desc",
    "https://www.sahibinden.com/fiat-egea?price_max=360000&sorting=date_desc"
]

SEEN_FILE = "/tmp/seen_ids.json"

# Sahibinden engelini aşmak için çok daha detaylı tarayıcı taklidi (Headers)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        print(f"Telegram Yanıtı: {r.status_code}")
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_listings(url):
    time.sleep(random.uniform(3, 6)) # Engeli yememek için bekleme süresini artırdık
    session = requests.Session()
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        print(f"Site Yanıt Kodu: {resp.status_code} ({url.split('/')[-1].split('?')[0]})")
        
        if resp.status_code != 200:
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
    # Güvenlik testi: Kod başlar başlamaz Telegram bağlantısını hemen denetleyecek
    send_telegram("🚀 Bot taranıyor... Telegram bağlantısı aktif!")
    
    seen = load_seen()
    ilk_calisma = len(seen) == 0
    toplam_yeni = 0
    
    for index, url_link in enumerate(SEARCH_URLS, 1):
        listings = fetch_listings(url_link)
        print(f"Bulunan ilan sayısı: {len(listings)}")
        
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
