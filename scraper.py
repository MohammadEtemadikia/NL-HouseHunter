import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from telegram import Bot

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
DATA_FILE = Path("seen_ads.json")

seen_ads = set()

if DATA_FILE.exists():
    seen_ads = set(json.loads(DATA_FILE.read_text(encoding="utf-8")))

async def send_telegram(msg):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, disable_web_page_preview=True)


async def get_pararius_new():
    new_ads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.pararius.com/apartments/nederland/600-1000/25m2/since-1", timeout=90000)
        await page.wait_for_timeout(4000)   # صبر برای لود

        # اگر کپچا یا صفحه بلاک دیدی اینجا باید بعداً تنظیم کنی
        cards = await page.query_selector_all('section[class*="SearchResults"] article')

        for card in cards[:15]:  # فقط ۱۰–۱۵ تا اول رو چک می‌کنیم
            try:
                title_tag = await card.query_selector('h2 a')
                title = await title_tag.inner_text() if title_tag else "بدون عنوان"
                link_tag = title_tag
                link = await link_tag.get_attribute("href") if link_tag else ""
                if link and not link.startswith("http"):
                    link = "https://www.pararius.com" + link

                price_tag = await card.query_selector('[class*="price"]')
                price = await price_tag.inner_text() if price_tag else ""

                unique = link or title + price
                if unique not in seen_ads:
                    seen_ads.add(unique)
                    new_ads.append(f"🆕 Pararius\n{title.strip()}\n{price.strip()}\n{link}")
            except:
                pass

        await browser.close()
    return new_ads


async def get_funda_new():
    new_ads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://www.funda.nl/zoeken/huur?selected_area=[%22nl%22]&price=%22600-1000%22&publication_date=%221%22",
            timeout=90000
        )
        await page.wait_for_timeout(5000)

        # Funda معمولاً سخت‌تره → ممکنه نیاز به اسکرول یا تنظیم user-agent داشته باشه
        items = await page.query_selector_all('ol li[data-object-id]')

        for item in items[:12]:
            try:
                link_tag = await item.query_selector('a')
                link = await link_tag.get_attribute("href") if link_tag else ""
                if link and "funda.nl" not in link:
                    link = "https://www.funda.nl" + link

                title_tag = await item.query_selector('[data-test-id="listing-title"]')
                title = await title_tag.inner_text() if title_tag else ""

                price_tag = await item.query_selector('[data-test-id="price"]')
                price = await price_tag.inner_text() if price_tag else ""

                unique = link or title + price
                if unique not in seen_ads:
                    seen_ads.add(unique)
                    new_ads.append(f"🆕 Funda\n{title.strip()}\n{price.strip()}\n{link}")
            except:
                pass

        await browser.close()
    return new_ads


async def main():
    pararius_new = await get_pararius_new()
    funda_new = await get_funda_new()

    all_new = pararius_new + funda_new

    if all_new:
        message = f"آگهی جدید پیدا شد! ({len(all_new)} مورد) — {datetime.now():%Y-%m-%d %H:%M}\n\n"
        message += "\n\n".join(all_new)
        await send_telegram(message)

    # ذخیره آگهی‌های دیده شده
    DATA_FILE.write_text(json.dumps(list(seen_ads), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
