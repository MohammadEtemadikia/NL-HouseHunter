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
        link_tag = ad.select_one("a.listing-search-item__link")
        if not link_tag:
            continue

        link = "https://www.pararius.com" + link_tag["href"]
        if link in seen:
            continue

        # title
        title_tag = ad.select_one("h2.listing-search-item__title")
        title = title_tag.get_text(strip=True) if title_tag else "Apartment for rent"

        # city
        city_tag = ad.select_one("div.listing-search-item__sub-title")
        city = city_tag.get_text(strip=True) if city_tag else "Unknown city"

        # price
        price_tag = ad.select_one("div.listing-search-item__price")
        price = price_tag.get_text(strip=True) if price_tag else "Price unknown"

        # size (m²)
        size = "Unknown size"
        for li in ad.select("li.illustrated-features__item"):
            if "m²" in li.get_text():
                size = li.get_text(strip=True)
                break

        # image
        img_tag = ad.select_one("img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

        message = (
            f"🏠 {title}\n\n"
            f"📍 {city}\n"
            f"📐 {size}\n"
            f"💰 {price}\n\n"
            f"🔗 {link}"
        )

        send(message, image)
        seen.append(link)
        new_count += 1

    save_seen(seen)

    if new_count == 0:
        send("ℹ️ آگهی جدیدی پیدا نشد")

if __name__ == "__main__":
    main()
