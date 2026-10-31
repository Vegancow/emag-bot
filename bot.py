import requests
from bs4 import BeautifulSoup
import time
import re

TOKEN = "6173977681:AAGBuceUISMAeeFsx0yGGZYaNTstm3SoyjE"
CHAT_ID = "939492553"
TARGET_PRICE = 5000
CHECK_EVERY = 900  # 15 minute

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_URL = "https://www.emag.ro/telefoane-mobile/brand/apple/resigilate/filter/model-f9396,iphone-17-pro-v-13878975/c?ref=lst_leftbar_6407_resealed"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def parse_price(text):
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".").replace("Lei", "").strip()
    match = re.search(r"(\d+\.?\d*)", text)
    return float(match.group(1)) if match else None

def check_emag():
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        products = soup.select(".card-item, .card-v2")
        
        for p in products:
            title_el = p.select_one(".card-v2-title, .card-title")
            price_el = p.select_one(".product-new-price")
            link_el = p.select_one("a")
            
            if not title_el or not price_el:
                continue
                
            title = title_el.get_text(strip=True)
            price = parse_price(price_el.get_text())
            link = link_el["href"] if link_el and link_el.get("href") else SEARCH_URL
            if link.startswith("/"):
                link = "https://www.emag.ro" + link
            
            if price and price < TARGET_PRICE:
                msg = f"""💳 preț {price:.2f} lei
📱 {title}
📈 Preț minim: {TARGET_PRICE} lei
🔗 {link}"""
                send_telegram(msg)
                print(f"Alertă: {title} - {price}")
    except Exception as e:
        print("Eroare:", e)

if __name__ == "__main__":
    send_telegram("✅ Botul a pornit! Monitorizez pagina de iPhone 17 Pro resigilate și te anunț când apare ceva sub 5000 lei.")
    while True:
        check_emag()
        time.sleep(CHECK_EVERY)
