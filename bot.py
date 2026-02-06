import requests
import json
import os
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.pararius.com/apartments/nederland/600-1000/25m2/since-1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEEN_FILE = "seen.json"

def send(text, image=None):
    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {"chat_id": CHAT_ID, "photo": image, "caption": text}
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return []
    with open(SEEN_FILE) as f:
        return json.load(f)

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def main():
    seen = load_seen()

    r = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    ads = soup.select("li.search-list__item")
    new_count = 0

    for ad in ads:
        a = ad.select_one("a.listing-search-item__link")
        img = ad.select_one("img")

        if not a:
            continue

        link = "https://www.pararius.com" + a["href"]
        if link in seen:
            continue

        image = img["src"] if img else None
        send(f"🏠 آگهی جدید Pararius\n{link}", image)
        seen.append(link)
        new_count += 1

    save_seen(seen)

    if new_count == 0:
        send("ℹ️ آگهی جدیدی پیدا نشد")

if __name__ == "__main__":
    main()
