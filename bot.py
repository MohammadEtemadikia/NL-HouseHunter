import requests
import json
import os
from bs4 import BeautifulSoup

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PARARIUS_URL = "https://www.pararius.com/apartments/nederland/600-1000/25m2/since-1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEEN_FILE = "seen.json"
# =========================================


def send_message(text, image=None):
    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": CHAT_ID,
            "photo": image,
            "caption": text
        }
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text
        }
    requests.post(url, data=data)


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return []
    with open(SEEN_FILE, "r") as f:
        return json.load(f)


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)


def extract_id(link):
    return link.rstrip("/").split("/")[-1]


def main():
    seen = load_seen()
    response = requests.get(PARARIUS_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    ads = soup.select("li.search-list__item")
    new_ads = 0

    for ad in ads:
        link_tag = ad.select_one("a.listing-search-item__link")
        if not link_tag:
            continue

        link = "https://www.pararius.com" + link_tag["href"]
        ad_id = extract_id(link)

        if ad_id in seen:
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

        # size
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

        send_message(message, image)
        seen.append(ad_id)
        new_ads += 1

    save_seen(seen)

    if new_ads == 0:
        send_message("ℹ️ آگهی جدیدی پیدا نشد")


if __name__ == "__main__":
    main()
