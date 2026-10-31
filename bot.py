import requests
from bs4 import BeautifulSoup
import time
import re

TOKEN = "6173977681:AAGBuceUISMAeeFsx0yGGZYaNTstm3SoyjE"
CHAT_ID = "939492553"
TARGET_PRICE = 5000
CHECK_EVERY = 30  # 1 minut

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_URL = "https://www.emag.ro/telefoane-mobile/brand/apple/resigilate/filter/model-f9396,iphone-17-pro-v-13878975/c?ref=lst_leftbar_6407_resealed"

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print("Nu am putut trimite mesaj Telegram:", e)

def parse_price(text):
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".").replace("Lei", "").strip()
    match = re.search(r"(\d+\.?\d*)", text)
    return float(match.group(1)) if match else None

def is_blocked(response):
    """Verifică dacă eMAG a blocat cererea"""
    if response.status_code in (403, 429, 503):
        return True, f"Status code: {response.status_code}"
    
    text_lower = response.text.lower()
    blocked_signs = [
        "cloudflare",
        "access denied",
        "blocked",
        "captcha",
        "please wait",
        "too many requests",
        "forbidden"
    ]
    for sign in blocked_signs:
        if sign in text_lower:
            return True, f"Detectat: {sign}"
    
    # Dacă pagina e aproape goală
    if len(response.text) < 1000:
        return True, "Pagină prea scurtă (posibil blocare)"
    
    return False, None

def check_emag():
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
        
        blocked, reason = is_blocked(r)
        if blocked:
            msg = f"⚠️ Botul a fost blocat de eMAG!\nMotiv: {reason}\nStatus: {r.status_code}"
            send_telegram(msg)
            print(msg)
            return
        
        soup = BeautifulSoup(r.text, "html.parser")
        products = soup.select(".card-item, .card-v2")
        
        if not products:
            send_telegram("⚠️ Nu am găsit niciun produs pe pagină. Posibil că eMAG a schimbat structura sau e blocat.")
            return
        
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
                
    except requests.exceptions.RequestException as e:
        msg = f"⚠️ Eroare de conexiune cu eMAG:\n{str(e)}"
        send_telegram(msg)
        print(msg)
    except Exception as e:
        msg = f"⚠️ Eroare neașteptată:\n{str(e)}"
        send_telegram(msg)
        print(msg)

if __name__ == "__main__":
    send_telegram("✅ Botul a pornit! Verific pagina la fiecare minut.")
    while True:
        check_emag()
        time.sleep(CHECK_EVERY)
